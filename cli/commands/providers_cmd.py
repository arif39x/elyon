from __future__ import annotations

from cli.context import CliContext


def execute(context: CliContext) -> dict[str, object]:
    providers = []
    for name in context.providers.list_names():
        provider_settings = context.settings.provider(name)
        providers.append(
            {
                "name": provider_settings.name,
                "model": provider_settings.model,
                "timeout_seconds": provider_settings.timeout_seconds,
                "max_retries": provider_settings.max_retries,
                "remote": provider_settings.base_url is not None,
            }
        )

    return {"status": "ok", "providers": providers}
