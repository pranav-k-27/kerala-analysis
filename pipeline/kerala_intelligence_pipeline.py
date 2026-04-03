"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          KERALA 2026 WAR ROOM — LANGGRAPH INTELLIGENCE PIPELINE             ║
║          Daily Political Intelligence Automation System                     ║
║          Stack: LangGraph · Claude claude-sonnet-4 · Qdrant · FastAPI           ║
╚══════════════════════════════════════════════════════════════════════════════╝

PIPELINE ARCHITECTURE:
══════════════════════

  [SCHEDULER]
      │
      ▼
  ┌─────────────────────────────────────────────────────────┐
  │                   INGESTION LAYER                       │
  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
  │  │ News Scraper │ │ Social Media │ │  Field Input  │    │
  │  │ (Malayalam + │ │ Aggregator   │ │  (WhatsApp   │    │
  │  │  National)   │ │ (X/FB/YT)    │ │   Reports)   │    │
  │  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘    │
  └─────────┼────────────────┼────────────────┼────────────┘
            └────────────────┼────────────────┘
                             ▼
  ┌─────────────────────────────────────────────────────────┐
  │                    AI PROCESSING LAYER (LangGraph)      │
  │                                                         │
  │  StateGraph with these nodes:                           │
  │                                                         │
  │  sentiment_analyzer ──► topic_clusterer                 │
  │         │                     │                         │
  │         ▼                     ▼                         │
  │  constituency_scorer ──► swing_predictor                │
  │         │                     │                         │
  │         ▼                     ▼                         │
  │   risk_detector   ──►  action_recommender               │
  │                               │                         │
  │                               ▼                         │
  │                      report_generator                   │
  └──────────────────────────────┬──────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────┐
  │                    OUTPUT LAYER                         │
  │  • Daily War Report (PDF + JSON)                        │
  │  • Constituency Score Updates (Qdrant vector DB)        │
  │  • WhatsApp / Telegram Alerts (critical signals)        │
  │  • Dashboard API push (FastAPI endpoints)               │
  └─────────────────────────────────────────────────────────┘

USAGE:
  pip install langgraph langchain-anthropic qdrant-client
           playwright python-telegram-bot fastapi uvicorn
           beautifulsoup4 httpx pandas schedule

  export ANTHROPIC_API_KEY="your-key"
  python kerala_intelligence_pipeline.py --run-now
  python kerala_intelligence_pipeline.py --schedule daily
"""

# ─── IMPORTS ────────────────────────────────────────────────────────────────

import asyncio
import json
import logging
import os
from dataclasses import dataclass, asdict, field
from datetime import datetime, date
from typing import Annotated, Any, TypedDict
import operator

# LangGraph
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# LangChain / Claude
from langchain_openai import ChatOpenAI
from constituency_scorer import score_all_constituencies, DEFAULT_DISTRICT_SIGNALS
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from dotenv import load_dotenv
load_dotenv()

# Qdrant (vector store for constituency embeddings)
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("⚠️  Qdrant not installed. Vector store features disabled.")

# Web scraping
import httpx
from bs4 import BeautifulSoup

# Scheduling
import schedule
import time
import threading


# ─── LOGGING ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("WarRoom")


# ─── DOMAIN MODELS ──────────────────────────────────────────────────────────

@dataclass
class NewsItem:
    title: str
    source: str
    url: str
    content: str
    published: str
    language: str = "en"
    district: str | None = None

@dataclass
class SentimentReading:
    topic: str
    front: str          # UDF | LDF | NDA
    score: float        # -1.0 to +1.0
    volume: int
    platform: str
    district: str | None = None

@dataclass
class ConstituencyScore:
    name: str
    district: str
    udf_win_probability: float
    swing_direction: str
    risk_level: str
    key_issues: list[str]
    last_updated: str

@dataclass
class AlertMessage:
    severity: str       # CRITICAL | HIGH | MEDIUM | INFO
    title: str
    body: str
    district: str | None = None
    action_required: str | None = None


# ─── PIPELINE STATE ─────────────────────────────────────────────────────────

class PipelineState(TypedDict):
    """
    Shared state flowing through every LangGraph node.
    Each node reads what it needs and writes its outputs.
    """
    # Raw ingested data
    raw_news: list[dict]
    raw_social: list[dict]
    raw_field_reports: list[dict]

    # Processed signals
    sentiment_readings: Annotated[list[dict], operator.add]
    topic_clusters: list[dict]

    # Intelligence outputs
    constituency_scores: Annotated[list[dict], operator.add]
    swing_predictions: list[dict]
    risk_alerts: Annotated[list[dict], operator.add]
    action_recommendations: list[dict]

    # Final report
    daily_report: dict
    report_markdown: str

    # Pipeline metadata
    run_date: str
    run_id: str
    errors: Annotated[list[str], operator.add]


# ─── CONFIGURATION ──────────────────────────────────────────────────────────

KERALA_DISTRICTS = [
    "Thiruvananthapuram", "Kollam", "Pathanamthitta", "Alappuzha",
    "Kottayam", "Idukki", "Ernakulam", "Thrissur", "Palakkad",
    "Malappuram", "Kozhikode", "Wayanad", "Kannur", "Kasaragod"
]

SWING_SEATS = [
    "Thrissur", "Nemom", "Attingal", "Kazhakuttam", "Pala",
    "Chalakudy", "Irinjalakkuda", "Aranmula", "Kuthuparamba",
    "Beypore", "Palakkad", "Malampuzha", "Kayamkulam"
]

NEWS_SOURCES = [
    {"name": "Mathrubhumi",  "url": "https://www.mathrubhumi.com/elections/2026",     "lang": "ml"},
    {"name": "Manorama",     "url": "https://www.onmanorama.com/news/kerala.html",     "lang": "ml"},
    {"name": "The Hindu KL", "url": "https://www.thehindu.com/elections/kerala/",      "lang": "en"},
    {"name": "Deccan Herald","url": "https://www.deccanherald.com/tag/kerala-elections","lang": "en"},
    {"name": "National Herald","url":"https://www.nationalheraldindia.com/politics",   "lang": "en"},
]

KEYWORDS = [
    "UDF", "LDF", "BJP", "Congress", "CPI(M)", "Pinarayi", "Satheesan",
    "Kerala election", "Kerala Assembly", "inflation Kerala", "unemployment Kerala",
    "Sabarimala", "corruption Kerala", "NDA Kerala", "swing seat",
]


# ─── LLM CLIENT ─────────────────────────────────────────────────────────────

def get_llm(temperature: float = 0.1) -> ChatOpenAI:
    """Return a configured Claude claude-sonnet-4 client."""
    return ChatOpenAI(
        model="gpt-4o",
        temperature=temperature,
        max_tokens=2048,
        api_key=os.getenv("OPENAI_API_KEY"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# NODE 1: DATA INGESTION — Scrape news + social media
# ══════════════════════════════════════════════════════════════════════════════

async def ingest_news(state: PipelineState) -> dict:
    """
    Scrapes Malayalam and English news sources for Kerala election coverage.
    In production: use Playwright for JS-rendered pages, rate limiting, proxies.
    """
    log.info("📡 [NODE 1] Ingesting news sources...")
    articles = []

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        for source in NEWS_SOURCES:
            try:
                resp = await client.get(source["url"],
                    headers={"User-Agent": "Mozilla/5.0 (compatible; WarRoomBot/1.0)"})
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")

                # Extract headlines + snippets
                # Real implementation: customize per site's HTML structure
                for tag in soup.find_all(["h2", "h3", "article"], limit=20):
                    text = tag.get_text(strip=True)
                    if any(kw.lower() in text.lower() for kw in KEYWORDS) and len(text) > 40:
                        articles.append({
                            "title":     text[:200],
                            "source":    source["name"],
                            "url":       source["url"],
                            "content":   text,
                            "published": datetime.now().isoformat(),
                            "language":  source["lang"],
                            "district":  _detect_district(text),
                        })
            except Exception as e:
                log.warning(f"  ↳ Failed to scrape {source['name']}: {e}")
                state["errors"].append(f"Scrape error [{source['name']}]: {str(e)}")

    log.info(f"  ↳ Collected {len(articles)} articles")

    # ── MOCK DATA (used when scraping is blocked / for demo) ──────────────────
    if not articles:
        log.info("  ↳ Using mock data for demonstration")
        articles = _get_mock_news()

    return {"raw_news": articles}


async def ingest_social_media(state: PipelineState) -> dict:
    """
    Pulls social media data.
    Production: Twitter/X API v2, Facebook Graph API, YouTube Data API.
    """
    log.info("📱 [NODE 1b] Ingesting social media signals...")

    # In production, use actual API clients here.
    # Example structure for X (Twitter) API v2:
    #
    # from tweepy import StreamingClient, StreamRule
    # client = tweepy.Client(bearer_token=os.getenv("TWITTER_BEARER"))
    # response = client.search_recent_tweets(
    #     query='("Kerala election" OR "UDF" OR "LDF") -is:retweet lang:en',
    #     max_results=100,
    #     tweet_fields=["created_at","public_metrics","geo"]
    # )

    # Using mock data for the pipeline demonstration:
    social_data = _get_mock_social_data()
    log.info(f"  ↳ Collected {len(social_data)} social signals")
    return {"raw_social": social_data}


async def ingest_field_reports(state: PipelineState) -> dict:
    """
    Processes field reports from ground workers.
    Production: WhatsApp Business API / Telegram Bot / Google Forms webhook.
    
    Field workers submit structured reports:
    - Constituency name
    - Booth-level observation
    - Issues raised by voters
    - Opposition activity
    - Confidence score
    """
    log.info("🗺️  [NODE 1c] Processing field reports...")
    reports = _get_mock_field_reports()
    log.info(f"  ↳ Processed {len(reports)} field reports")
    return {"raw_field_reports": reports}


# ══════════════════════════════════════════════════════════════════════════════
# NODE 2: SENTIMENT ANALYSIS — Malayalam + English NLP
# ══════════════════════════════════════════════════════════════════════════════

async def analyze_sentiment(state: PipelineState) -> dict:
    """
    Uses Claude to perform sentiment analysis on all ingested content.
    Produces per-front, per-district sentiment scores.
    
    Why Claude instead of traditional NLP:
    - Malayalam text support (crucial for ground-level content)
    - Understands political context (e.g., "Sabarimala gold theft" → negative for LDF)
    - Can extract nuanced sentiment that VADER/TextBlob miss
    """
    log.info("🧠 [NODE 2] Running sentiment analysis...")
    llm = get_llm(temperature=0.1)

    all_content = state["raw_news"] + state["raw_social"] + state["raw_field_reports"]

    SENTIMENT_PROMPT = """You are a political sentiment analysis engine for Kerala elections 2026.

