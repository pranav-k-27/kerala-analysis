"""
╔══════════════════════════════════════════════════════════════╗
║   KERALA WAR ROOM 2026 — Malayalam RSS Ingestion &          ║
║   AI Summarizer Module                                      ║
║                                                             ║
║   Features:                                                 ║
║   1. Fetches from 12 Malayalam RSS feeds                   ║
║   2. Filters election-relevant articles                     ║
║   3. GPT-4o translates + summarizes Malayalam → English     ║
║   4. Extracts political intelligence signals                ║
║   5. FastAPI endpoints for React dashboard                  ║
╚══════════════════════════════════════════════════════════════╝

Usage (standalone):
    python malayalam_rss.py --fetch        # fetch + summarize
    python malayalam_rss.py --show         # show latest summaries

Usage (integrated into pipeline):
    from malayalam_rss import fetch_and_summarize_rss
    articles = await fetch_and_summarize_rss()
"""

import asyncio
import json
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

# ── OpenAI client ────────────────────────────────────────────
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Output directory ─────────────────────────────────────────
SUMMARIES_DIR = Path("summaries")
SUMMARIES_DIR.mkdir(exist_ok=True)


# ════════════════════════════════════════════════════════════
# RSS FEED REGISTRY — 12 Malayalam Sources
# ════════════════════════════════════════════════════════════

MALAYALAM_RSS_FEEDS = [
    # ── Tier 1: High circulation Malayalam dailies ──
    {
        "name":     "Mathrubhumi",
        "url":      "https://www.mathrubhumi.com/rss/politics.xml",
        "fallback": "https://www.mathrubhumi.com/rss/kerala.xml",
        "language": "ml",
        "tier":     1,
        "focus":    "politics",
    },
    {
        "name":     "Manorama Online",
        "url":      "https://www.onmanorama.com/rss/politics.xml",
        "fallback": "https://www.onmanorama.com/rss/home.xml",
        "language": "ml",
        "tier":     1,
        "focus":    "politics",
    },
    {
        "name":     "Mangalam",
        "url":      "https://www.mangalam.com/rss/politics",
        "fallback": "https://www.mangalam.com/feed/",
        "language": "ml",
        "tier":     1,
        "focus":    "politics",
    },
    {
        "name":     "Deepika",
        "url":      "https://www.deepika.com/rss/politics",
        "fallback": "https://www.deepika.com/feed/",
        "language": "ml",
        "tier":     1,
        "focus":    "politics",
    },

    # ── Tier 2: Malayalam TV news channels ──
    {
        "name":     "Asianet News",
        "url":      "https://asianetnews.com/feed/",
        "fallback": "https://asianetnews.com/rss/politics",
        "language": "ml",
        "tier":     2,
        "focus":    "breaking",
    },
    {
        "name":     "Media One",
        "url":      "https://www.mediaone.tv/feed/",
        "fallback": "https://www.mediaone.tv/rss/politics",
        "language": "ml",
        "tier":     2,
        "focus":    "politics",
    },
    {
        "name":     "Reporter TV",
        "url":      "https://reporterlive.com/feed/",
        "fallback": "https://reporterlive.com/rss/",
        "language": "ml",
        "tier":     2,
        "focus":    "breaking",
    },
    {
        "name":     "Janam TV",
        "url":      "https://www.janamtv.com/feed/",
        "fallback": "https://www.janamtv.com/rss/",
        "language": "ml",
        "tier":     2,
        "focus":    "politics",
    },

    # ── Tier 3: Digital Malayalam news ──
    {
        "name":     "Kerala Kaumudi",
        "url":      "https://www.keralakaumudi.com/en/rss/politics.xml",
        "fallback": "https://www.keralakaumudi.com/feed/",
        "language": "ml",
        "tier":     3,
        "focus":    "politics",
    },
    {
        "name":     "Veekshanam",
        "url":      "https://www.veekshanam.com/feed/",
        "fallback": "https://www.veekshanam.com/rss/",
        "language": "ml",
        "tier":     3,
        "focus":    "politics",
    },
    {
        "name":     "Deshabhimani",
        "url":      "https://www.deshabhimani.com/rss/politics",
        "fallback": "https://www.deshabhimani.com/feed/",
        "language": "ml",
        "tier":     3,
        "focus":    "politics",
        "note":     "CPI(M) aligned — good for LDF internal signals",
    },
    {
        "name":     "Janayugom",
        "url":      "https://www.janayugom.com/feed/",
        "fallback": "https://www.janayugom.com/rss/",
        "language": "ml",
        "tier":     3,
        "focus":    "politics",
        "note":     "CPI aligned — useful for LDF perspective",
    },
]

