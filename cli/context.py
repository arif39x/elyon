from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bindings import RuntimeClient, RustRuntimeClient
from orchestration import MonadEngine, MonadSettings, load_settings
from orchestration.events import JsonlEventStore
from orchestration.logging import configure_logging
from providers import MockProvider, ProviderRegistry, build_registry
from state import InMemorySessionStore


@dataclass(frozen=True)
class CliContext:
    settings: MonadSettings
    engine: MonadEngine
    providers: ProviderRegistry
    event_store: JsonlEventStore
    runtime_client: RuntimeClient


def build_context(config_path: Path) -> CliContext:
    settings = load_settings(config_path)
    configure_logging(settings.telemetry)

    event_store = JsonlEventStore(path=Path(settings.state.event_log_path))
    providers = build_registry(settings)

    for provider_name, provider_settings in settings.providers.items():
        if provider_settings.base_url is None:
            providers.register_factory(
                provider_name,
                lambda provider_name=provider_name: MockProvider(
                    response_text=f"{provider_name}:ok"
                ),
            )

    runtime_client = RustRuntimeClient(
        runtime_command=settings.runtime.command,
        allowed_command_prefixes=settings.sandbox.allowed_command_prefixes,
    )

    engine = MonadEngine(
        settings=settings,
        event_store=event_store,
        session_store=InMemorySessionStore(),
        provider_registry=providers,
        runtime_client=runtime_client,
    )

    return CliContext(
        settings=settings,
        engine=engine,
        providers=providers,
        event_store=event_store,
        runtime_client=runtime_client,
    )
