use tauri::State;
use uuid::Uuid;

use crate::domain::aggregate::{build_group_rows, collect_problem_tests, compute_result_totals};
use crate::domain::export::export_to_template;
use crate::domain::models::{
    ExportRequest, ExportResponse, GroupExecutionsResponse, ImportedSummaryInfo,
    ParseSummaryResponse, ProblemTestsResponse, SummaryInput,
};
use crate::domain::summary::{merge_summaries, parse_summary_documents};
use crate::error::{AppError, AppResult, CommandResult};
use crate::state::{AppState, SummarySession};

#[derive(Debug, serde::Deserialize)]
pub struct GroupExecutionsArgs {
    pub summary_id: String,
    pub base_name: String,
}

#[derive(Debug, serde::Deserialize)]
pub struct ProblemTestsArgs {
    pub summary_id: String,
}

#[tauri::command]
pub fn parse_summaries(
    inputs: Vec<SummaryInput>,
    state: State<'_, AppState>,
) -> CommandResult<ParseSummaryResponse> {
    run_and_map_error(|| parse_summaries_impl(inputs, state))
}

#[tauri::command]
pub fn get_group_executions(
    args: GroupExecutionsArgs,
    state: State<'_, AppState>,
) -> CommandResult<GroupExecutionsResponse> {
    run_and_map_error(|| get_group_executions_impl(args, state))
}

#[tauri::command]
pub fn get_problem_tests(
    args: ProblemTestsArgs,
    state: State<'_, AppState>,
) -> CommandResult<ProblemTestsResponse> {
    run_and_map_error(|| get_problem_tests_impl(args, state))
}

#[tauri::command]
pub fn export_report(
    request: ExportRequest,
    state: State<'_, AppState>,
) -> CommandResult<ExportResponse> {
    run_and_map_error(|| export_report_impl(request, state))
}

#[tauri::command]
pub fn health() -> serde_json::Value {
    serde_json::json!({
      "status": "ok",
      "app_version": env!("CARGO_PKG_VERSION")
    })
}

fn parse_summaries_impl(
    inputs: Vec<SummaryInput>,
    state: State<'_, AppState>,
) -> AppResult<ParseSummaryResponse> {
    if inputs.is_empty() {
        return Err(AppError::validation(
            "Please select at least one summary file.".to_string(),
        ));
    }

    let mut parsed_summaries = Vec::new();
    let mut imported_summaries = Vec::new();
    for input in inputs {
        if input.content.trim().is_empty() {
            return Err(AppError::validation(format!(
                "Summary content is empty: {}",
                input.name
            )));
        }
        let parsed_summary = parse_summary_documents(&input.content)?;
        imported_summaries.push(ImportedSummaryInfo {
            name: input.name,
            controller_info: parsed_summary.controller_info.clone(),
        });
        parsed_summaries.push(parsed_summary);
    }

    let merged = merge_summaries(&parsed_summaries);
    let totals = compute_result_totals(&merged.executions);
    let group_rows = build_group_rows(&merged.executions);
    let summary_id = Uuid::new_v4().to_string();

    let session = SummarySession {
        executions: merged.executions.clone(),
        group_rows: group_rows.clone(),
    };

    state
        .sessions
        .lock()
        .map_err(|_| AppError::internal("Failed to lock app state.".to_string()))?
        .insert(summary_id.clone(), session);

    Ok(ParseSummaryResponse {
        summary_id,
        requested_tests: merged.requested_tests,
        imported_summaries,
        group_rows,
        totals,
    })
}

fn get_group_executions_impl(
    args: GroupExecutionsArgs,
    state: State<'_, AppState>,
) -> AppResult<GroupExecutionsResponse> {
    let sessions = state
        .sessions
        .lock()
        .map_err(|_| AppError::internal("Failed to lock app state.".to_string()))?;
    let session = sessions.get(&args.summary_id).ok_or_else(|| {
        AppError::not_found(format!("Summary session not found: {}", args.summary_id))
    })?;

    let row = session
        .group_rows
        .iter()
        .find(|row| row.base_name == args.base_name)
        .ok_or_else(|| AppError::not_found(format!("Group not found: {}", args.base_name)))?;

    let mut executions = session
        .executions
        .iter()
        .filter(|execution| execution.base_name == args.base_name)
        .cloned()
        .collect::<Vec<_>>();

    executions.sort_by(|left, right| {
        left.begin_time
            .unwrap_or(-1)
            .cmp(&right.begin_time.unwrap_or(-1))
            .then(
                left.iteration
                    .unwrap_or(0)
                    .cmp(&right.iteration.unwrap_or(0)),
            )
    });

    Ok(GroupExecutionsResponse {
        base_name: args.base_name,
        latency_averages: row.latency_averages.clone(),
        executions,
    })
}

fn get_problem_tests_impl(
    args: ProblemTestsArgs,
    state: State<'_, AppState>,
) -> AppResult<ProblemTestsResponse> {
    let sessions = state
        .sessions
        .lock()
        .map_err(|_| AppError::internal("Failed to lock app state.".to_string()))?;
    let session = sessions.get(&args.summary_id).ok_or_else(|| {
        AppError::not_found(format!("Summary session not found: {}", args.summary_id))
    })?;
    Ok(ProblemTestsResponse {
        tests: collect_problem_tests(&session.group_rows),
    })
}

fn export_report_impl(
    request: ExportRequest,
    state: State<'_, AppState>,
) -> AppResult<ExportResponse> {
    let sessions = state
        .sessions
        .lock()
        .map_err(|_| AppError::internal("Failed to lock app state.".to_string()))?;
    let session = sessions.get(&request.summary_id).ok_or_else(|| {
        AppError::not_found(format!("Summary session not found: {}", request.summary_id))
    })?;

    let template_path = std::path::PathBuf::from(&request.template_path);
    let output_path = std::path::PathBuf::from(&request.output_path);

    let exported_count = export_to_template(
        &session.executions,
        &template_path,
        &output_path,
        &request.sheet_name,
        &request.column,
    )?;

    Ok(ExportResponse {
        output_path: output_path
            .canonicalize()
            .unwrap_or(output_path)
            .to_string_lossy()
            .to_string(),
        exported_count,
    })
}

fn run_and_map_error<T, F>(f: F) -> CommandResult<T>
where
    F: FnOnce() -> AppResult<T>,
{
    f().map_err(|error| error.to_payload())
}
