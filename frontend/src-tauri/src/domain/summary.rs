use std::collections::{BTreeMap, HashMap, HashSet};

use serde::Deserialize;
use serde_yaml::{Mapping, Value};

use crate::error::{AppError, AppResult};

use super::models::{ExecutionRow, ParsedSummary};

pub fn parse_summary_documents(content: &str) -> AppResult<ParsedSummary> {
    let mut requested_tests: Vec<String> = Vec::new();
    let mut pending_userdata: HashMap<String, Mapping> = HashMap::new();
    let mut controller_info: Option<serde_json::Value> = None;
    let mut executions: Vec<ExecutionRow> = Vec::new();
    let mut record_index: usize = 0;

    for document in serde_yaml::Deserializer::from_str(content) {
        let value = Value::deserialize(document)
            .map_err(|error| AppError::parse(format!("Failed to parse YAML document: {error}")))?;
        let Some(map) = value.as_mapping() else {
            continue;
        };
        let Some(doc_type) = get_string(map, "Type") else {
            continue;
        };

        match doc_type.as_str() {
            "TestNameList" => {
                requested_tests = get_requested_tests(map);
            }
            "UserData" => {
                if let Some(test_name) = get_string(map, "Test Name") {
                    pending_userdata.insert(test_name, map.clone());
                }
            }
            "Record" => {
                if let Some(execution) = build_execution(map, &mut pending_userdata, record_index) {
                    executions.push(execution);
                }
                record_index += 1;
            }
            "ControllerInfo" => {
                if let Some(parsed_controller_info) = extract_summary_controller_info(map) {
                    controller_info = Some(parsed_controller_info);
                }
            }
            _ => {}
        }
    }

    sort_executions(&mut executions);

    Ok(ParsedSummary {
        requested_tests,
        controller_info,
        executions,
    })
}

pub fn merge_summaries(summaries: &[ParsedSummary]) -> ParsedSummary {
    let mut requested_tests: Vec<String> = Vec::new();
    let mut seen_tests: HashSet<String> = HashSet::new();
    let mut executions: Vec<ExecutionRow> = Vec::new();

    for (summary_index, summary) in summaries.iter().enumerate() {
        for test_name in &summary.requested_tests {
            if seen_tests.insert(test_name.clone()) {
                requested_tests.push(test_name.clone());
            }
        }
        executions.extend(summary.executions.iter().cloned().map(|mut execution| {
            execution.execution_id = format!("s{summary_index}::{}", execution.execution_id);
            execution
        }));
    }

    sort_executions(&mut executions);
    ParsedSummary {
        requested_tests,
        controller_info: None,
        executions,
    }
}

fn build_execution(
    record_doc: &Mapping,
    pending_userdata: &mut HashMap<String, Mapping>,
    record_index: usize,
) -> Option<ExecutionRow> {
    let raw_name = get_string(record_doc, "Test Name")?;
    let user_doc = pending_userdata.remove(&raw_name);
    let (base_name, iteration) = split_iteration(&raw_name);
    let execution_id = build_execution_id(record_doc, &raw_name, record_index);

    Some(ExecutionRow {
        execution_id,
        raw_name,
        base_name,
        iteration,
        result: normalize_result(get_string(record_doc, "Result").as_deref()),
        details: collect_details(record_doc),
        sponge_properties: extract_sponge_properties(user_doc.as_ref()),
        begin_time: get_i64(record_doc, "Begin Time"),
        end_time: get_i64(record_doc, "End Time"),
    })
}

fn build_execution_id(record_doc: &Mapping, raw_name: &str, record_index: usize) -> String {
    if let Some(signature) = get_string(record_doc, "Signature") {
        let normalized = signature.trim();
        if !normalized.is_empty() {
            return normalized.to_string();
        }
    }

    let begin_time = get_i64(record_doc, "Begin Time").unwrap_or(-1);
    let end_time = get_i64(record_doc, "End Time").unwrap_or(-1);
    format!("{raw_name}::{begin_time}::{end_time}::{record_index}")
}

fn get_requested_tests(document: &Mapping) -> Vec<String> {
    match document.get(Value::String("Requested Tests".to_string())) {
        Some(Value::Sequence(items)) => items
            .iter()
            .filter_map(|value| value.as_str().map(ToOwned::to_owned))
            .collect(),
        _ => Vec::new(),
    }
}

fn split_iteration(raw_name: &str) -> (String, Option<u32>) {
    let Some((head, tail)) = raw_name.rsplit_once('_') else {
        return (raw_name.to_string(), None);
    };
    if let Ok(iteration) = tail.parse::<u32>() {
        return (head.to_string(), Some(iteration));
    }
    (raw_name.to_string(), None)
}

fn normalize_result(result: Option<&str>) -> String {
    result
        .map(|value| value.trim().to_ascii_uppercase())
        .filter(|value| !value.is_empty())
        .unwrap_or_else(|| "UNKNOWN".to_string())
}

