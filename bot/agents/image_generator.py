import urllib.parse
import httpx

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1280&height=720&nologo=true&model=flux"
HEADERS = {"User-Agent": "Mozilla/5.0"}


async def generate_image(post_text: str) -> bytes:
    context = post_text[:300]
    prompt = f"professional photography, realistic, 16:9 landscape format, {context}"
    encoded = urllib.parse.quote(prompt)
    url = POLLINATIONS_URL.format(prompt=encoded)

    async with httpx.AsyncClient(timeout=90, follow_redirects=True, headers=HEADERS) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content
