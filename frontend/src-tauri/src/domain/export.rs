use std::collections::HashMap;
use std::fs;
use std::path::Path;

use regex::Regex;

use crate::error::{AppError, AppResult};

use super::models::ExecutionRow;

const RESULT_INDEX: u32 = 0;
const DETAILS_INDEX: u32 = 13;

const SPONGE_PROPERTIES_IN_SHEET: [(&str, u32); 12] = [
    ("SASS trigger switch", 1),
    ("ACL connection initiated", 2),
    ("profile connecting", 3),
    ("ACL connection successful", 4),
    ("profile connected", 5),
    ("Active switch trigger", 6),
    ("Receive active switch", 7),
    ("HFP audio streaming", 8),
    ("A2DP start streaming", 9),
    ("State change latency", 10),
    ("Audio change latency", 11),
    ("debug_msg", 13),
];

const STATE_TEST_CASE: [&str; 6] = [
    "test_1_01_most_recently_inuse_state",
    "test_1_02_no_streaming_state",
    "test_1_03_game_state",
    "test_1_04_media_state",
    "test_1_05_phonecallout_state",
    "test_1_06_voip_state",
];

const KEY_STATE_TEST_CASE: [&str; 7] = [
    "test_2_1_dut_a_inuse",
    "test_2_1_dut_a_mostrecentlyinuse",
    "test_2_2_dut_c_inuse",
    "test_2_3_dut_e_inuse",
    "test_2_4_from_dut_a_to_dut_n",
    "test_2_5",
    "test_2_6",
];

const KEY_STATE_MULTIPOINT_TEST_CASE: [&str; 2] = ["test_2_7_keystate", "test_2_8_keystate"];

const E2E_TEST_CASE: [&str; 29] = [
    "test_3_01_phonecallout_not_switch_phonecallout",
    "test_3_02_phonecallout_not_switch_voip",
    "test_3_03_phonecallout_not_switch_media",
    "test_3_04_phonecallout_not_switch_game",
    "test_3_05_media_switch_phonecallout",
    "test_3_06_media_switch_voip",
    "test_3_07_media_switch_media",
    "test_3_08_media_not_switch_game",
    "test_3_09_game_switch_phonecallout",
    "test_3_10_game_switch_voip",
    "test_3_11_game_switch_media",
    "test_3_12_game_switch_game",
    "test_3_13_no_streaming_switch_phonecallout",
    "test_3_14_no_streaming_switch_voip",
    "test_3_15_no_streaming_switch_media",
    "test_3_16_no_streaming_switch_game",
    "test_3_17_revert_button",
    "test_3_18_revert_after_auto_connect",
    "test_3_19_auto_connect_via_phonecallout",
    "test_3_20_auto_connect_via_media",
    "test_3_21_non_sass_no_streaming_not_switch_media",
    "test_3_22_non_sass_no_streaming_not_switch_phonecallout",
    "test_3_23_auto_connect_via_phonecallout_if_lastest_is_non_sass",
    "test_3_24_auto_connect_via_media_if_lastest_is_non_sass",
    "test_3_25_media_not_switch_media_different_account",
    "test_3_26_no_streaming_not_switch_phonecallout_different_account",
    "test_3_27_auto_connect_via_media_different_accounts",
    "test_3_28_auto_connect_via_phonecallout_different_accounts",
    "test_3_29_revert_resume_playing",
];

const E2E_MULTIPOINT_TEST_CASE: [&str; 28] = [
    "test_3_30_phonecallout_not_switch_phonecallout",
    "test_3_31_phonecallout_not_switch_voip",
    "test_3_32_phonecallout_not_switch_media",
    "test_3_33_phonecallout_not_switch_game",
    "test_3_34_media_switch_phonecallout",
    "test_3_35_media_switch_voip",
    "test_3_36_media_switch_media",
    "test_3_37_media_not_switch_game",
    "test_3_38_game_switch_phonecallout",
    "test_3_39_game_switch_voip",
    "test_3_40_game_switch_media",
    "test_3_41_game_switch_game",
    "test_3_42_no_streaming_switch_phonecallout",
    "test_3_43_no_streaming_switch_voip",
    "test_3_44_no_streaming_switch_media",
    "test_3_45_no_streaming_switch_game",
    "test_3_46_revert_resume_playing",
    "test_3_47_media_switch_phonecallout_non_sass",
    "test_3_48_media_not_switch_media_non_sass",
    "test_3_49_no_streaming_switch_media_non_sass",
    "test_3_50_media_non_sass_switch_phonecallout",
    "test_3_51_media_non_sass_not_switch_media",
    "test_3_52_phonecallout_non_sass_not_switch_phonecallout_third",
    "test_3_53_phonecallout_non_sass_not_switch_media_third",
    "test_3_54",
    "test_3_55_mixed_devices",
    "test_3_56",
    "test_3_57_avail_flag",
];