fn collect_details(record_doc: &Mapping) -> Vec<String> {
    let mut candidates: Vec<String> = Vec::new();

    if let Some(details) = get_string(record_doc, "Details") {
        if !details.trim().is_empty() {
            candidates.push(details.trim().to_string());
        }
    }

    if let Some(extras) = get_string(record_doc, "Extras") {
        if !extras.trim().is_empty() {
            candidates.push(extras.trim().to_string());
        }
    }

    if let Some(Value::Mapping(extra_errors)) =
        record_doc.get(Value::String("Extra Errors".to_string()))
    {
        for payload in extra_errors.values() {
            if let Value::Mapping(payload_map) = payload {
                if let Some(detail) = get_string(payload_map, "Details") {
                    if !detail.trim().is_empty() {
                        candidates.push(detail.trim().to_string());
                    }
                }
            }
        }
    }

    dedupe_preserve_order(candidates)
}

fn extract_sponge_properties(user_doc: Option<&Mapping>) -> BTreeMap<String, serde_json::Value> {
    let mut result = BTreeMap::new();
    let Some(user_doc) = user_doc else {
        return result;
    };
    let Some(Value::Mapping(sponge_map)) =
        user_doc.get(Value::String("sponge_properties".to_string()))
    else {
        return result;
    };

    for (key, value) in sponge_map {
        let Some(key) = key.as_str() else {
            continue;
        };
        let converted = yaml_to_json(value);
        result.insert(key.to_string(), converted);
    }

    result
}

fn extract_summary_controller_info(doc: &Mapping) -> Option<serde_json::Value> {
    let value = doc.get(Value::String("Controller Info".to_string()))?;
    let converted = yaml_to_json(value);
    if converted.is_null() {
        return None;
    }
    Some(converted)
}

fn yaml_to_json(value: &Value) -> serde_json::Value {
    match value {
        Value::Null => serde_json::Value::Null,
        Value::Bool(value) => serde_json::Value::Bool(*value),
        Value::Number(number) => {
            if let Some(int_value) = number.as_i64() {
                serde_json::Value::Number(int_value.into())
            } else if let Some(float_value) = number.as_f64() {
                serde_json::json!(float_value)
            } else {
                serde_json::Value::Null
            }
        }
        Value::String(value) => serde_json::Value::String(value.clone()),
        Value::Sequence(items) => {
            serde_json::Value::Array(items.iter().map(yaml_to_json).collect())
        }
        Value::Mapping(map) => {
            let mut object = serde_json::Map::new();
            for (key, value) in map {
                if let Some(key) = key.as_str() {
                    object.insert(key.to_string(), yaml_to_json(value));
                }
            }
            serde_json::Value::Object(object)
        }
        _ => serde_json::Value::Null,
    }
}

fn dedupe_preserve_order(values: Vec<String>) -> Vec<String> {
    let mut seen = HashSet::<String>::new();
    let mut deduped = Vec::<String>::new();
    for value in values {
        if seen.insert(value.clone()) {
            deduped.push(value);
        }
    }
    deduped
}

fn get_string(map: &Mapping, key: &str) -> Option<String> {
    map.get(Value::String(key.to_string()))
        .and_then(Value::as_str)
        .map(ToOwned::to_owned)
}

fn get_i64(map: &Mapping, key: &str) -> Option<i64> {
    let value = map.get(Value::String(key.to_string()))?;
    if let Some(number) = value.as_i64() {
        return Some(number);
    }
    if let Some(number) = value.as_u64() {
        return i64::try_from(number).ok();
    }
    if let Some(text) = value.as_str() {
        return text.parse::<i64>().ok();
    }
    None
}

fn sort_executions(executions: &mut [ExecutionRow]) {
    executions.sort_by(|left, right| {
        let left_iteration = left.iteration.map_or(-1_i64, i64::from);
        let right_iteration = right.iteration.map_or(-1_i64, i64::from);
        left.base_name
            .cmp(&right.base_name)
            .then(left_iteration.cmp(&right_iteration))
            .then(
                left.begin_time
                    .unwrap_or(0)
                    .cmp(&right.begin_time.unwrap_or(0)),
            )
            .then(left.execution_id.cmp(&right.execution_id))
    });
}

#[cfg(test)]
mod tests {
    use super::{merge_summaries, parse_summary_documents};

    const SUMMARY_CONTENT: &str = r#"---
Type: TestNameList
Requested Tests:
  - test_a
  - test_b
...
---
Type: UserData
Test Name: test_a_0
sponge_properties:
  metric_a: 42
...
---
Type: Record
Test Name: test_a_0
Result: PASS
Begin Time: 1700000000100
End Time: 1700000000200
Signature: test_a_0-1700000000100
Details: success detail
Extras: null
Extra Errors: {}
...
---
Type: UserData
Test Name: test_b_0
sponge_properties:
  metric_b: 3.14
  Controller Info:
    serial: ctrl-b
    mode: wifi
...
---
Type: Record
Test Name: test_b_0
Result: FAIL
Begin Time: 1700000000400
End Time: 1700000000500
Signature: test_b_0-1700000000400
Details: failure detail
Extras: null
Extra Errors:
  err@1700000000400:
    Details: deeper issue
...
---
Type: ControllerInfo
Controller Info:
  serial: ctrl-summary
  mode: ethernet
...
"#;

