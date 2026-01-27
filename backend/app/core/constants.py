from enum import Enum


class OpenAIModel(str, Enum):
    GPT_4_TURBO_PREVIEW = "gpt-4-turbo-preview"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4O = "gpt-4o"


class GeminiModel(str, Enum):
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_PRO = "gemini-2.5-pro"


class EmbeddingModel(str, Enum):
    OPENAI_TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"
    GEMINI_EMBEDDING_001 = "gemini-embedding-001"
    COHERE_EMBED_ENGLISH_V3 = "embed-english-v3.0"


DEFAULT_LLM_MODEL = OpenAIModel.GPT_4_TURBO_PREVIEW
DEFAULT_EMBEDDING_MODEL = EmbeddingModel.GEMINI_EMBEDDING_001
DEFAULT_EMBEDDING_DIMENSIONS = 1536
