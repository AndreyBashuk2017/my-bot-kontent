import base64
import httpx
from bot.agents.client import chat
from bot.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

IMAGE_PROMPT_SYSTEM = """Create a short English image generation prompt based on the post topic.
Style: professional photography, realistic, 16:9 landscape.
Max 15 words. Only the prompt — no explanations, no quotes."""


async def _make_prompt(post_text: str) -> str:
    return await chat(
        messages=[
            {"role": "system", "content": IMAGE_PROMPT_SYSTEM},
            {"role": "user", "content": post_text[:400]},
        ],
        max_tokens=50,
        temperature=0.5,
    )


async def generate_image(post_text: str) -> bytes:
    prompt = await _make_prompt(post_text)
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={
                "model": "google/gemini-2.5-flash-image",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        data = resp.json()

    images = data["choices"][0]["message"].get("images", [])
    if not images:
        raise ValueError("Модель не вернула изображение")

    data_url = images[0]["image_url"]["url"]
    base64_data = data_url.split(",", 1)[1]
    return base64.b64decode(base64_data)
