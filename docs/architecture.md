# Monad Architecture

## Layer Responsibilities

- Python (`orchestration/`, `providers/`, `repair/`, `state/`): agent coordination, provider routing, event orchestration, repair planning.
- Rust (`runtime/`): subprocess management, timeout enforcement, stream capture, sandbox policy enforcement.
- Compiler/Diagnostics (`compiler/`, `diagnostics/`): diagnostic normalization and failure classification.

## Deterministic Event Model

All critical operations emit immutable events (`orchestration/events/models.py`) and are persisted append-only (`orchestration/events/store.py`).

Event examples:

- `prompt_issued`
- `provider_requested`
- `provider_responded`
- `compile_executed`
- `diagnostic_emitted`
- `repair_generated`
- `run_failed`

## Security Posture

- Fail-closed command validation in both Python sandbox policy and Rust runtime sandbox.
- No hidden background execution behavior.
- Runtime command, timeouts, and limits are configuration-driven.

## Extension Points

- Add providers by registering factories in `providers/registry.py`.
- Add agent roles in `orchestration/agents.py`.
- Add diagnostics classifiers in `diagnostics/classifier.py`.
- Swap event storage with any implementation matching `EventStore` protocol.
- Runtime execution bridge lives in `bindings/runtime_client.py` (`RustRuntimeClient`) and communicates with Rust runtime via JSON stdin/stdout.