# ── Election keywords in Malayalam (transliterated) ──────────
ELECTION_KEYWORDS_ML = [
    # Parties / fronts
    "തിരഞ്ഞെടുപ്പ്", "തെരഞ്ഞെടുപ്പ്",  # election
    "UDF", "LDF", "NDA", "BJP", "Congress", "CPM", "CPI",
    "IUML", "Kerala Congress",
    # Leaders
    "സതീശൻ", "Satheesan", "പിണറായി", "Pinarayi",
    "രാഹുൽ", "Rahul", "ചെന്നിത്തല", "Chennithala",
    # Key issues
    "വോട്ട്", "vote", "സ്ഥാനാർഥി", "candidate",
    "പ്രകടനപത്രിക", "manifesto",
    "അഴിമതി", "corruption", "തൊഴിലില്ലായ്മ", "unemployment",
    "വിലക്കയറ്റം", "inflation", "ശബരിമല", "Sabarimala",
    # Districts
    "തിരുവനന്തപുരം", "Thiruvananthapuram",
    "കൊച്ചി", "Kochi", "Ernakulam",
    "തൃശ്ശൂർ", "Thrissur",
    "കോഴിക്കോട്", "Kozhikode",
    "മലപ്പുറം", "Malappuram",
]

# Same keywords in English for bilingual matching
ELECTION_KEYWORDS_EN = [
    "election", "vote", "UDF", "LDF", "BJP", "Congress", "CPM",
    "Pinarayi", "Satheesan", "Rahul", "Kerala", "constituency",
    "candidate", "manifesto", "poll", "assembly", "campaign",
    "inflation", "unemployment", "corruption", "Sabarimala",
    "Thrissur", "Kozhikode", "Malappuram", "Ernakulam",
    "Thiruvananthapuram", "Kollam", "Kannur", "Palakkad",
]


# ════════════════════════════════════════════════════════════
# DATA MODELS
# ════════════════════════════════════════════════════════════

@dataclass
class RSSArticle:
    """Raw article from RSS feed."""
    title:       str
    source:      str
    url:         str
    content:     str
    published:   str
    language:    str
    tier:        int
    is_election_relevant: bool = False


@dataclass
class SummarizedArticle:
    """AI-summarized + translated article."""
    # Original
    title_original:  str
    source:          str
    url:             str
    published:       str
    language:        str
    tier:            int

    # AI outputs
    title_english:   str
    summary_english: str
    political_angle: str   # UDF / LDF / NDA / NEUTRAL
    sentiment_score: float  # -1.0 to +1.0
    key_claims:      list
    districts_mentioned: list
    electoral_impact: str  # HIGH / MEDIUM / LOW
    urgency:         str   # BREAKING / TODAY / BACKGROUND

    # Meta
    summarized_at:   str


# ════════════════════════════════════════════════════════════
# RSS FETCHER
# ════════════════════════════════════════════════════════════

