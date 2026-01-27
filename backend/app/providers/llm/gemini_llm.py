from typing import AsyncGenerator, Optional, Any, Dict
from google import genai
from app.core.interfaces.llm import BaseLLM, LLMResponse
from app.core.config import settings
from app.core.constants import GeminiModel

# Global client cache
_gemini_clients: Dict[str, genai.Client] = {}


class GeminiLLM(BaseLLM):
    """
    Gemini LLM provider using google-genai library with client caching.
    """

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or settings.GOOGLE_API_KEY
        if self._api_key not in _gemini_clients:
            _gemini_clients[self._api_key] = genai.Client(api_key=self._api_key)
        self.client = _gemini_clients[self._api_key]

    @staticmethod
    def supported_models() -> list[dict[str, Any]]:
        return [
            {
                "id": GeminiModel.GEMINI_2_5_FLASH,
                "name": "Gemini 2.5 Flash",
                "description": "Fast and versatile multimodal model.",
            },
            {
                "id": GeminiModel.GEMINI_2_5_PRO,
                "name": "Gemini 2.5 Pro",
                "description": "High-intelligence model for complex tasks.",
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
        model = kwargs.get("model", GeminiModel.GEMINI_2_5_FLASH)

        response = await self.client.aio.models.generate_content(
            model=model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
                **{k: v for k, v in kwargs.items() if k not in ["model"]}
            ),
        )

        content = response.text or ""
        usage = response.usage_metadata

        return LLMResponse(
            content=content,
            model_name=model,
            prompt_tokens=usage.prompt_token_count if usage else None,
            completion_tokens=usage.candidates_token_count if usage else None,
            total_tokens=usage.total_token_count if usage else None,
        )

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        model = kwargs.get("model", GeminiModel.GEMINI_2_5_FLASH)

        stream = await self.client.aio.models.generate_content_stream(
            model=model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
                **{k: v for k, v in kwargs.items() if k not in ["model"]}
            ),
        )

        async for chunk in stream:
            if chunk.text:
                yield chunk.text
