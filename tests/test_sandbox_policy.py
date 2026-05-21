from __future__ import annotations

from pathlib import Path

from orchestration.config import SandboxSettings
from sandbox import SandboxPolicy


def test_sandbox_denies_unapproved_command_and_path() -> None:
    policy = SandboxPolicy(
        SandboxSettings(
            allowed_command_prefixes=["cargo"],
            allowed_read_roots=["."],
            allowed_write_roots=["."],
        )
    )

    assert policy.command_allowed(["python", "-c", "print('x')"]) is False
    assert policy.read_allowed(Path("/tmp/outside")) is False
