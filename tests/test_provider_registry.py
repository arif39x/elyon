from __future__ import annotations

import asyncio

import pytest

from providers import MockProvider, ProviderRegistry


def test_provider_registry_initializes_provider_once() -> None:
    async def scenario() -> None:
        registry = ProviderRegistry()
        calls = {"count": 0}

        def factory() -> MockProvider:
            calls["count"] += 1
            return MockProvider(response_text="ok")

        registry.register_factory("mock", factory)

        first = await registry.get("mock")
        second = await registry.get("mock")

        assert first is second
        assert calls["count"] == 1

    asyncio.run(scenario())


def test_provider_registry_raises_for_unknown_provider() -> None:
    async def scenario() -> None:
        registry = ProviderRegistry()

        with pytest.raises(KeyError):
            await registry.get("missing")

    asyncio.run(scenario())
