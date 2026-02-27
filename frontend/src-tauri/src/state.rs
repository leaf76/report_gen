use std::collections::HashMap;
use std::sync::Mutex;

use crate::domain::models::{ExecutionRow, GroupRow};

#[derive(Debug, Clone)]
pub struct SummarySession {
    pub executions: Vec<ExecutionRow>,
    pub group_rows: Vec<GroupRow>,
}

#[derive(Default)]
pub struct AppState {
    pub sessions: Mutex<HashMap<String, SummarySession>>,
}
