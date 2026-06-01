import openai
from bot.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

_client = openai.AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)

_NICHE_PROMPT = """Find 3 trending topics for Telegram posts in the niche: {niche}.

Requirements:
- Topics are relevant right now (last 1-2 weeks)
- Each is a concrete post idea, not a generic category
- Reply in Russian

Respond with EXACTLY 3 lines, one topic per line, no numbering, no extra text."""

_TOPIC_PROMPT = """Find 3 trending angles for writing about: {topic}.

Requirements:
- Tied to real events or discussions from the last 1-2 weeks
- Unexpected or interesting angles for a Telegram post
- Reply in Russian

Respond with EXACTLY 3 lines, one angle per line, no numbering, no extra text."""


async def search_by_niche(niche: str) -> list[str]:
    return await _search(_NICHE_PROMPT.format(niche=niche))


async def search_by_topic(topic: str) -> list[str]:
    return await _search(_TOPIC_PROMPT.format(topic=topic))


async def _search(prompt: str) -> list[str]:
    response = await _client.chat.completions.create(
        model="perplexity/sonar",
        max_tokens=300,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.choices[0].message.content.strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    cleaned = []
    for line in lines:
        if line and line[0].isdigit() and len(line) > 2 and line[1] in '.) ':
            line = line[2:].strip()
        cleaned.append(line)
    return cleaned[:3]
