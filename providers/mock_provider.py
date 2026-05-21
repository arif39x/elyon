from __future__ import annotations

import asyncio

from providers.base import ProviderClient, ProviderRequest, ProviderResponse


class MockProvider(ProviderClient):
    def __init__(self, *, response_text: str, chunk_delay_seconds: float = 0.0) -> None:
        self._response_text = response_text
        self._chunk_delay_seconds = chunk_delay_seconds

    async def complete(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            text=f"{self._response_text}\n{request.prompt}",
            usage_input_tokens=len(request.prompt.split()),
            usage_output_tokens=len(self._response_text.split()),
            latency_ms=1,
        )

    async def stream_complete(self, request: ProviderRequest):
        text = f"{self._response_text} {request.prompt}"
        for chunk in text.split():
            if self._chunk_delay_seconds > 0:
                await asyncio.sleep(self._chunk_delay_seconds)
            yield f"{chunk} "