async def fetch_rss_feed(
    feed: dict,
    client: httpx.AsyncClient,
) -> list[RSSArticle]:
    """Fetch and parse a single RSS feed."""
    articles = []
    urls_to_try = [feed["url"]]
    if feed.get("fallback"):
        urls_to_try.append(feed["fallback"])

    for url in urls_to_try:
        try:
            resp = await client.get(
                url,
                timeout=10,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; WarRoomBot/2.0)",
                    "Accept": "application/rss+xml, application/xml, text/xml, */*",
                },
                follow_redirects=True,
            )
            if resp.status_code != 200:
                continue

            # Parse RSS/Atom XML
            root = ET.fromstring(resp.content)

            # Handle both RSS 2.0 and Atom
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            items = root.findall(".//item") or root.findall(".//atom:entry", ns)

            for item in items[:15]:  # Max 15 per feed
                # Extract fields (RSS 2.0 format)
                title   = _get_text(item, "title")
                link    = _get_text(item, "link") or _get_text(item, "guid")
                desc    = _get_text(item, "description") or _get_text(item, "summary")
                pubdate = _get_text(item, "pubDate") or _get_text(item, "published") or datetime.now().isoformat()

                if not title:
                    continue

                content = _clean_html(f"{title} {desc or ''}")
                is_relevant = _is_election_relevant(content)

                articles.append(RSSArticle(
                    title=title,
                    source=feed["name"],
                    url=link or feed["url"],
                    content=content[:1000],
                    published=pubdate,
                    language=feed["language"],
                    tier=feed["tier"],
                    is_election_relevant=is_relevant,
                ))

            if articles:
                break  # Success — don't try fallback

        except Exception as e:
            print(f"    ↳ {feed['name']} fetch error: {e}")
            continue

    return articles


async def fetch_all_rss_feeds(
    tier_limit: int = 3,
    max_per_feed: int = 10,
) -> tuple[list[RSSArticle], dict]:
    """
    Fetch all RSS feeds concurrently.
    Returns (all_articles, stats_dict)
    """
    print(f"📡 Fetching {len(MALAYALAM_RSS_FEEDS)} Malayalam RSS feeds...")

    async with httpx.AsyncClient() as http:
        tasks = [
            fetch_rss_feed(feed, http)
            for feed in MALAYALAM_RSS_FEEDS
            if feed["tier"] <= tier_limit
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_articles = []
    stats = {"total": 0, "election_relevant": 0, "by_source": {}, "errors": 0}

    for feed, result in zip(MALAYALAM_RSS_FEEDS, results):
        if isinstance(result, Exception):
            stats["errors"] += 1
            continue
        articles = result[:max_per_feed]
        all_articles.extend(articles)
        relevant = sum(1 for a in articles if a.is_election_relevant)
        stats["by_source"][feed["name"]] = {
            "total":    len(articles),
            "relevant": relevant,
        }
        stats["total"]            += len(articles)
        stats["election_relevant"] += relevant

    # Sort: election-relevant first, then by tier
    all_articles.sort(key=lambda a: (not a.is_election_relevant, a.tier))

    print(f"  ↳ Fetched {stats['total']} articles "
          f"({stats['election_relevant']} election-relevant) "
          f"from {len(stats['by_source'])} sources")

    return all_articles, stats


# ════════════════════════════════════════════════════════════
# MALAYALAM → ENGLISH SUMMARIZER (GPT-4o)
# ════════════════════════════════════════════════════════════

SUMMARIZER_SYSTEM_PROMPT = """You are a political intelligence analyst for the Kerala 2026 Assembly Elections.
Your job is to analyze Malayalam news articles and extract election intelligence for the UDF War Room.

You receive article text that may be in Malayalam, English, or mixed (Manglish).
You must respond ONLY with valid JSON — no markdown, no backticks, no extra text."""

SUMMARIZER_USER_PROMPT = """Analyze this Kerala election news article and extract political intelligence.

SOURCE: {source}
LANGUAGE: {language}
CONTENT: {content}

CONTEXT: Kerala Assembly Elections April 9, 2026. UDF (Congress-led) vs LDF (CPI(M)-led) vs NDA (BJP-led).
Key issues: Inflation 9.49% (India #1), unemployment, Sabarimala gold scandal, corruption.
CM race: Pinarayi Vijayan (LDF) 27.85% vs VD Satheesan (UDF) 27.77%.

Return this exact JSON:
{{
  "title_english": "<translated/paraphrased title in English>",
  "summary_english": "<3-4 sentence English summary of the article's key political content>",
  "political_angle": "<'UDF' | 'LDF' | 'NDA' | 'NEUTRAL'> — which front does this favor?",
  "sentiment_score": <float -1.0 to +1.0 for the favored front>,
  "key_claims": ["<claim 1>", "<claim 2>", "<claim 3>"],
  "districts_mentioned": ["<district names if any>"],
  "electoral_impact": "<'HIGH' | 'MEDIUM' | 'LOW'>",
  "urgency": "<'BREAKING' | 'TODAY' | 'BACKGROUND'>",
  "war_room_note": "<1 sentence — what this means for UDF strategy specifically>"
}}"""


async def summarize_article(article: RSSArticle) -> SummarizedArticle | None:
    """Use GPT-4o to translate + summarize a Malayalam article."""
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o",
            max_tokens=600,
            temperature=0.1,
            messages=[
                {"role": "system", "content": SUMMARIZER_SYSTEM_PROMPT},
                {"role": "user", "content": SUMMARIZER_USER_PROMPT.format(
                    source=article.source,
                    language=article.language,
                    content=article.content[:800],
                )},
            ],
        )

        raw = resp.choices[0].message.content.strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)

        return SummarizedArticle(
            title_original=article.title,
            source=article.source,
            url=article.url,
            published=article.published,
            language=article.language,
            tier=article.tier,
            title_english=data.get("title_english", article.title),
            summary_english=data.get("summary_english", ""),
            political_angle=data.get("political_angle", "NEUTRAL"),
            sentiment_score=float(data.get("sentiment_score", 0)),
            key_claims=data.get("key_claims", []),
            districts_mentioned=data.get("districts_mentioned", []),
            electoral_impact=data.get("electoral_impact", "LOW"),
            urgency=data.get("urgency", "BACKGROUND"),
            summarized_at=datetime.now().isoformat(),
        )

    except Exception as e:
        print(f"    ↳ Summarize error [{article.source}]: {e}")
        return None


