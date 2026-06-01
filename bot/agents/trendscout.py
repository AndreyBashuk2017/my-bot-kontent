import asyncio
import os
import time
import openai
from bot.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

_client = openai.AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)

_NICHE_PROMPT = """Find 5 trending topics for Telegram posts in the niche: {niche}.

Requirements:
- Topics are relevant right now (last 1-2 weeks)
- Each is a concrete post idea, not a generic category
- Reply in Russian

Respond with EXACTLY 5 lines, one topic per line, no numbering, no extra text."""

_TOPIC_PROMPT = """Find 5 trending angles for writing about: {topic}.

Requirements:
- Tied to real events or discussions from the last 1-2 weeks
- Unexpected or interesting angles for a Telegram post
- Reply in Russian

Respond with EXACTLY 5 lines, one angle per line, no numbering, no extra text."""


async def _get_google_trends(keyword: str) -> list[str]:
    """Fetch rising queries from Google Trends (Russia, last 7 days)."""
    loop = asyncio.get_event_loop()

    def _fetch():
        os.environ.setdefault("TMPDIR", "/tmp")
        from pytrends.request import TrendReq

        short_kw = " ".join(keyword.split()[:3])
        pt = TrendReq(hl="ru-RU", tz=180)
        pt.build_payload([short_kw], timeframe="now 7-d", geo="RU")
        time.sleep(2)

        rel = pt.related_queries()
        rising = rel.get(short_kw, {}).get("rising")
        if rising is not None and not rising.empty:
            return rising["query"].head(5).tolist()

        top = rel.get(short_kw, {}).get("top")
        if top is not None and not top.empty:
            return top["query"].head(5).tolist()

        return []

    try:
        return await asyncio.wait_for(loop.run_in_executor(None, _fetch), timeout=15.0)
    except Exception:
        return []


DEFAULT_NICHE = "строительство загородных домов"


async def search_by_niche(niche: str) -> dict:
    gt_terms = await _get_google_trends(niche)

    extra = ""
    if gt_terms:
        extra = (
            f"\n\nGoogle Trends Russia rising searches this week: {', '.join(gt_terms[:5])}. "
            "Use this data to make topics more specific and timely."
        )

    topics = await _search(_NICHE_PROMPT.format(niche=niche) + extra)
    return {"topics": topics, "trending_searches": gt_terms}


async def search_by_topic(topic: str) -> dict:
    gt_terms = await _get_google_trends(topic)

    extra = ""
    if gt_terms:
        extra = (
            f"\n\nGoogle Trends Russia rising searches this week: {', '.join(gt_terms[:5])}. "
            "Incorporate relevant trends into the angles."
        )

    topics = await _search(_TOPIC_PROMPT.format(topic=topic) + extra)
    return {"topics": topics, "trending_searches": gt_terms}


async def _search(prompt: str) -> list[str]:
    response = await _client.chat.completions.create(
        model="perplexity/sonar",
        max_tokens=500,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.choices[0].message.content.strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    cleaned = []
    for line in lines:
        if line and line[0].isdigit() and len(line) > 2 and line[1] in ") .":
            line = line[2:].strip()
        cleaned.append(line)
    return cleaned[:5]
