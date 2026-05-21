use thiserror::Error;

#[derive(Debug, Error)]
pub enum RuntimeError {
    #[error("sandbox policy denied command: {0}")]
    SandboxDenied(String),

    #[error("invalid request: {0}")]
    InvalidRequest(String),

    #[error("process spawn failed: {0}")]
    SpawnFailed(String),

    #[error("process execution timed out")]
    Timeout,

    #[error("process wait failed: {0}")]
    WaitFailed(String),

    #[error("io failure: {0}")]
    Io(String),
}