async def summarize_batch(
    articles: list[RSSArticle],
    max_articles: int = 30,
    only_relevant: bool = True,
) -> list[SummarizedArticle]:
    """
    Summarize a batch of articles concurrently.
    Filters to election-relevant only by default.
    """
    # Filter
    to_summarize = [
        a for a in articles
        if (not only_relevant or a.is_election_relevant)
    ][:max_articles]

    print(f"🧠 Summarizing {len(to_summarize)} election-relevant articles...")

    # Process in batches of 5 to avoid rate limits
    batch_size = 5
    all_summaries = []

    for i in range(0, len(to_summarize), batch_size):
        batch = to_summarize[i:i + batch_size]
        tasks = [summarize_article(a) for a in batch]
        results = await asyncio.gather(*tasks)
        summaries = [r for r in results if r is not None]
        all_summaries.extend(summaries)
        print(f"  ↳ Batch {i//batch_size + 1}: {len(summaries)}/{len(batch)} summarized")

        # Small delay between batches
        if i + batch_size < len(to_summarize):
            await asyncio.sleep(1)

    # Sort by urgency + impact
    urgency_order = {"BREAKING": 0, "TODAY": 1, "BACKGROUND": 2}
    impact_order  = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    all_summaries.sort(key=lambda s: (
        urgency_order.get(s.urgency, 3),
        impact_order.get(s.electoral_impact, 3),
    ))

    print(f"  ↳ Total summaries: {len(all_summaries)}")
    return all_summaries


# ════════════════════════════════════════════════════════════
# MAIN FUNCTION — for pipeline integration
# ════════════════════════════════════════════════════════════

async def fetch_and_summarize_rss(
    tier_limit: int = 2,
    max_summarize: int = 25,
) -> dict:
    """
    Main function called by the LangGraph pipeline.
    Returns structured data ready for pipeline state.
    """
    # Step 1: Fetch RSS
    articles, fetch_stats = await fetch_all_rss_feeds(tier_limit=tier_limit)

    # Step 2: Summarize
    summaries = await summarize_batch(
        articles,
        max_articles=max_summarize,
        only_relevant=True,
    )

    # Step 3: Save to file
    output = {
        "fetched_at":   datetime.now().isoformat(),
        "fetch_stats":  fetch_stats,
        "total_fetched": len(articles),
        "total_summarized": len(summaries),
        "summaries": [asdict(s) for s in summaries],
        "breaking_count": sum(1 for s in summaries if s.urgency == "BREAKING"),
        "high_impact_count": sum(1 for s in summaries if s.electoral_impact == "HIGH"),
        "by_angle": {
            "UDF":     [asdict(s) for s in summaries if s.political_angle == "UDF"],
            "LDF":     [asdict(s) for s in summaries if s.political_angle == "LDF"],
            "NDA":     [asdict(s) for s in summaries if s.political_angle == "NDA"],
            "NEUTRAL": [asdict(s) for s in summaries if s.political_angle == "NEUTRAL"],
        },
    }

    # Save to summaries/ folder
    date_str = datetime.now().strftime("%Y-%m-%d")
    out_path = SUMMARIES_DIR / f"malayalam_news_{date_str}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  ↳ Saved → {out_path}")
    return output


