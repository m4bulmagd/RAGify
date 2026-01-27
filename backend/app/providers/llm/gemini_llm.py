from typing import AsyncGenerator, Optional, Any
from google import genai
from app.core.interfaces.llm import BaseLLM
from app.core.config import settings


class GeminiLLM(BaseLLM):
    """
    Gemini LLM provider using google-genai library.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.client = genai.Client(api_key=api_key or settings.GOOGLE_API_KEY)

    @staticmethod
    def supported_models() -> list[dict[str, Any]]:
        return [
            {
                "id": "gemini-2.5-flash",
                "name": "Gemini 2.5 Flash",
                "description": "Fast and versatile multimodal model.",
            },
            {
                "id": "gemini-2.5-pro",
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
    ) -> str:
        # Construct config
        config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        # Combine system prompt with user prompt if needed, strictly Gemini 2.5 supports system_instruction
        # but for broad attributes usage we can check argument support
        model = kwargs.get("model", "gemini-2.5-flash")

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

        return response.text or ""

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        model = kwargs.get("model", "gemini-2.5-flash")

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