Analyze the following news/social media items and return ONLY a JSON array.
Each item must have:
- topic: string (what this is about)
- front: "UDF" | "LDF" | "NDA" | "NEUTRAL"
- score: float (-1.0 very negative to +1.0 very positive)  
- volume: integer (estimated reach/importance 1-100)
- platform: string
- district: string or null
- key_signal: string (1 line — what makes this significant)

Focus on signals that affect electoral outcomes.
Items to analyze:

{content}

Return ONLY the JSON array. No preamble, no markdown."""

    # Process in batches of 10 for efficiency
    batch_size = 10
    all_sentiments = []

    for i in range(0, min(len(all_content), 50), batch_size):
        batch = all_content[i:i+batch_size]
        content_str = "\n---\n".join([
            f"[{j+1}] SOURCE: {item.get('source','unknown')} | "
            f"DISTRICT: {item.get('district','unknown')}\n"
            f"TEXT: {item.get('title', item.get('content',''))[:300]}"
            for j, item in enumerate(batch)
        ])
        try:
            resp = await llm.ainvoke([
                SystemMessage(content="You are a precise political data analyst. Return only valid JSON arrays."),
                HumanMessage(content=SENTIMENT_PROMPT.format(content=content_str))
            ])
            raw = resp.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            batch_sentiments = json.loads(raw)
            all_sentiments.extend(batch_sentiments)
        except Exception as e:
            log.warning(f"  ↳ Sentiment batch {i//batch_size+1} failed: {e}")
            state["errors"].append(f"Sentiment error (batch {i//batch_size+1}): {str(e)}")

    # Fall back to mock if no results
    if not all_sentiments:
        all_sentiments = _get_mock_sentiments()

    log.info(f"  ↳ Generated {len(all_sentiments)} sentiment readings")
    return {"sentiment_readings": all_sentiments}


# ══════════════════════════════════════════════════════════════════════════════
# NODE 3: TOPIC CLUSTERING — What narratives are rising?
# ══════════════════════════════════════════════════════════════════════════════

async def cluster_topics(state: PipelineState) -> dict:
    """
    Groups content into narrative clusters to detect trending issues.
    Outputs a ranked list of narratives with momentum scores.
    """
    log.info("🗂️  [NODE 3] Clustering topics and detecting narratives...")
    llm = get_llm(temperature=0.2)

    if not state["raw_news"]:
        return {"topic_clusters": []}

    sample_titles = [item.get("title","") for item in state["raw_news"][:40]]

    CLUSTER_PROMPT = """You are a political narrative analyst for Kerala elections 2026.
    
Given these {n} news headlines from today, identify the TOP 8 narrative clusters.

Headlines:
{headlines}

For each cluster return JSON with:
- cluster_id: "C1" through "C8"
- theme: string (short label)
- narrative: string (1-2 sentences — what story this tells voters)
- front_benefiting: "UDF" | "LDF" | "NDA" | "NEUTRAL"
- momentum: "RISING" | "STABLE" | "FALLING"
- sentiment_score: float (-1 to +1)
- affected_districts: list of Kerala districts
- electoral_impact: "HIGH" | "MEDIUM" | "LOW"
- headlines_count: integer

