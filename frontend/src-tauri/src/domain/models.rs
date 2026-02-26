use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SummaryInput {
    pub name: String,
    pub content: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionRow {
    pub execution_id: String,
    pub raw_name: String,
    pub base_name: String,
    pub iteration: Option<u32>,
    pub result: String,
    pub details: Vec<String>,
    pub sponge_properties: BTreeMap<String, serde_json::Value>,
    pub begin_time: Option<i64>,
    pub end_time: Option<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResultTotals {
    pub total: usize,
    pub by_result: BTreeMap<String, usize>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GroupRow {
    pub base_name: String,
    pub total: usize,
    pub by_result: BTreeMap<String, usize>,
    pub latest_result: String,
    pub group_result: String,
    pub failure_count: usize,
    pub error_rate: f64,
    pub latency_averages: BTreeMap<String, f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParseSummaryResponse {
    pub summary_id: String,
    pub requested_tests: Vec<String>,
    pub imported_summaries: Vec<ImportedSummaryInfo>,
    pub group_rows: Vec<GroupRow>,
    pub totals: ResultTotals,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImportedSummaryInfo {
    pub name: String,
    pub controller_info: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GroupExecutionsResponse {
    pub base_name: String,
    pub latency_averages: BTreeMap<String, f64>,
    pub executions: Vec<ExecutionRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProblemTestsResponse {
    pub tests: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportRequest {
    pub summary_id: String,
    pub template_path: String,
    pub output_path: String,
    pub sheet_name: String,
    pub column: String,
    pub debug_mode: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportResponse {
    pub output_path: String,
    pub exported_count: usize,
}

#[derive(Debug, Clone)]
pub struct ParsedSummary {
    pub requested_tests: Vec<String>,
    pub controller_info: Option<serde_json::Value>,
    pub executions: Vec<ExecutionRow>,
}
