use std::collections::BTreeMap;

use super::models::{ExecutionRow, GroupRow, ResultTotals};

pub fn compute_result_totals(executions: &[ExecutionRow]) -> ResultTotals {
    let mut by_result = BTreeMap::<String, usize>::new();
    for execution in executions {
        *by_result.entry(execution.result.clone()).or_default() += 1;
    }
    ResultTotals {
        total: executions.len(),
        by_result,
    }
}

pub fn build_group_rows(executions: &[ExecutionRow]) -> Vec<GroupRow> {
    let mut grouped = BTreeMap::<String, Vec<&ExecutionRow>>::new();
    for execution in executions {
        grouped
            .entry(execution.base_name.clone())
            .or_default()
            .push(execution);
    }

    let mut rows = Vec::<GroupRow>::new();
    for (base_name, items) in grouped {
        let totals = compute_group_totals(&items);
        let latest_result = latest_result(&items);
        let group_result = compute_group_result(&totals);
        let failure_count =
            totals.get("FAIL").copied().unwrap_or(0) + totals.get("ERROR").copied().unwrap_or(0);
        let total = items.len();
        let error_rate = if total > 0 {
            failure_count as f64 / total as f64
        } else {
            0.0
        };

        rows.push(GroupRow {
            base_name,
            total,
            by_result: totals,
            latest_result,
            group_result,
            failure_count,
            error_rate,
            latency_averages: compute_latency_averages(&items),
        });
    }

    rows
}

pub fn collect_problem_tests(rows: &[GroupRow]) -> Vec<String> {
    rows.iter()
        .filter(|row| matches!(row.group_result.as_str(), "FAIL" | "ERROR"))
        .map(|row| row.base_name.clone())
        .collect()
}

pub fn compute_group_result(by_result: &BTreeMap<String, usize>) -> String {
    if by_result.is_empty() {
        return "UNKNOWN".to_string();
    }

    if by_result.get("ERROR").copied().unwrap_or(0) > 0 {
        return "ERROR".to_string();
    }
    if by_result.get("FAIL").copied().unwrap_or(0) > 0 {
        return "FAIL".to_string();
    }

    let total: usize = by_result.values().sum();
    let pass_count = by_result.get("PASS").copied().unwrap_or(0);
    if total > 0 && pass_count == total {
        return "PASS".to_string();
    }

    for status in ["SKIP", "UNKNOWN"] {
        if by_result.get(status).copied().unwrap_or(0) > 0 {
            return status.to_string();
        }
    }

    by_result
        .keys()
        .next()
        .cloned()
        .unwrap_or_else(|| "UNKNOWN".to_string())
}

fn compute_group_totals(items: &[&ExecutionRow]) -> BTreeMap<String, usize> {
    let mut totals = BTreeMap::<String, usize>::new();
    for item in items {
        *totals.entry(item.result.clone()).or_default() += 1;
    }
    totals
}

fn latest_result(items: &[&ExecutionRow]) -> String {
    items
        .iter()
        .max_by(|left, right| {
            left.begin_time
                .unwrap_or(-1)
                .cmp(&right.begin_time.unwrap_or(-1))
                .then(
                    left.iteration
                        .unwrap_or(0)
                        .cmp(&right.iteration.unwrap_or(0)),
                )
        })
        .map(|item| item.result.clone())
        .unwrap_or_else(|| "UNKNOWN".to_string())
}

fn compute_latency_averages(items: &[&ExecutionRow]) -> BTreeMap<String, f64> {
    let mut acc = BTreeMap::<String, Vec<f64>>::new();
    for item in items {
        for (key, value) in &item.sponge_properties {
            if !key.to_ascii_lowercase().contains("latency") {
                continue;
            }
            let Some(num) = value_to_f64(value) else {
                continue;
            };
            acc.entry(key.clone()).or_default().push(num);
        }
    }

    acc.into_iter()
        .filter_map(|(key, values)| {
            if values.is_empty() {
                return None;
            }
            let sum: f64 = values.iter().sum();
            Some((key, sum / values.len() as f64))
        })
        .collect()
}

fn value_to_f64(value: &serde_json::Value) -> Option<f64> {
    if let Some(number) = value.as_f64() {
        return Some(number);
    }
    value.as_str()?.parse::<f64>().ok()
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeMap;

    use serde_json::json;

    use super::{build_group_rows, collect_problem_tests, compute_group_result};
    use crate::domain::models::ExecutionRow;

    fn execution(
        raw_name: &str,
        base_name: &str,
        result: &str,
        begin_time: i64,
        latency: Option<f64>,
    ) -> ExecutionRow {
        let mut sponge_properties = BTreeMap::new();
        if let Some(latency) = latency {
            sponge_properties.insert("State change latency".to_string(), json!(latency));
        }
        ExecutionRow {
            execution_id: format!("{raw_name}-{begin_time}"),
            raw_name: raw_name.to_string(),
            base_name: base_name.to_string(),
            iteration: Some(0),
            result: result.to_string(),
            details: Vec::new(),
            sponge_properties,
            begin_time: Some(begin_time),
            end_time: Some(begin_time + 100),
        }
    }

    #[test]
    fn compute_group_result_prioritizes_error_then_fail() {
        let mut by_result = BTreeMap::new();
        by_result.insert("PASS".to_string(), 1);
        by_result.insert("FAIL".to_string(), 1);
        by_result.insert("ERROR".to_string(), 1);
        assert_eq!(compute_group_result(&by_result), "ERROR");
    }

    #[test]
    fn build_group_rows_calculates_failure_rate_and_latency() {
        let executions = vec![
            execution("test_b_0", "test_b", "FAIL", 100, Some(30.0)),
            execution("test_b_1", "test_b", "FAIL", 200, Some(50.0)),
        ];

        let rows = build_group_rows(&executions);
        assert_eq!(rows.len(), 1);
        let row = &rows[0];
        assert_eq!(row.group_result, "FAIL");
        assert_eq!(row.failure_count, 2);
        assert!((row.error_rate - 1.0).abs() < f64::EPSILON);
        assert_eq!(
            row.latency_averages.get("State change latency").copied(),
            Some(40.0)
        );
    }

    #[test]
    fn collect_problem_tests_includes_fail_and_error_only() {
        let executions = vec![
            execution("test_a_0", "test_a", "PASS", 100, None),
            execution("test_b_0", "test_b", "FAIL", 200, None),
            execution("test_c_0", "test_c", "ERROR", 300, None),
        ];
        let rows = build_group_rows(&executions);
        let problems = collect_problem_tests(&rows);
        assert!(problems.iter().any(|name| name.contains("test_b")));
        assert!(problems.iter().any(|name| name.contains("test_c")));
    }
}
