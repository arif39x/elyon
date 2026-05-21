from __future__ import annotations

from typing import AsyncIterator, Protocol

from pydantic import BaseModel, Field


class ProviderRequest(BaseModel):
    prompt: str
    model: str
    temperature: float = Field(ge=0, le=2)
    max_tokens: int = Field(gt=0)
    timeout_seconds: float = Field(gt=0)
    trace_id: str


class ProviderResponse(BaseModel):
    text: str
    usage_input_tokens: int = Field(ge=0)
    usage_output_tokens: int = Field(ge=0)
    latency_ms: int = Field(ge=0)


class ProviderClient(Protocol):
    async def complete(self, request: ProviderRequest) -> ProviderResponse: ...

    async def stream_complete(self, request: ProviderRequest) -> AsyncIterator[str]: ...
