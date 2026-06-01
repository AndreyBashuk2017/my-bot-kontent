import openai
from bot.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

openai_client = openai.AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)

_MODELS = [
    "anthropic/claude-haiku-4-5",
    "openai/gpt-oss-120b:free",
    "google/gemma-4-31b-it:free",
    "openai/gpt-oss-20b:free",
]


async def chat(messages: list, max_tokens: int = 600, temperature: float = 0.7) -> str:
    last_error: Exception | None = None
    for model in _MODELS:
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
        except openai.APIStatusError as e:
            if e.status_code == 402:
                last_error = e
                continue
            raise
    raise last_error  # type: ignore[misc]
