from typing import AsyncGenerator, Optional, Any
from openai import AsyncOpenAI
from app.core.interfaces.llm import BaseLLM
from app.core.config import settings


class OpenAILLM(BaseLLM):
    """
    OpenAI LLM provider.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key or settings.OPENAI_API_KEY)

    @staticmethod
    def supported_models() -> list[dict[str, Any]]:
        return [
            {
                "id": "gpt-4-turbo-preview",
                "name": "GPT-4 Turbo",
                "description": "Latest GPT-4 model with improved capability and knowledge.",
            },
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "description": "Fast and cost-effective model for simple tasks.",
            },
            {
                "id": "gpt-4o",
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
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=kwargs.get("model", "gpt-4-turbo-preview"),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            **kwargs
        )

        return response.choices[0].message.content or ""

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
            model=kwargs.get("model", "gpt-4-turbo-preview"),
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
