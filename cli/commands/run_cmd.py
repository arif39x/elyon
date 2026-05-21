from __future__ import annotations

from uuid import uuid4

from cli.context import CliContext


async def execute(
    context: CliContext,
    *,
    prompt: str,
    provider: str | None,
    stream: bool,
    session_id: str | None,
) -> dict[str, object]:
    trace_id = str(uuid4())
    output = await context.engine.run_prompt(
        prompt=prompt,
        provider_name=provider,
        trace_id=trace_id,
        session_id=session_id,
        stream=stream,
    )
    return {
        "status": "ok",
        "trace_id": trace_id,
        "provider": provider or context.settings.default_provider,
        "output": output,
    }