pub fn export_to_template(
    executions: &[ExecutionRow],
    template_path: &Path,
    output_path: &Path,
    sheet_name: &str,
    column: &str,
) -> AppResult<usize> {
    if !template_path.exists() {
        return Err(AppError::export(format!(
            "Template not found: {}",
            template_path.display()
        )));
    }

    if sheet_name.trim().is_empty() {
        return Err(AppError::validation(
            "Sheet name must not be empty.".to_string(),
        ));
    }
    if column.trim().is_empty() {
        return Err(AppError::validation(
            "Column must not be empty.".to_string(),
        ));
    }

    if let Some(parent) = output_path.parent() {
        fs::create_dir_all(parent).map_err(|error| {
            AppError::io(format!(
                "Failed to create output directory {}: {error}",
                parent.display()
            ))
        })?;
    }
    fs::copy(template_path, output_path).map_err(|error| {
        AppError::io(format!(
            "Failed to copy template {} -> {}: {error}",
            template_path.display(),
            output_path.display()
        ))
    })?;

    let mut workbook = umya_spreadsheet::reader::xlsx::read(output_path).map_err(|error| {
        AppError::export(format!(
            "Failed to open workbook {}: {error}",
            output_path.display()
        ))
    })?;
    let sheet = workbook
        .get_sheet_by_name_mut(sheet_name)
        .ok_or_else(|| AppError::export(format!("Sheet not found: {sheet_name}")))?;

    let row_dict = generate_row_dict();
    let start_col = alph_to_num(column)?;
    let mut updated_count = 0usize;

    for execution in executions {
        let (sub_test_name, num) = get_test_name(&execution.raw_name);
        let Some(base_row) = row_dict.get(sub_test_name.as_str()) else {
            continue;
        };
        let row = base_row + num;

        set_cell_if_allowed(
            sheet,
            row,
            start_col + RESULT_INDEX,
            Some(CellData::Text(String::new())),
        );
        set_cell_if_allowed(
            sheet,
            row,
            start_col + DETAILS_INDEX,
            Some(CellData::Text(String::new())),
        );

        match execution.result.as_str() {
            "PASS" => {
                set_cell_if_allowed(
                    sheet,
                    row,
                    start_col + RESULT_INDEX,
                    Some(CellData::Text("Y".to_string())),
                );
            }
            "SKIP" => {
                if let Some(detail) = execution.details.first() {
                    set_cell_if_allowed(
                        sheet,
                        row,
                        start_col + DETAILS_INDEX,
                        Some(CellData::Text(detail.clone())),
                    );
                }
            }
            _ => {
                let mut priority = "P2".to_string();
                if !execution.details.is_empty() {
                    let debug_message = execution.details.join("\n");
                    set_cell_if_allowed(
                        sheet,
                        row,
                        start_col + DETAILS_INDEX,
                        Some(CellData::Text(debug_message)),
                    );
                    for detail in &execution.details {
                        let next_priority = get_priority(detail);
                        if next_priority < priority {
                            priority = next_priority;
                        }
                    }
                }
                set_cell_if_allowed(
                    sheet,
                    row,
                    start_col + RESULT_INDEX,
                    Some(CellData::Text(priority)),
                );
            }
        }

        for (key, offset) in SPONGE_PROPERTIES_IN_SHEET {
            let target_col = start_col + offset;
            set_cell_if_allowed(sheet, row, target_col, Some(CellData::Text(String::new())));
            let Some(value) = execution.sponge_properties.get(key) else {
                continue;
            };
            let value = cell_data_from_json(value);
            set_cell_if_allowed(sheet, row, target_col, value);
        }

        updated_count += 1;
    }

    umya_spreadsheet::writer::xlsx::write(&workbook, output_path).map_err(|error| {
        AppError::export(format!(
            "Failed to write workbook {}: {error}",
            output_path.display()
        ))
    })?;

    Ok(updated_count)
}

#[derive(Debug, Clone)]
enum CellData {
    Text(String),
    Number(f64),
}

fn set_cell_if_allowed(
    sheet: &mut umya_spreadsheet::Worksheet,
    row: u32,
    col: u32,
    value: Option<CellData>,
) {
    let Some(value) = value else {
        return;
    };

    let existing = sheet.get_cell_value((col, row)).get_value().to_string();
    if existing == "N/A" {
        return;
    }

    match value {
        CellData::Text(text) => {
            sheet.get_cell_mut((col, row)).set_value(text);
        }
        CellData::Number(number) => {
            if (number - 100.0).abs() < f64::EPSILON || (number + 100.0).abs() < f64::EPSILON {
                return;
            }
            if number >= 0.0 {
                sheet.get_cell_mut((col, row)).set_value_number(number);
            }
        }
    }
}

fn cell_data_from_json(value: &serde_json::Value) -> Option<CellData> {
    if value.is_null() {
        return None;
    }
    if let Some(number) = value.as_f64() {
        return Some(CellData::Number(number));
    }
    if let Some(text) = value.as_str() {
        return Some(CellData::Text(text.to_string()));
    }
    Some(CellData::Text(value.to_string()))
}

