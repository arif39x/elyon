use crate::error::RuntimeError;
use tokio::io::{AsyncRead, AsyncReadExt, BufReader};

pub async fn read_limited<R>(reader: R, limit: usize) -> Result<String, RuntimeError>
where
    R: AsyncRead + Unpin,
{
    let mut buffer = Vec::new();
    let mut wrapped = BufReader::new(reader);
    wrapped
        .read_to_end(&mut buffer)
        .await
        .map_err(|err| RuntimeError::Io(err.to_string()))?;

    if buffer.len() > limit {
        buffer.truncate(limit);
    }

    Ok(String::from_utf8_lossy(&buffer).into_owned())
}
