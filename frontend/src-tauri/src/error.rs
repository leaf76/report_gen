use serde::Serialize;
use thiserror::Error;
use uuid::Uuid;

pub type AppResult<T> = Result<T, AppError>;
pub type CommandResult<T> = Result<T, AppErrorPayload>;

#[derive(Debug, Clone, Serialize)]
pub struct AppErrorPayload {
    pub error: String,
    pub code: String,
    pub trace_id: String,
}

#[derive(Debug, Error)]
pub enum AppError {
    #[error("{0}")]
    Validation(String),
    #[error("{0}")]
    Parse(String),
    #[error("{0}")]
    NotFound(String),
    #[error("{0}")]
    Export(String),
    #[error("{0}")]
    Io(String),
    #[error("{0}")]
    Internal(String),
}

impl AppError {
    pub fn validation(message: String) -> Self {
        Self::Validation(message)
    }

    pub fn parse(message: String) -> Self {
        Self::Parse(message)
    }

    pub fn not_found(message: String) -> Self {
        Self::NotFound(message)
    }

    pub fn export(message: String) -> Self {
        Self::Export(message)
    }

    pub fn io(message: String) -> Self {
        Self::Io(message)
    }

    pub fn internal(message: String) -> Self {
        Self::Internal(message)
    }

    pub fn code(&self) -> &'static str {
        match self {
            Self::Validation(_) => "ERR_VALIDATION",
            Self::Parse(_) => "ERR_PARSE",
            Self::NotFound(_) => "ERR_NOT_FOUND",
            Self::Export(_) => "ERR_EXPORT",
            Self::Io(_) => "ERR_IO",
            Self::Internal(_) => "ERR_INTERNAL",
        }
    }

    pub fn to_payload(&self) -> AppErrorPayload {
        AppErrorPayload {
            error: self.to_string(),
            code: self.code().to_string(),
            trace_id: Uuid::new_v4().to_string(),
        }
    }
}

impl From<std::io::Error> for AppError {
    fn from(value: std::io::Error) -> Self {
        Self::io(value.to_string())
    }
}
