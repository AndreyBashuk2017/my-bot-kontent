import openai
from bot.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

openai_client = openai.AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)

_FALLBACK_MODELS = [
    "openai/gpt-oss-120b:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "openai/gpt-oss-20b:free",
]


async def chat(messages: list, max_tokens: int = 600, temperature: float = 0.7) -> str:
    last_error: Exception | None = None
    for model in _FALLBACK_MODELS:
        try:
            response = await openai_client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
            )
            return response.choices[0].message.content.strip()
        except openai.RateLimitError as e:
            last_error = e
            continue
    raise last_error  # type: ignore[misc]
