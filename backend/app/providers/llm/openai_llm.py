from typing import AsyncGenerator, Optional, Any, Dict
from openai import AsyncOpenAI
from app.core.interfaces.llm import BaseLLM, LLMResponse
from app.core.config import settings
from app.core.constants import OpenAIModel

# Global client cache
_openai_clients: Dict[str, AsyncOpenAI] = {}


class OpenAILLM(BaseLLM):
    """
    OpenAI LLM provider with client caching.
    """

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or settings.OPENAI_API_KEY
        if self._api_key not in _openai_clients:
            _openai_clients[self._api_key] = AsyncOpenAI(api_key=self._api_key)
        self.client = _openai_clients[self._api_key]

    @staticmethod
    def supported_models() -> list[dict[str, Any]]:
        return [
            {
                "id": OpenAIModel.GPT_4_TURBO_PREVIEW,
                "name": "GPT-4 Turbo",
                "description": "Latest GPT-4 model with improved capability and knowledge.",
            },
            {
                "id": OpenAIModel.GPT_3_5_TURBO,
                "name": "GPT-3.5 Turbo",
                "description": "Fast and cost-effective model for simple tasks.",
            },
            {
                "id": OpenAIModel.GPT_4O,
                "name": "GPT-4o",
                "description": "Omni model with high intelligence and speed.",
            },
        ]

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any
    ) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        model = kwargs.get("model", OpenAIModel.GPT_4_TURBO_PREVIEW)
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            **{k: v for k, v in kwargs.items() if k not in ["model"]}
        )

        content = response.choices[0].message.content or ""
        usage = response.usage

        return LLMResponse(
            content=content,
            model_name=model,
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
        )

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        stream = await self.client.chat.completions.create(
            model=kwargs.get("model", OpenAIModel.GPT_4_TURBO_PREVIEW),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )

        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