    #[test]
    fn parse_summary_returns_requested_tests_and_executions() {
        let summary = parse_summary_documents(SUMMARY_CONTENT).unwrap();

        assert_eq!(summary.requested_tests, vec!["test_a", "test_b"]);
        assert_eq!(summary.executions.len(), 2);

        let first = &summary.executions[0];
        assert_eq!(first.execution_id, "test_a_0-1700000000100".to_string());
        assert_eq!(first.base_name, "test_a");
        assert_eq!(first.iteration, Some(0));
        assert_eq!(first.result, "PASS");
        assert_eq!(first.details, vec!["success detail"]);
        assert_eq!(
            first.sponge_properties.get("metric_a").unwrap().as_i64(),
            Some(42)
        );
        assert_eq!(
            summary
                .controller_info
                .as_ref()
                .and_then(|value| value.get("serial"))
                .and_then(|value| value.as_str()),
            Some("ctrl-summary")
        );

        let second = &summary.executions[1];
        assert_eq!(second.execution_id, "test_b_0-1700000000400".to_string());
        assert_eq!(second.base_name, "test_b");
        assert_eq!(second.result, "FAIL");
        assert_eq!(second.details, vec!["failure detail", "deeper issue"]);
    }

    #[test]
    fn parse_summary_sets_controller_info_none_when_missing() {
        let content = r#"---
Type: TestNameList
Requested Tests:
  - test_c
...
---
Type: UserData
Test Name: test_c_0
sponge_properties:
  metric_c: 1
...
---
Type: Record
Test Name: test_c_0
Result: PASS
Begin Time: 1700000000100
End Time: 1700000000200
Details: ok
Extra Errors: {}
...
"#;

        let summary = parse_summary_documents(content).unwrap();
        assert_eq!(summary.executions.len(), 1);
        assert_eq!(summary.controller_info, None);
    }

    #[test]
    fn parse_summary_uses_last_controller_info_document() {
        let content = r#"---
Type: ControllerInfo
Controller Info:
  serial: ctrl-first
...
---
Type: ControllerInfo
Controller Info:
  serial: ctrl-last
...
"#;

        let summary = parse_summary_documents(content).unwrap();
        assert_eq!(
            summary
                .controller_info
                .as_ref()
                .and_then(|value| value.get("serial"))
                .and_then(|value| value.as_str()),
            Some("ctrl-last")
        );
    }

    #[test]
    fn merge_summary_dedupes_requested_tests() {
        let first = parse_summary_documents(SUMMARY_CONTENT).unwrap();
        let second = parse_summary_documents(SUMMARY_CONTENT).unwrap();
        let merged = merge_summaries(&[first, second]);

        assert_eq!(merged.requested_tests, vec!["test_a", "test_b"]);
        assert_eq!(merged.executions.len(), 4);
        let execution_ids = merged
            .executions
            .iter()
            .map(|execution| execution.execution_id.as_str())
            .collect::<Vec<_>>();
        assert!(execution_ids.contains(&"s0::test_a_0-1700000000100"));
        assert!(execution_ids.contains(&"s1::test_a_0-1700000000100"));
        assert!(execution_ids.contains(&"s0::test_b_0-1700000000400"));
        assert!(execution_ids.contains(&"s1::test_b_0-1700000000400"));
    }

    #[test]
    fn parse_summary_falls_back_to_deterministic_execution_id_without_signature() {
        let content = r#"---
Type: TestNameList
Requested Tests:
  - test_x
...
---
Type: Record
Test Name: test_x_0
Result: ERROR
Begin Time: 1700000009999
End Time: 1700000011111
Details: fallback id
Extra Errors: {}
...
"#;

        let summary = parse_summary_documents(content).unwrap();
        assert_eq!(summary.executions.len(), 1);
        assert_eq!(
            summary.executions[0].execution_id,
            "test_x_0::1700000009999::1700000011111::0".to_string()
        );
    }

    #[test]
    fn merge_summary_disambiguates_execution_ids_across_summaries() {
        let content = r#"---
Type: TestNameList
Requested Tests:
  - test_x
...
---
Type: Record
Test Name: test_x_0
Result: PASS
Begin Time: 10
End Time: 20
Details: same execution
Extra Errors: {}
...
"#;

        let first = parse_summary_documents(content).unwrap();
        let second = parse_summary_documents(content).unwrap();
        let merged = merge_summaries(&[first, second]);

        assert_eq!(merged.executions.len(), 2);
        assert_eq!(
            merged.executions[0].execution_id,
            "s0::test_x_0::10::20::0".to_string()
        );
        assert_eq!(
            merged.executions[1].execution_id,
            "s1::test_x_0::10::20::0".to_string()
        );
    }
}
