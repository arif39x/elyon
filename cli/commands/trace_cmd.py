from __future__ import annotations

from cli.context import CliContext


async def execute(context: CliContext, *, trace_id: str) -> dict[str, object]:
    events = await context.engine.events_for_trace(trace_id)
    return {
        "status": "ok",
        "trace_id": trace_id,
        "events": [event.model_dump(mode="json") for event in events],
    }
