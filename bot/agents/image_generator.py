import urllib.parse
import httpx
from bot.agents.client import chat

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1280&height=720&nologo=true&model=flux"
HEADERS = {"User-Agent": "Mozilla/5.0"}

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
    encoded = urllib.parse.quote(prompt)
    url = POLLINATIONS_URL.format(prompt=encoded)

    async with httpx.AsyncClient(timeout=90, follow_redirects=True, headers=HEADERS) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content