Return ONLY a JSON array. No preamble."""

    try:
        resp = await llm.ainvoke([
            SystemMessage(content="Return only valid JSON. No extra text."),
            HumanMessage(content=CLUSTER_PROMPT.format(
                n=len(sample_titles),
                headlines="\n".join([f"  {i+1}. {t}" for i, t in enumerate(sample_titles)])
            ))
        ])
        raw = resp.content.strip().lstrip("```json").rstrip("```").strip()
        clusters = json.loads(raw)
    except Exception as e:
        log.warning(f"  ↳ Topic clustering failed: {e}")
        clusters = _get_mock_clusters()

    log.info(f"  ↳ Identified {len(clusters)} narrative clusters")
    return {"topic_clusters": clusters}


# ══════════════════════════════════════════════════════════════════════════════
# NODE 4: CONSTITUENCY SCORER — Update seat-level intelligence
# ══════════════════════════════════════════════════════════════════════════════

async def score_constituencies(state: PipelineState) -> dict:
    """
    Scores ALL 140 constituencies using GPT-4o + 2021 base results
    + district-level sentiment signals from today's news pipeline.
    """
    log.info("🎯 [NODE 4] Scoring ALL 140 constituencies...")

    # Build district signals from today's sentiment readings
    dist_sentiment = {}
    for s in state["sentiment_readings"]:
        d = s.get("district")
        if not d:
            continue
        if d not in dist_sentiment:
            dist_sentiment[d] = {"udf": [], "ldf": [], "nda": []}
        front = s.get("front", "NEUTRAL").lower()
        if front in dist_sentiment[d]:
            dist_sentiment[d][front].append(s.get("score", 0))

    # Convert raw sentiment to 0-10 signal scores
    def avg(lst): return sum(lst)/len(lst) if lst else 0.0
    def to_signal(v): return min(10, max(0, int((v + 1) * 5)))

    district_signals = {}
    for dist, data in dist_sentiment.items():
        udf_sent = avg(data.get("udf", [0]))
        ldf_sent = avg(data.get("ldf", [0]))
        district_signals[dist] = {
            "anti_inc":    to_signal(-ldf_sent),
            "inflation":   7,
            "nda_surge":   3,
            "udf_momentum":to_signal(udf_sent),
        }

    # Fill missing districts with defaults
    for dist, defaults in DEFAULT_DISTRICT_SIGNALS.items():
        if dist not in district_signals:
            district_signals[dist] = defaults

    # Score all 140 seats
    try:
        scores = await score_all_constituencies(
            district_signals,
            field_reports=state.get("raw_field_reports", [])
        )
        log.info(f"  ↳ Scored {len(scores)} constituencies")
    except Exception as e:
        log.warning(f"  ↳ Full scoring failed: {e} — using mock data")
        scores = _get_mock_constituency_scores()

    return {"constituency_scores": scores}


# ══════════════════════════════════════════════════════════════════════════════
# NODE 5: SWING PREDICTOR — Identify seats moving today
# ══════════════════════════════════════════════════════════════════════════════

async def predict_swings(state: PipelineState) -> dict:
    """
    Identifies which seats have seen meaningful movement today and why.
    Generates a swing watchlist for the war room.
    """
    log.info("📈 [NODE 5] Running swing prediction...")
    llm = get_llm(temperature=0.2)

    SWING_PROMPT = f"""You are the swing prediction engine for Kerala 2026 elections.

CURRENT INTELLIGENCE:
Constituency scores: {json.dumps(state['constituency_scores'][:5], indent=2)}
Topic clusters: {json.dumps([c.get('theme','') + ': ' + c.get('narrative','') for c in state['topic_clusters'][:5]], indent=2)}
Total sentiment readings: {len(state['sentiment_readings'])}

