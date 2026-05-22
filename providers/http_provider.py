from __future__ import annotations

from time import perf_counter
from typing import Any

import httpx

from orchestration.config import ProviderSettings
from providers.base import ProviderClient, ProviderRequest, ProviderResponse


class ProviderExecutionError(RuntimeError):
    pass


class HttpProvider(ProviderClient):
    def __init__(self, *, settings: ProviderSettings, api_key: str | None) -> None:
        self._settings = settings
        self._api_key = api_key

    async def complete(self, request: ProviderRequest) -> ProviderResponse:
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "trace_id": request.trace_id,
        }

        headers: dict[str, str] = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        start = perf_counter()
        last_error: Exception | None = None

        async with httpx.AsyncClient(timeout=request.timeout_seconds) as client:
            for _ in range(self._settings.max_retries + 1):
                try:
                    response = await client.post(
                        self._settings.base_url,
                        json=payload,
                        headers=headers,
                    )
                    response.raise_for_status()
                    latency_ms = int((perf_counter() - start) * 1000)
                    data = response.json()
                    text = _extract_text(data)
                    return ProviderResponse(
                        text=text,
                        usage_input_tokens=_extract_usage(data, "input_tokens"),
                        usage_output_tokens=_extract_usage(data, "output_tokens"),
                        latency_ms=latency_ms,
                    )
                except Exception as exc:  # noqa: BLE001
                    last_error = exc

        raise ProviderExecutionError("Provider request failed after retries") from last_error

    async def stream_complete(self, request: ProviderRequest):
        response = await self.complete(request)
        for chunk in response.text.split():
            yield f"{chunk} "


def _extract_text(payload: dict[str, Any]) -> str:
    direct = payload.get("text")
    if isinstance(direct, str):
        return direct

    output = payload.get("output")
    if isinstance(output, str):
        return output

    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            candidate = first.get("text")
            if isinstance(candidate, str):
                return candidate

    raise ProviderExecutionError("Provider response did not include a supported text field")


def _extract_usage(payload: dict[str, Any], field: str) -> int:
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return 0
    value = usage.get(field)
    return int(value) if isinstance(value, int | float) else 0
