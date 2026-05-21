from __future__ import annotations

import asyncio
import sys

import pytest

from bindings import (
    RuntimeExecLimits,
    RuntimeExecRequest,
    RuntimeExecutionError,
    RustRuntimeClient,
)


def test_runtime_client_parses_success_response() -> None:
    async def scenario() -> None:
        script = (
            "import json,sys;"
            "json.loads(sys.stdin.read());"
            "print(json.dumps({'exit_code':0,'stdout':'ok','stderr':'','duration_ms':3}))"
        )
        client = RustRuntimeClient(
            runtime_command=[sys.executable, "-c", script],
            allowed_command_prefixes=["pytest"],
        )
        response = await client.execute(
            RuntimeExecRequest(
                command=["pytest", "-q"],
                cwd=".",
                limits=RuntimeExecLimits(
                    timeout_seconds=1.0,
                    max_stdout_bytes=1024,
                    max_stderr_bytes=1024,
                ),
            )
        )

        assert response.exit_code == 0
        assert response.stdout == "ok"
        assert response.duration_ms == 3

    asyncio.run(scenario())


def test_runtime_client_raises_on_runtime_error_payload() -> None:
    async def scenario() -> None:
        script = (
            "import json,sys;"
            "json.loads(sys.stdin.read());"
            "print(json.dumps({'error':'sandbox policy denied command: rm'}));"
            "raise SystemExit(1)"
        )
        client = RustRuntimeClient(
            runtime_command=[sys.executable, "-c", script],
            allowed_command_prefixes=["pytest"],
        )

        with pytest.raises(RuntimeExecutionError, match="sandbox policy denied command"):
            await client.execute(
                RuntimeExecRequest(
                    command=["rm", "-rf", "tmp"],
                    cwd=".",
                    limits=RuntimeExecLimits(
                        timeout_seconds=1.0,
                        max_stdout_bytes=1024,
                        max_stderr_bytes=1024,
                    ),
                )
            )

    asyncio.run(scenario())