MACRO CONTEXT:
- 10 days to polling (April 9, 2026)
- UDF holds momentum from local body sweep (43% vs LDF 40%)
- NDA is structural spoiler in 12 seats
- Inflation narrative accelerating (9.49% — India #1)

Produce a JSON with:
- seats_moving_toward_udf: list of seat names
- seats_moving_toward_ldf: list of seat names
- seats_at_risk_nda_spoil: list of seat names
- overall_momentum: "UDF_SURGING" | "UDF_LEADING" | "NECK_AND_NECK" | "LDF_RECOVERING"
- confidence_in_udf_majority: integer 0-100
- seats_likely_udf: integer
- seats_likely_ldf: integer
- seats_likely_nda: integer
- swing_summary: string (2-3 sentences for the war room briefing)
- critical_actions_today: list of 3 strings (what UDF must do TODAY)

Return ONLY the JSON object."""

    try:
        resp = await llm.ainvoke([
            SystemMessage(content="Return only valid JSON. No preamble."),
            HumanMessage(content=SWING_PROMPT)
        ])
        raw = resp.content.strip().lstrip("```json").rstrip("```").strip()
        predictions = json.loads(raw)
    except Exception as e:
        log.warning(f"  ↳ Swing prediction failed: {e}")
        predictions = _get_mock_swing_predictions()

    log.info(f"  ↳ Swing prediction: {predictions.get('overall_momentum', 'unknown')}")
    return {"swing_predictions": predictions}


# ══════════════════════════════════════════════════════════════════════════════
# NODE 6: RISK DETECTOR — What threats need immediate action?
# ══════════════════════════════════════════════════════════════════════════════

async def detect_risks(state: PipelineState) -> dict:
    """
    Scans all signals for emerging threats to UDF performance.
    Generates CRITICAL alerts for immediate war-room action.
    """
    log.info("⚠️  [NODE 6] Running risk detection...")
    llm = get_llm(temperature=0.1)

    RISK_PROMPT = f"""You are the risk intelligence officer for UDF's Kerala 2026 war room.

Scan today's intelligence for THREATS to UDF:

NEWS SIGNALS: {json.dumps([n.get('title','') for n in state['raw_news'][:20]], indent=2)}
SOCIAL SIGNALS: {json.dumps([s.get('content','') for s in state['raw_social'][:10] if s.get('content')], indent=2)}
FIELD REPORTS: {json.dumps(state['raw_field_reports'][:5], indent=2)}
SENTIMENT TRENDS: UDF avg: {_avg_sentiment(state['sentiment_readings'],'UDF'):.2f}, LDF avg: {_avg_sentiment(state['sentiment_readings'],'LDF'):.2f}

KNOWN VULNERABILITIES:
- NDA spoiler in 12 swing seats
- Congress internal factionalism risk
- LDF's last-minute populist budget scheme launches
- Ezhava vote drift to BJP in South Kerala
- Voter turnout suppression risk (UDF voters assuming victory)

Identify TOP 5 risks. Return a JSON array where each risk has:
- risk_id: "R1" through "R5"
- severity: "CRITICAL" | "HIGH" | "MEDIUM"
- title: string (short alert title)
- description: string (what is happening and why it's a risk)
- affected_seats: list of constituency names
- counter_action: string (what UDF must do to neutralize)
- time_sensitivity: "IMMEDIATE" | "24H" | "48H" | "WEEK"

Return ONLY the JSON array."""

    try:
        resp = await llm.ainvoke([
            SystemMessage(content="Return only valid JSON arrays. No extra text."),
            HumanMessage(content=RISK_PROMPT)
        ])
        raw = resp.content.strip().lstrip("```json").rstrip("```").strip()
        risks = json.loads(raw)
    except Exception as e:
        log.warning(f"  ↳ Risk detection failed: {e}")
        risks = _get_mock_risks()

    critical_count = sum(1 for r in risks if r.get("severity") == "CRITICAL")
    log.info(f"  ↳ Detected {len(risks)} risks ({critical_count} CRITICAL)")
    return {"risk_alerts": risks}


# ══════════════════════════════════════════════════════════════════════════════
# NODE 7: ACTION RECOMMENDER — Generate today's tactical playbook
# ══════════════════════════════════════════════════════════════════════════════

async def recommend_actions(state: PipelineState) -> dict:
    """
    Synthesizes all intelligence into concrete daily actions for:
    - Leadership (Satheesan, Chennithala, Rahul Gandhi)
    - Campaign managers (district-level)
    - Ground workers (booth-level)
    - Digital team (social media response)
    """
    log.info("🎯 [NODE 7] Generating action recommendations...")
    llm = get_llm(temperature=0.3)

    ACTION_PROMPT = f"""You are the chief strategist for UDF's Kerala 2026 election campaign.
Today is {date.today().strftime('%B %d, %Y')}.

INTELLIGENCE BRIEFING:
- Overall momentum: {state['swing_predictions'].get('overall_momentum', 'UDF_LEADING')}
- UDF majority confidence: {state['swing_predictions'].get('confidence_in_udf_majority', 72)}%
- Seats moving toward UDF: {state['swing_predictions'].get('seats_moving_toward_udf', [])}
- Critical risks: {[r.get('title') for r in state['risk_alerts'] if r.get('severity')=='CRITICAL']}
- Top rising narrative: {state['topic_clusters'][0].get('theme','') if state['topic_clusters'] else 'Inflation'}

Produce TODAY'S TACTICAL PLAYBOOK as a JSON object with:
{{
  "date": "{date.today().isoformat()}",
  "priority_message_of_day": string,
  "leadership_actions": {{
    "satheesan": list of 2 specific actions,
    "rahul_gandhi": list of 1 specific action,
    "district_presidents": list of 2 instructions
  }},
  "digital_actions": {{
    "trending_hashtags": list of 3,
    "content_themes": list of 3,
    "platform_focus": list of 2 platforms with rationale
  }},
  "ground_actions": {{
    "priority_constituencies": list of 5 seats,
    "booth_instructions": list of 3 bullet points,
    "voter_outreach_focus": string
  }},
  "alliance_management": list of 2 items,
  "counter_narrative": string (how to respond to LDF's strongest message today),
  "do_not_do": list of 2 things UDF should avoid doing today
}}

Return ONLY the JSON object."""

    try:
        resp = await llm.ainvoke([
            SystemMessage(content="Return only valid JSON. No preamble or markdown."),
            HumanMessage(content=ACTION_PROMPT)
        ])
        raw = resp.content.strip().lstrip("```json").rstrip("```").strip()
        actions = json.loads(raw)
    except Exception as e:
        log.warning(f"  ↳ Action recommendation failed: {e}")
        actions = _get_mock_actions()

    log.info("  ↳ Action playbook generated")
    return {"action_recommendations": actions}


# ══════════════════════════════════════════════════════════════════════════════
# NODE 8: REPORT GENERATOR — Daily War Room Briefing
# ══════════════════════════════════════════════════════════════════════════════

async def generate_report(state: PipelineState) -> dict:
    """
    Generates the final Daily War Room Briefing document.
    Output: structured JSON + human-readable Markdown.
    Dispatched to: Leadership WhatsApp, Dashboard API, PDF archive.
    """
    log.info("📋 [NODE 8] Generating Daily War Room Report...")

    # ── Compute seat projection from AI-scored constituencies ──
    # This is the ground truth — NOT from swing_predictions GPT call
    scores = state.get("constituency_scores", [])
    seat_projection = {
        "udf":             sum(1 for s in scores if s.get("lean") == "UDF"),
        "ldf":             sum(1 for s in scores if s.get("lean") == "LDF"),
        "nda":             sum(1 for s in scores if s.get("lean") == "NDA"),
        "swing":           sum(1 for s in scores if s.get("lean") == "SWING"),
        "majority_needed": 71,
        "total":           len(scores),
        "source":          f"AI-scored {len(scores)} constituencies (v3)",
    }

    # ── Additional stats from scores ──
    critical_seats = [s["name"] for s in scores if s.get("risk") == "CRITICAL"]
    high_risk_seats = [s["name"] for s in scores if s.get("risk") == "HIGH"]
    nda_spoiler_seats = [
        s["name"] for s in scores
        if s.get("nda", 0) > 20 and s.get("lean") in ("SWING", "UDF", "LDF")
    ]
    avg_udf_win_prob = round(
        sum(s.get("win_prob_udf", 0) for s in scores) / max(len(scores), 1), 1
    )

    report_data = {
        "run_id":          state["run_id"],
        "date":            state["run_date"],
        "generated_at":    datetime.now().isoformat(),
        "overall_status":  state["swing_predictions"].get("overall_momentum", "UDF_LEADING"),

        # ✅ FIX: use AI-scored seat_projection, NOT swing_predictions
        "seat_projection": seat_projection,

        # Keep swing_predictions data separately for reference
        "swing_model_estimate": {
            "udf": state["swing_predictions"].get("seats_likely_udf", 80),
            "ldf": state["swing_predictions"].get("seats_likely_ldf", 54),
            "nda": state["swing_predictions"].get("seats_likely_nda",  6),
        },

        "majority_confidence":  state["swing_predictions"].get("confidence_in_udf_majority", 72),
        "avg_udf_win_prob":     avg_udf_win_prob,
        "critical_seats":       critical_seats,
        "high_risk_seats":      high_risk_seats,
        "nda_spoiler_seats":    nda_spoiler_seats,
        "top_risks":            state["risk_alerts"][:3],
        "constituency_scores":  state["constituency_scores"],
        "topic_clusters":       state["topic_clusters"][:5],
        "action_playbook":      state["action_recommendations"],
        "swing_summary":        state["swing_predictions"].get("swing_summary", ""),
        "pipeline_errors":      state["errors"],
    }

    # ── Generate human-readable markdown brief ──
    swings_toward_udf = state["swing_predictions"].get("seats_moving_toward_udf", [])
    risks_md = "\n".join([
        f"  {'🔴' if r.get('severity')=='CRITICAL' else '🟡'} **{r.get('title','')}** "
        f"[{r.get('severity','')}] → {r.get('counter_action','')}"
        for r in state["risk_alerts"][:5]
    ])
    clusters_md = "\n".join([
        f"  {i+1}. **{c.get('theme','')}** [{c.get('front_benefiting','')}] "
        f"↗ {c.get('momentum','')} — {c.get('narrative','')[:80]}..."
        for i, c in enumerate(state["topic_clusters"][:5])
    ])
    actions = state["action_recommendations"]

    # Seat breakdown string for markdown
    proj = seat_projection
    seat_str = (
        f"UDF: **{proj['udf']}** | LDF: {proj['ldf']} | "
        f"NDA: {proj['nda']} | SWING: {proj['swing']}"
    )
    majority_status = (
        "✅ MAJORITY LIKELY" if proj["udf"] >= 71
        else f"⚠️ {71 - proj['udf']} SHORT OF MAJORITY — swing seats critical"
    )

    md = f"""
# 🗳️ KERALA WAR ROOM — DAILY INTELLIGENCE BRIEF
**Date:** {state['run_date']}  |  **Run ID:** {state['run_id']}  |  **Generated:** {datetime.now().strftime('%H:%M IST')}

---

## 📊 HEADLINE SCORECARD

| Metric | Value |
|--------|-------|
| UDF Seat Projection | **{proj['udf']}** seats |
| LDF Seat Projection | {proj['ldf']} seats |
| NDA Projection | {proj['nda']} seats |
| SWING Seats | {proj['swing']} seats |
| Majority Status | {majority_status} |
| Overall Momentum | **{report_data['overall_status']}** |
| UDF Avg Win Probability | **{avg_udf_win_prob}%** |
| UDF Majority Confidence | **{report_data['majority_confidence']}%** |
| Days to Polling | **{(date(2026,4,9)-date.today()).days}** |

**Seat breakdown:** {seat_str}
**Source:** {proj['source']}

---

## 🔥 NARRATIVE LANDSCAPE (Top 5 Clusters Today)

{clusters_md}

---

## ⚠️  RISK ALERTS

{risks_md}

---

## 📍 CRITICAL & HIGH RISK SEATS

**CRITICAL ({len(critical_seats)} seats):** {', '.join(critical_seats) if critical_seats else 'None'}
**HIGH RISK ({len(high_risk_seats)} seats):** {', '.join(high_risk_seats[:10]) if high_risk_seats else 'None'}
**NDA Spoiler Risk ({len(nda_spoiler_seats)} seats):** {', '.join(nda_spoiler_seats[:8]) if nda_spoiler_seats else 'None'}

---

## 📈 SWING INTELLIGENCE

**Seats Moving Toward UDF:** {', '.join(swings_toward_udf) if swings_toward_udf else 'Stable'}
**Seats at NDA Spoil Risk:** {', '.join(state['swing_predictions'].get('seats_at_risk_nda_spoil', []))}

{state['swing_predictions'].get('swing_summary', '')}

---

## 🎯 TODAY'S TACTICAL PLAYBOOK

**Priority Message of Day:** {actions.get('priority_message_of_day', 'N/A')}

### Leadership Actions
{chr(10).join(['- ' + a for a in (actions.get('leadership_actions', {}).get('satheesan', []) + actions.get('leadership_actions', {}).get('district_presidents', []))])}

### Digital Actions
- Trending: {', '.join(actions.get('digital_actions', {}).get('trending_hashtags', []))}
- Content themes: {', '.join(actions.get('digital_actions', {}).get('content_themes', []))}

### Ground Priority Seats
{', '.join(actions.get('ground_actions', {}).get('priority_constituencies', []))}

### Counter-Narrative
> {actions.get('counter_narrative', 'N/A')}

---
*Generated by Kerala 2026 War Room AI Pipeline | LangGraph + Claude claude-sonnet-4*
*Sources: {len(state['raw_news'])} news articles | {len(state['raw_social'])} social signals | {len(state['raw_field_reports'])} field reports*
"""

    log.info("  ↳ Daily War Report generated ✅")
    return {"daily_report": report_data, "report_markdown": md}


# ══════════════════════════════════════════════════════════════════════════════
# VECTOR STORE: Store constituency embeddings in Qdrant
# ══════════════════════════════════════════════════════════════════════════════

class ConstituencyVectorStore:
    """
    Stores constituency intelligence as semantic embeddings in Qdrant.
    Enables similarity search: "find seats with similar risk profile to Thrissur"
    """
    COLLECTION = "kerala_constituencies"

    def __init__(self, host: str = "localhost", port: int = 6333):
        if not QDRANT_AVAILABLE:
            self.client = None
            return
        try:
            self.client = QdrantClient(host=host, port=port)
            self._ensure_collection()
        except Exception as e:
            log.warning(f"Qdrant connection failed: {e}. Vector store disabled.")
            self.client = None

    def _ensure_collection(self):
        cols = [c.name for c in self.client.get_collections().collections]
        if self.COLLECTION not in cols:
            self.client.create_collection(
                collection_name=self.COLLECTION,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
            log.info(f"  ↳ Created Qdrant collection: {self.COLLECTION}")

    async def upsert_constituency(self, score: dict, llm: ChatOpenAI):
        """Embed constituency profile and store in Qdrant for similarity search."""
        if not self.client:
            return
        # In production: use text-embedding-3-small or equivalent
        # For now, we use a placeholder approach
        text = f"{score['constituency']} {score.get('key_issues',[])} {score.get('swing_direction','')}"
        log.debug(f"  ↳ Would embed: {text[:80]}...")

    def find_similar_seats(self, seat_name: str, top_k: int = 5) -> list[dict]:
        """Find constituencies with similar political risk profiles."""
        if not self.client:
            return []
        # Production: embed query and search
        return []


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE ORCHESTRATOR — LangGraph StateGraph
# ══════════════════════════════════════════════════════════════════════════════

def build_pipeline() -> StateGraph:
    """
    Constructs the LangGraph StateGraph with all 8 nodes.
    
    Graph flow:
    
    ingest_news ─────────────────────────────────────────┐
    ingest_social ────────────────────────────────────────┤→ analyze_sentiment
    ingest_field_reports ─────────────────────────────────┘        │
                                                                    ▼
                                                           cluster_topics
                                                                    │
                                                                    ▼
                                                         score_constituencies
                                                                    │
                                                                    ▼
                                                           predict_swings
                                                                    │
                                                           ┌────────┴────────┐
                                                           ▼                 ▼
                                                      detect_risks   recommend_actions
                                                           │                 │
                                                           └────────┬────────┘
                                                                    ▼
                                                           generate_report
                                                                    │
                                                                   END
    """
    graph = StateGraph(PipelineState)

    # Add all nodes
    graph.add_node("ingest_news",         ingest_news)
    graph.add_node("ingest_social",       ingest_social_media)
    graph.add_node("ingest_field",        ingest_field_reports)
    graph.add_node("analyze_sentiment",   analyze_sentiment)
    graph.add_node("cluster_topics",      cluster_topics)
    graph.add_node("score_constituencies",score_constituencies)
    graph.add_node("predict_swings",      predict_swings)
    graph.add_node("detect_risks",        detect_risks)
    graph.add_node("recommend_actions",   recommend_actions)
    graph.add_node("generate_report",     generate_report)

    # Define flow
    graph.set_entry_point("ingest_news")
    graph.add_edge("ingest_news",         "ingest_social")
    graph.add_edge("ingest_social",       "ingest_field")
    graph.add_edge("ingest_field",        "analyze_sentiment")
    graph.add_edge("analyze_sentiment",   "cluster_topics")
    graph.add_edge("cluster_topics",      "score_constituencies")
    graph.add_edge("score_constituencies","predict_swings")
    graph.add_edge("predict_swings",      "detect_risks")
    graph.add_edge("detect_risks",        "recommend_actions")
    graph.add_edge("recommend_actions",   "generate_report")
    graph.add_edge("generate_report",     END)

    return graph.compile(checkpointer=MemorySaver())


# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT DISPATCHERS — WhatsApp, Dashboard API, Archive
# ══════════════════════════════════════════════════════════════════════════════

class OutputDispatcher:
    """Dispatches the daily report to multiple channels."""

    @staticmethod
    async def send_telegram_alert(report: dict, token: str, chat_id: str):
        """Send critical alerts via Telegram Bot."""
        # pip install python-telegram-bot
        # from telegram import Bot
        # bot = Bot(token=token)
        # await bot.send_message(chat_id=chat_id, text=summary, parse_mode='Markdown')
        log.info("  ↳ [Dispatcher] Telegram alert queued")

    @staticmethod
    async def push_to_dashboard(report: dict, api_url: str):
        """Push updated scores to the React war room dashboard via FastAPI."""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{api_url}/api/warroom/update",
                    json=report,
                    timeout=10
                )
            log.info("  ↳ [Dispatcher] Dashboard updated")
        except Exception as e:
            log.warning(f"  ↳ [Dispatcher] Dashboard push failed: {e}")

    @staticmethod
    def save_to_archive(report: dict, markdown: str, output_dir: str = "reports"):
        """Archive report as JSON + Markdown."""
        os.makedirs(output_dir, exist_ok=True)
        date_str = date.today().isoformat()
        run_id = report.get("run_id", "unknown")

        json_path = f"{output_dir}/report_{date_str}_{run_id}.json"
        md_path   = f"{output_dir}/brief_{date_str}_{run_id}.md"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        log.info(f"  ↳ [Dispatcher] Saved → {json_path}")
        log.info(f"  ↳ [Dispatcher] Saved → {md_path}")
        return md_path


# ══════════════════════════════════════════════════════════════════════════════
# MAIN RUNNER
# ══════════════════════════════════════════════════════════════════════════════

async def run_pipeline(run_id: str | None = None) -> dict:
    """
    Execute the full intelligence pipeline.
    Returns the final state including the daily report.
    """
    import uuid
    run_id = run_id or str(uuid.uuid4())[:8].upper()
    log.info(f"\n{'═'*60}")
    log.info(f"  🚀 KERALA WAR ROOM PIPELINE — RUN {run_id}")
    log.info(f"  📅 {datetime.now().strftime('%A, %B %d %Y %H:%M IST')}")
    log.info(f"{'═'*60}\n")

    pipeline = build_pipeline()
    vector_store = ConstituencyVectorStore()

    # Initial state
    initial_state: PipelineState = {
        "raw_news":             [],
        "raw_social":           [],
        "raw_field_reports":    [],
        "sentiment_readings":   [],
        "topic_clusters":       [],
        "constituency_scores":  [],
        "swing_predictions":    {},
        "risk_alerts":          [],
        "action_recommendations": {},
        "daily_report":         {},
        "report_markdown":      "",
        "run_date":             date.today().isoformat(),
        "run_id":               run_id,
        "errors":               [],
    }

    config = {"configurable": {"thread_id": run_id}}

    try:
        start = time.time()
        final_state = await pipeline.ainvoke(initial_state, config=config)
        elapsed = time.time() - start

        log.info(f"\n{'═'*60}")
        log.info(f"  ✅ PIPELINE COMPLETE in {elapsed:.1f}s")
        log.info(f"  📊 Articles processed: {len(final_state['raw_news'])}")
        log.info(f"  🎯 Constituencies scored: {len(final_state['constituency_scores'])}")
        log.info(f"  ⚠️  Risks detected: {len(final_state['risk_alerts'])}")
        log.info(f"  🗺️  Momentum: {final_state['swing_predictions'].get('overall_momentum','?')}")
        log.info(f"{'═'*60}\n")

        # Dispatch outputs
        dispatcher = OutputDispatcher()
        md_path = dispatcher.save_to_archive(
            final_state["daily_report"],
            final_state["report_markdown"]
        )

        # Print markdown brief to console
        print("\n" + "="*60)
        print(final_state["report_markdown"])
        print("="*60)

        return final_state

    except Exception as e:
        log.error(f"Pipeline failed: {e}", exc_info=True)
        raise


def schedule_daily_run(time_str: str = "06:00"):
    """
    Schedule the pipeline to run every day at a fixed time.
    Usage: schedule_daily_run("06:00")  # Run at 6am IST
    """
    log.info(f"📅 Scheduling daily pipeline at {time_str} IST")
    schedule.every().day.at(time_str).do(
        lambda: asyncio.run(run_pipeline())
    )
    while True:
        schedule.run_pending()
        time.sleep(60)


# ──────────────────────────── MOCK DATA HELPERS ──────────────────────────────

def _detect_district(text: str) -> str | None:
    for d in KERALA_DISTRICTS:
        if d.lower() in text.lower():
            return d
    return None

def _get_district_for_seat(seat: str) -> str:
    mapping = {
        "Thrissur": "Thrissur",   "Nemom": "Thiruvananthapuram",
        "Attingal": "Thiruvananthapuram", "Kazhakuttam": "Thiruvananthapuram",
        "Pala": "Kottayam",       "Chalakudy": "Thrissur",
        "Irinjalakkuda": "Thrissur", "Aranmula": "Pathanamthitta",
        "Kuthuparamba": "Kannur", "Beypore": "Kozhikode",
        "Palakkad": "Palakkad",   "Malampuzha": "Palakkad",
        "Kayamkulam": "Alappuzha",
    }
    return mapping.get(seat, "Unknown")

def _avg_sentiment(readings: list, front: str) -> float:
    scores = [r.get("score", 0) for r in readings if r.get("front","").upper() == front.upper()]
    return sum(scores) / len(scores) if scores else 0.0

def _get_mock_news() -> list[dict]:
    return [
        {"title": "Kerala inflation hits 9.49% — highest in India for 7th month running", "source": "The Hindu", "url": "#", "content": "Kerala records the highest retail inflation in India...", "published": datetime.now().isoformat(), "language": "en", "district": "Thiruvananthapuram"},
        {"title": "UDF's Puthuyuga Yathra draws massive crowds in Thrissur district", "source": "Manorama", "url": "#", "content": "V.D. Satheesan-led march sees unprecedented turnout...", "published": datetime.now().isoformat(), "language": "ml", "district": "Thrissur"},
        {"title": "Rahul Gandhi: LDF-BJP secret understanding exposed in Kerala", "source": "National Herald", "url": "#", "content": "Congress leader alleges collusion citing corruption cases...", "published": datetime.now().isoformat(), "language": "en", "district": None},
        {"title": "Youth unemployment at 1 in 3 in Kerala — UDF attack sharpens", "source": "Deccan Herald", "url": "#", "content": "Opposition targets LDF on jobs crisis...", "published": datetime.now().isoformat(), "language": "en", "district": "Kozhikode"},
        {"title": "NDA surges to 38% in Nemom — triangular contest intensifies", "source": "Mathrubhumi", "url": "#", "content": "BJP consolidating Hindu vote in South Kerala capital...", "published": datetime.now().isoformat(), "language": "ml", "district": "Thiruvananthapuram"},
    ]

def _get_mock_social_data() -> list[dict]:
    return [
        {"source": "Twitter/X", "content": "Pinarayi government has failed on inflation. Time for change! #UDF #Kerala2026", "district": "Ernakulam", "sentiment_hint": "negative_ldf"},
        {"source": "Facebook", "content": "Satheesan's open sabha in Thrissur was impressive. He actually listens!", "district": "Thrissur", "sentiment_hint": "positive_udf"},
        {"source": "YouTube", "content": "Rahul Gandhi's Kozhikode speech viral — 2M views in 6 hours", "district": "Kozhikode", "sentiment_hint": "positive_udf"},
        {"source": "WhatsApp", "content": "BJP winning in Thiruvananthapuram means split vote in South Kerala. Worry for UDF.", "district": "Thiruvananthapuram", "sentiment_hint": "risk_nda"},
    ]

def _get_mock_field_reports() -> list[dict]:
    return [
        {"constituency": "Thrissur", "observer": "District Coordinator", "date": date.today().isoformat(), "observations": "Strong anti-incumbency visible at vegetable markets. Women voters actively discussing inflation. NDA booth workers spotted in 3 wards.", "udf_confidence": 6, "issues_raised": ["coconut oil prices", "auto jobs", "road condition"]},
        {"constituency": "Pala", "observer": "Block Level Worker", "date": date.today().isoformat(), "observations": "Church community divided. Some priests privately supportive of UDF candidate. Rubber price issue dominant.", "udf_confidence": 7, "issues_raised": ["rubber price", "youth migration", "healthcare"]},
    ]

def _get_mock_sentiments() -> list[dict]:
    return [
        {"topic": "inflation", "front": "LDF", "score": -0.82, "volume": 95, "platform": "Twitter", "district": "Thiruvananthapuram", "key_signal": "9.49% inflation dominates negative LDF coverage"},
        {"topic": "UDF momentum", "front": "UDF", "score": 0.71, "volume": 78, "platform": "Facebook", "district": "Ernakulam", "key_signal": "Puthuyuga Yathra crowds signal positive momentum"},
        {"topic": "NDA spoiler", "front": "NDA", "score": 0.42, "volume": 55, "platform": "Twitter", "district": "Thiruvananthapuram", "key_signal": "BJP consolidation threatens UDF in Nemom, Attingal"},
        {"topic": "youth unemployment", "front": "LDF", "score": -0.68, "volume": 72, "platform": "YouTube", "district": "Kozhikode", "key_signal": "Rahul Gandhi drug + jobs speech went viral"},
    ]

def _get_mock_clusters() -> list[dict]:
    return [
        {"cluster_id":"C1","theme":"Inflation Crisis","narrative":"Kerala's 9.49% inflation narrative is dominating voter conversations, directly blaming LDF mismanagement.","front_benefiting":"UDF","momentum":"RISING","sentiment_score":-0.80,"affected_districts":["Thiruvananthapuram","Thrissur","Ernakulam"],"electoral_impact":"HIGH","headlines_count":12},
        {"cluster_id":"C2","theme":"LDF-BJP Collusion","narrative":"Congress's 'secret understanding' between LDF and BJP is gaining traction, cornering CPI(M) ideologically.","front_benefiting":"UDF","momentum":"RISING","sentiment_score":-0.65,"affected_districts":["Kozhikode","Malappuram"],"electoral_impact":"HIGH","headlines_count":8},
        {"cluster_id":"C3","theme":"Youth Unemployment","narrative":"1-in-3 youth jobless story combined with drug menace creates powerful UDF attack narrative.","front_benefiting":"UDF","momentum":"STABLE","sentiment_score":-0.55,"affected_districts":["Kozhikode","Ernakulam","Kottayam"],"electoral_impact":"HIGH","headlines_count":7},
        {"cluster_id":"C4","theme":"NDA South Kerala Surge","narrative":"BJP consolidation in Thiruvananthapuram and Nemom risks splitting anti-LDF vote.","front_benefiting":"LDF","momentum":"RISING","sentiment_score":0.35,"affected_districts":["Thiruvananthapuram","Kollam"],"electoral_impact":"MEDIUM","headlines_count":5},
        {"cluster_id":"C5","theme":"LDF Welfare Schemes","narrative":"LDF's pre-election budget with pension hikes tries to reset narrative with scheme beneficiaries.","front_benefiting":"LDF","momentum":"FALLING","sentiment_score":0.28,"affected_districts":["Alappuzha","Kannur"],"electoral_impact":"MEDIUM","headlines_count":4},
    ]

def _get_mock_constituency_scores() -> list[dict]:
    return [
        {"constituency":"Thrissur","district":"Thrissur","udf_win_probability":52,"swing_direction":"CONTESTED","risk_level":"CRITICAL","today_change":+1.2,"key_issues":["inflation","NDA split","Christian vote"],"recommendation":"Deploy Rahul Gandhi rally here — his 44% influence rating highest in state","last_updated":datetime.now().isoformat()},
        {"constituency":"Nemom","district":"Thiruvananthapuram","udf_win_probability":31,"swing_direction":"LDF_HOLD","risk_level":"HIGH","today_change":-0.8,"key_issues":["BJP spoiler","Ezhava drift","Hindu consolidation"],"recommendation":"Counter NDA with data showing BJP cannot win here — redirect their vote","last_updated":datetime.now().isoformat()},
        {"constituency":"Attingal","district":"Thiruvananthapuram","udf_win_probability":48,"swing_direction":"CONTESTED","risk_level":"CRITICAL","today_change":+0.5,"key_issues":["NDA 29% spoiler","inflation","candidate quality"],"recommendation":"Bipolar messaging campaign: 'Only UDF can beat LDF here'","last_updated":datetime.now().isoformat()},
    ]

def _get_mock_swing_predictions() -> dict:
    return {
        "seats_moving_toward_udf": ["Chalakudy", "Kayamkulam", "Beypore", "Aranmula"],
        "seats_moving_toward_ldf": ["Kuthuparamba"],
        "seats_at_risk_nda_spoil": ["Thrissur", "Attingal", "Kazhakuttam", "Irinjalakkuda"],
        "overall_momentum": "UDF_LEADING",
        "confidence_in_udf_majority": 72,
        "seats_likely_udf": 78,
        "seats_likely_ldf": 54,
        "seats_likely_nda": 8,
        "swing_summary": "UDF holds structural momentum with inflation and anti-incumbency narratives accelerating. NDA spoiler risk in 4 South Kerala seats is the primary danger that could cost UDF 6-8 seats and push the majority into uncertainty.",
        "critical_actions_today": [
            "Deploy bipolar counter-messaging in Thrissur, Attingal, Kazhakuttam immediately",
            "Maximize Rahul Gandhi social media content — 44% influence rating is UDF's biggest asset",
            "Activate women's network for Indira Guarantee scheme in 15 swing constituencies"
        ]
    }

def _get_mock_risks() -> list[dict]:
    return [
        {"risk_id":"R1","severity":"CRITICAL","title":"NDA Spoiler Effect — 4 South Kerala Seats","description":"BJP polling 28-33% in Thrissur, Attingal, Kazhakuttam, Irinjalakkuda. In all 4, this creates genuine 3-way splits that could hand LDF wins on minority vote shares.","affected_seats":["Thrissur","Attingal","Kazhakuttam","Irinjalakkuda"],"counter_action":"Launch immediate bipolar campaign: data showing BJP has never won these seats — their vote is wasted","time_sensitivity":"IMMEDIATE"},
        {"risk_id":"R2","severity":"HIGH","title":"UDF Overconfidence — Turnout Suppression Risk","description":"Survey leads may create complacency among UDF voters who assume victory. LDF's disciplined cadre will turn out regardless.","affected_seats":["Ernakulam","Malappuram","Kottayam"],"counter_action":"Strong GOTV messaging: 'Your vote matters — don't assume, show up'","time_sensitivity":"24H"},
        {"risk_id":"R3","severity":"HIGH","title":"LDF Pre-Election Budget Scheme Bounce","description":"LDF's populist budget announcements (pension hike, youth loans) could create short-term positive sentiment among beneficiaries.","affected_seats":["Alappuzha","Kannur","Kozhikode"],"counter_action":"Counter: 'LDF announces schemes only when elections arrive — same empty promises for 10 years'","time_sensitivity":"48H"},
        {"risk_id":"R4","severity":"MEDIUM","title":"Congress Internal Rebel Candidates","description":"Seat-sharing disputes could produce rebel candidates in 3-4 marginal seats, splitting UDF's vote by 2-4%.","affected_seats":["Pala","Palakkad","Kuthuparamba"],"counter_action":"Emergency mediation by state leadership. Any rebel = automatic disqualification","time_sensitivity":"24H"},
        {"risk_id":"R5","severity":"MEDIUM","title":"Ezhava Community Drift Acceleration","description":"SNDP-BJP alignment continues to pull Ezhava votes away from LDF's traditional base. But if BJP fails to convert, votes may not go to UDF either.","affected_seats":["Nemom","Attingal","Kazhakuttam"],"counter_action":"UDF outreach to SNDP local leaders with development + employment pitch","time_sensitivity":"WEEK"},
    ]

def _get_mock_actions() -> dict:
    return {
        "date": date.today().isoformat(),
        "priority_message_of_day": "Kerala's kitchen is on fire — 9.49% inflation under LDF. UDF's Indira Guarantees will put ₹10,000 back in your monthly budget.",
        "leadership_actions": {
            "satheesan": ["Hold open sabha in Thrissur — address inflation and NDA spoiler directly with data", "Evening press conference: release constituency-wise inflation burden data"],
            "rahul_gandhi": ["Record 60-second Instagram Reel on youth unemployment in Malayalam — target first-time voters"],
            "district_presidents": ["Activate mahila networks in all 50 swing seat constituencies for Indira Guarantee outreach", "Brief all booth captains: turnout is the game — don't assume victory"]
        },
        "digital_actions": {
            "trending_hashtags": ["#KeralamJayikkum", "#InflationUnderLDF", "#UDFIndiraGuarantee"],
            "content_themes": ["Kitchen table inflation comparison before/after LDF", "First-time voter appeals", "Satheesan accessibility vs Pinarayi arrogance contrast"],
            "platform_focus": ["Facebook (mass rural reach — IUML mahila network)", "Instagram Reels (18-25 first-time voters in Ernakulam, Thrissur, Kozhikode)"]
        },
        "ground_actions": {
            "priority_constituencies": ["Thrissur", "Attingal", "Pala", "Chalakudy", "Irinjalakkuda"],
            "booth_instructions": ["Identify every UDF voter who hasn't committed to voting — personal call today", "Counter BJP volunteers in split-risk booths with bipolar messaging", "Distribute printed Indira Guarantee cards door-to-door in women's households"],
            "voter_outreach_focus": "Women heads of household — Indira Guarantee free bus travel + college allowance pitch"
        },
        "alliance_management": ["IUML coordination call — ensure Malappuram district delivers 9+ seats", "Kerala Congress (Jacob) — check candidate loyalty in Kottayam constituencies"],
        "counter_narrative": "When LDF says 'Who else but LDF?' — say: 'Who brought inflation? Who brought unemployment? Who stole Sabarimala gold? LDF did. Kerala has the answer.'",
        "do_not_do": ["Do NOT discuss internal ticket dissatisfaction publicly — it feeds LDF narrative of UDF chaos", "Do NOT ignore NDA voters — treat them as persuadable, not enemies"]
    }


# ─── ENTRYPOINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Kerala 2026 War Room — LangGraph Intelligence Pipeline"
    )
    parser.add_argument("--run-now",  action="store_true",
        help="Execute pipeline immediately")
    parser.add_argument("--schedule", type=str, default=None,
        metavar="HH:MM", help="Schedule daily run at HH:MM IST (e.g. 06:00)")
    parser.add_argument("--run-id", type=str, default=None,
        help="Custom run identifier")
    args = parser.parse_args()

    if args.schedule:
        schedule_daily_run(args.schedule)
    else:
        # Default: run now
        asyncio.run(run_pipeline(args.run_id))