pub fn generate_row_dict() -> HashMap<&'static str, u32> {
    let mut row_dict = HashMap::new();

    let state_start = 9_u32;
    for (index, test_case) in STATE_TEST_CASE.iter().enumerate() {
        row_dict.insert(*test_case, state_start + index as u32 * 3);
    }

    let key_state_start = 37_u32;
    for (index, test_case) in KEY_STATE_TEST_CASE.iter().enumerate() {
        row_dict.insert(*test_case, key_state_start + index as u32 * 3);
    }

    let key_state_multipoint_start = 59_u32;
    for (index, test_case) in KEY_STATE_MULTIPOINT_TEST_CASE.iter().enumerate() {
        row_dict.insert(*test_case, key_state_multipoint_start + index as u32 * 3);
    }

    let e2e_start = 74_u32;
    for (index, test_case) in E2E_TEST_CASE.iter().enumerate() {
        row_dict.insert(*test_case, e2e_start + index as u32 * 5);
    }

    let e2e_multipoint_start = 233_u32;
    for (index, test_case) in E2E_MULTIPOINT_TEST_CASE.iter().enumerate() {
        row_dict.insert(*test_case, e2e_multipoint_start + index as u32 * 5);
    }

    row_dict
}

pub fn alph_to_num(column: &str) -> AppResult<u32> {
    let cleaned = column.trim();
    if cleaned.is_empty() {
        return Err(AppError::validation(
            "Column must not be empty.".to_string(),
        ));
    }
    let mut result: u32 = 0;
    for ch in cleaned.chars() {
        if !ch.is_ascii_alphabetic() {
            return Err(AppError::validation(format!(
                "Invalid column character: {ch}"
            )));
        }
        result = result * 26 + (u32::from(ch.to_ascii_uppercase()) - u32::from('A') + 1);
    }
    Ok(result)
}

pub fn get_priority(message: &str) -> String {
    let regex = Regex::new(r"\[(?P<priority>P\d) issue\]").expect("valid regex");
    regex
        .captures(message)
        .and_then(|captures| captures.name("priority"))
        .map(|matched| matched.as_str().to_string())
        .unwrap_or_else(|| "P0".to_string())
}

pub fn get_test_name(test_name: &str) -> (String, u32) {
    let regex = Regex::new(r"^test_\d_\d{1,3}_\w+$").expect("valid regex");
    let Some((head, tail)) = test_name.rsplit_once('_') else {
        return (test_name.to_string(), 0);
    };
    let Ok(num) = tail.parse::<u32>() else {
        return (test_name.to_string(), 0);
    };
    if regex.is_match(head) {
        (head.to_string(), num)
    } else {
        (test_name.to_string(), 0)
    }
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeMap;
    use std::path::Path;

    use serde_json::json;

    use super::{alph_to_num, export_to_template, generate_row_dict, get_priority, get_test_name};
    use crate::domain::models::ExecutionRow;

    #[test]
    fn alph_to_num_converts_column_names() {
        assert_eq!(alph_to_num("A").unwrap(), 1);
        assert_eq!(alph_to_num("D").unwrap(), 4);
        assert_eq!(alph_to_num("AH").unwrap(), 34);
    }

    #[test]
    fn get_test_name_extracts_sub_name_and_iteration() {
        let (name, iteration) = get_test_name("test_1_01_most_recently_inuse_state_2");
        assert_eq!(name, "test_1_01_most_recently_inuse_state");
        assert_eq!(iteration, 2);
    }

    #[test]
    fn get_priority_defaults_to_p0_when_missing() {
        assert_eq!(get_priority("not tagged"), "P0");
        assert_eq!(get_priority("[P2 issue] hello"), "P2");
    }

    #[test]
    fn export_to_template_writes_expected_cells() {
        let mut workbook = umya_spreadsheet::new_file();
        let _ = workbook.new_sheet("Generic");
        let template_path = Path::new("/tmp/report_gen_export_template.xlsx");
        let output_path = Path::new("/tmp/report_gen_export_output.xlsx");
        umya_spreadsheet::writer::xlsx::write(&workbook, template_path).unwrap();

        let execution = ExecutionRow {
            execution_id: "test_1_01_most_recently_inuse_state_0-0".to_string(),
            raw_name: "test_1_01_most_recently_inuse_state_0".to_string(),
            base_name: "test_1_01_most_recently_inuse_state".to_string(),
            iteration: Some(0),
            result: "PASS".to_string(),
            details: vec![],
            sponge_properties: BTreeMap::from([("State change latency".to_string(), json!(3.125))]),
            begin_time: Some(0),
            end_time: Some(1),
        };

        let updated =
            export_to_template(&[execution], template_path, output_path, "Generic", "D").unwrap();
        assert_eq!(updated, 1);

        let row_dict = generate_row_dict();
        let row = *row_dict
            .get("test_1_01_most_recently_inuse_state")
            .expect("mapped row");

        let workbook = umya_spreadsheet::reader::xlsx::read(output_path).unwrap();
        let sheet = workbook.get_sheet_by_name("Generic").unwrap();
        assert_eq!(sheet.get_cell_value((4, row)).get_value(), "Y");
        assert_eq!(sheet.get_cell_value((14, row)).get_value(), "3.125");
    }
}
