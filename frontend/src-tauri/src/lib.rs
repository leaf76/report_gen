mod commands;
mod domain;
mod error;
mod state;

use state::AppState;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(AppState::default())
        .invoke_handler(tauri::generate_handler![
            commands::parse_summaries,
            commands::get_group_executions,
            commands::get_problem_tests,
            commands::export_report,
            commands::health
        ])
        .run(tauri::generate_context!())
        .expect("failed to run tauri application");
}