# ════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════

def _get_text(element: ET.Element, tag: str) -> str:
    """Safely extract text from XML element."""
    child = element.find(tag)
    if child is None:
        return ""
    return (child.text or "").strip()


def _clean_html(text: str) -> str:
    """Remove HTML tags from text."""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def _is_election_relevant(text: str) -> bool:
    """Check if article is election-relevant using keyword matching."""
    text_lower = text.lower()
    for kw in ELECTION_KEYWORDS_EN:
        if kw.lower() in text_lower:
            return True
    for kw in ELECTION_KEYWORDS_ML:
        if kw in text:
            return True
    return False


def _print_summary(s: SummarizedArticle):
    """Pretty-print a summary to terminal."""
    angle_color = {"UDF": "🔵", "LDF": "🔴", "NDA": "🟠", "NEUTRAL": "⚪"}.get(
        s.political_angle, "⚪"
    )
    urgency_icon = {"BREAKING": "🚨", "TODAY": "📰", "BACKGROUND": "📄"}.get(
        s.urgency, "📄"
    )
    impact_icon = {"HIGH": "🔥", "MEDIUM": "⚡", "LOW": "💤"}.get(
        s.electoral_impact, "💤"
    )

    print(f"\n{urgency_icon} {impact_icon} {angle_color} [{s.source}]")
    print(f"   {s.title_english}")
    print(f"   {s.summary_english[:200]}...")
    if s.key_claims:
        print(f"   Claims: {' | '.join(s.key_claims[:2])}")


# ════════════════════════════════════════════════════════════
# CLI ENTRYPOINT
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Kerala War Room — Malayalam RSS Ingestion & Summarizer"
    )
    parser.add_argument("--fetch",  action="store_true", help="Fetch + summarize RSS feeds")
    parser.add_argument("--show",   action="store_true", help="Show latest saved summaries")
    parser.add_argument("--tier",   type=int, default=2, help="Max feed tier (1=top, 3=all)")
    parser.add_argument("--max",    type=int, default=25, help="Max articles to summarize")
    args = parser.parse_args()

    if args.show:
        # Show latest saved summaries
        files = sorted(SUMMARIES_DIR.glob("malayalam_news_*.json"), reverse=True)
        if not files:
            print("No summaries found. Run with --fetch first.")
        else:
            with open(files[0], encoding="utf-8") as f:
                data = json.load(f)
            print(f"\n📰 LATEST MALAYALAM NEWS INTELLIGENCE")
            print(f"   Date: {data['fetched_at'][:10]}")
            print(f"   Total: {data['total_summarized']} summaries")
            print(f"   Breaking: {data['breaking_count']} | High Impact: {data['high_impact_count']}")
            for s_dict in data["summaries"][:10]:
                s = SummarizedArticle(**s_dict)
                _print_summary(s)

    else:
        # Default: fetch + summarize
        result = asyncio.run(fetch_and_summarize_rss(
            tier_limit=args.tier,
            max_summarize=args.max,
        ))
        print(f"\n✅ Done: {result['total_summarized']} articles summarized")
        print(f"   Breaking: {result['breaking_count']}")
        print(f"   High Impact: {result['high_impact_count']}")
        print(f"\n   UDF-favorable: {len(result['by_angle']['UDF'])}")
        print(f"   LDF-favorable: {len(result['by_angle']['LDF'])}")
        print(f"   NDA-favorable: {len(result['by_angle']['NDA'])}")
        print(f"   Neutral: {len(result['by_angle']['NEUTRAL'])}")
