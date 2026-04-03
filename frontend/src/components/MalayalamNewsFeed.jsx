import { useState, useEffect, useCallback } from "react";

const T = {
  bg:"#03080F", panel:"#07111E", card:"#0B1929", border:"#162840",
  udf:"#00C8FF", ldf:"#FF3F3F", nda:"#FF9500",
  green:"#00E57A", amber:"#FFD600", muted:"#4A6A8A",
  text:"#D8EAF8", dim:"#2A4A6A", dark:"#050C1A",
};

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ── Helpers ──────────────────────────────────────────────────

const angleColor = a =>
  a === "UDF" ? T.udf : a === "LDF" ? T.ldf : a === "NDA" ? T.nda : T.muted;

const angleIcon  = a =>
  a === "UDF" ? "🔵" : a === "LDF" ? "🔴" : a === "NDA" ? "🟠" : "⚪";

const urgencyIcon = u =>
  u === "BREAKING" ? "🚨" : u === "TODAY" ? "📰" : "📄";

const impactColor = i =>
  i === "HIGH" ? T.ldf : i === "MEDIUM" ? T.amber : T.muted;

const sentColor = s =>
  s >= 0.3 ? T.green : s <= -0.3 ? T.ldf : T.amber;

function PulseDot({ color = T.green }) {
  const [b, setB] = useState(true);
  useEffect(() => { const t = setInterval(() => setB(x => !x), 800); return () => clearInterval(t); }, []);
  return <div style={{ width: 7, height: 7, borderRadius: "50%", flexShrink: 0,
    background: b ? color : `${color}44`, boxShadow: b ? `0 0 8px ${color}` : "none",
    transition: "all 0.4s" }} />;
}

function Chip({ label, color }) {
  const c = color || T.muted;
  return (
    <span style={{ fontSize: 9, padding: "2px 8px", borderRadius: 20,
      background: `${c}18`, color: c, border: `1px solid ${c}35`,
      fontFamily: "monospace", letterSpacing: 1, whiteSpace: "nowrap" }}>
      {label}
    </span>
  );
}

function SourceBadge({ name, tier }) {
  const c = tier === 1 ? T.udf : tier === 2 ? T.amber : T.muted;
  return (
    <span style={{ fontSize: 9, padding: "1px 7px", borderRadius: 10,
      background: `${c}15`, color: c, border: `1px solid ${c}30`,
      fontFamily: "monospace" }}>
      {name} {tier === 1 ? "★" : ""}
    </span>
  );
}

// ── Stats Strip ───────────────────────────────────────────────

function StatsStrip({ data }) {
  const counts = {
    UDF:     data.by_angle?.UDF?.length || 0,
    LDF:     data.by_angle?.LDF?.length || 0,
    NDA:     data.by_angle?.NDA?.length || 0,
    NEUTRAL: data.by_angle?.NEUTRAL?.length || 0,
  };
  return (
    <div style={{ display: "grid",
      gridTemplateColumns: "repeat(auto-fit,minmax(110px,1fr))",
      gap: 1, background: T.border, marginBottom: 14 }}>
      {[
        { l: "Total Fetched",   v: data.total_fetched,     c: T.udf    },
        { l: "Summarized",      v: data.total_summarized,  c: T.green  },
        { l: "Breaking",        v: data.breaking_count,    c: T.ldf    },
        { l: "High Impact",     v: data.high_impact_count, c: T.amber  },
        { l: "UDF Favorable",   v: counts.UDF,             c: T.udf    },
        { l: "LDF Favorable",   v: counts.LDF,             c: T.ldf    },
        { l: "NDA Favorable",   v: counts.NDA,             c: T.nda    },
        { l: "Neutral",         v: counts.NEUTRAL,         c: T.muted  },
      ].map((k, i) => (
        <div key={i} style={{ background: T.panel, padding: "10px 12px" }}>
          <div style={{ fontSize: 8, color: T.muted, textTransform: "uppercase",
            letterSpacing: 1, marginBottom: 3 }}>{k.l}</div>
          <div style={{ fontSize: 18, fontWeight: 800, color: k.c,
            fontFamily: "monospace" }}>{k.v ?? "—"}</div>
        </div>
      ))}
    </div>
  );
}

// ── Article Card ──────────────────────────────────────────────

function ArticleCard({ article, expanded, onClick }) {
  const ac = angleColor(article.political_angle);
  const uc = urgencyIcon(article.urgency);
  const ic = impactColor(article.electoral_impact);
  const sc = sentColor(article.sentiment_score);

  return (
    <div onClick={onClick} style={{
      background: T.card,
      border: `1px solid ${expanded ? ac : ac + "30"}`,
      borderRadius: 8, padding: "12px 14px",
      cursor: "pointer", transition: "all 0.25s",
      boxShadow: expanded ? `0 0 20px ${ac}20` : "none",
    }}>
      {/* Header row */}
      <div style={{ display: "flex", justifyContent: "space-between",
        alignItems: "flex-start", gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center",
            gap: 6, marginBottom: 5, flexWrap: "wrap" }}>
            <span style={{ fontSize: 13 }}>{uc}</span>
            <SourceBadge name={article.source} tier={article.tier} />
            <Chip label={article.political_angle} color={ac} />
            <Chip label={article.electoral_impact} color={ic} />
            <Chip label={article.urgency} color={
              article.urgency === "BREAKING" ? T.ldf :
              article.urgency === "TODAY" ? T.amber : T.muted} />
          </div>
          {/* English title */}
          <div style={{ fontSize: 12, fontWeight: 700, color: T.text,
            lineHeight: 1.5 }}>
            {article.title_english}
          </div>
          {/* Original title */}
          {article.title_original !== article.title_english && (
            <div style={{ fontSize: 10, color: T.muted, marginTop: 3,
              fontStyle: "italic", lineHeight: 1.4 }}>
              ᴹᴸ {article.title_original?.slice(0, 100)}
            </div>
          )}
        </div>
        {/* Sentiment score */}
        <div style={{ textAlign: "center", flexShrink: 0 }}>
          <div style={{ fontSize: 9, color: T.muted, marginBottom: 3 }}>SENT.</div>
          <div style={{ fontSize: 16, fontWeight: 800, color: sc,
            fontFamily: "monospace" }}>
            {article.sentiment_score >= 0 ? "+" : ""}
            {article.sentiment_score?.toFixed(1)}
          </div>
        </div>
      </div>

      {/* Summary */}
      <div style={{ fontSize: 11, color: T.muted, lineHeight: 1.6 }}>
        {expanded
          ? article.summary_english
          : `${article.summary_english?.slice(0, 130)}...`}
      </div>

      {/* Expanded content */}
      {expanded && (
        <div style={{ marginTop: 12,
          borderTop: `1px solid ${T.border}`, paddingTop: 12 }}>

          {/* Key claims */}
          {article.key_claims?.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 9, color: T.muted, letterSpacing: 2,
                marginBottom: 6 }}>KEY CLAIMS</div>
              {article.key_claims.map((claim, i) => (
                <div key={i} style={{ display: "flex", gap: 8,
                  alignItems: "flex-start", marginBottom: 5 }}>
                  <span style={{ color: ac, flexShrink: 0, fontSize: 11 }}>›</span>
                  <span style={{ fontSize: 11, color: T.text,
                    lineHeight: 1.5 }}>{claim}</span>
                </div>
              ))}
            </div>
          )}

          {/* Districts mentioned */}
          {article.districts_mentioned?.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 9, color: T.muted,
                letterSpacing: 2, marginBottom: 5 }}>DISTRICTS</div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {article.districts_mentioned.map((d, i) => (
                  <span key={i} style={{ fontSize: 10, padding: "2px 8px",
                    borderRadius: 20, background: `${T.udf}12`,
                    color: T.udf, border: `1px solid ${T.udf}25` }}>
                    {d}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* War room note */}
          {article.war_room_note && (
            <div style={{ background: `${ac}08`,
              border: `1px solid ${ac}20`,
              borderRadius: 6, padding: "8px 10px" }}>
              <div style={{ fontSize: 9, color: ac,
                letterSpacing: 2, marginBottom: 4 }}>
                WAR ROOM NOTE
              </div>
              <div style={{ fontSize: 11, color: T.text,
                lineHeight: 1.6, fontStyle: "italic" }}>
                {article.war_room_note}
              </div>
            </div>
          )}

          {/* Source link */}
          {article.url && article.url !== "#" && (
            <div style={{ marginTop: 8 }}>
              <a href={article.url} target="_blank" rel="noopener noreferrer"
                style={{ fontSize: 9, color: T.muted, textDecoration: "none" }}
                onClick={e => e.stopPropagation()}>
                🔗 {article.url.slice(0, 60)}...
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Angle Filter Tabs ─────────────────────────────────────────

function AngleTabs({ active, counts, onChange }) {
  const tabs = [
    { key: "ALL",     label: "All",     color: T.text  },
    { key: "UDF",     label: "UDF",     color: T.udf   },
    { key: "LDF",     label: "LDF",     color: T.ldf   },
    { key: "NDA",     label: "NDA",     color: T.nda   },
    { key: "NEUTRAL", label: "Neutral", color: T.muted },
    { key: "BREAKING",label: "🚨 Breaking", color: T.ldf },
    { key: "HIGH",    label: "🔥 High Impact", color: T.amber },
  ];
  return (
    <div style={{ display: "flex", gap: 0, overflowX: "auto",
      borderBottom: `1px solid ${T.border}`, marginBottom: 14 }}>
      {tabs.map(tab => (
        <button key={tab.key} onClick={() => onChange(tab.key)}
          style={{ background: "none", border: "none",
            borderBottom: active === tab.key
              ? `2px solid ${tab.color}` : "2px solid transparent",
            color: active === tab.key ? tab.color : T.muted,
            padding: "8px 14px", fontSize: 10, letterSpacing: 1,
            cursor: "pointer", whiteSpace: "nowrap",
            fontFamily: "monospace", transition: "all 0.2s" }}>
          {tab.label}
          {counts[tab.key] !== undefined && (
            <span style={{ marginLeft: 5, fontSize: 9,
              color: active === tab.key ? tab.color : T.dim }}>
              ({counts[tab.key]})
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

// ── Source Grid ───────────────────────────────────────────────

function SourceGrid({ stats }) {
  if (!stats?.by_source) return null;
  const sources = Object.entries(stats.by_source);
  return (
    <div style={{ background: T.card, border: `1px solid ${T.border}`,
      borderRadius: 8, padding: 14, marginBottom: 14 }}>
      <div style={{ fontSize: 9, color: T.muted, letterSpacing: 2,
        textTransform: "uppercase", marginBottom: 12 }}>
        SOURCE PERFORMANCE ({sources.length} feeds)
      </div>
      <div style={{ display: "grid",
        gridTemplateColumns: "repeat(auto-fill,minmax(180px,1fr))", gap: 6 }}>
        {sources.map(([name, data], i) => (
          <div key={i} style={{ background: T.dark, borderRadius: 5,
            padding: "7px 10px", display: "flex",
            justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 10, color: T.text }}>{name}</span>
            <div style={{ display: "flex", gap: 8 }}>
              <span style={{ fontSize: 10, color: T.muted,
                fontFamily: "monospace" }}>{data.total}</span>
              <span style={{ fontSize: 10, color: T.udf,
                fontFamily: "monospace" }}>{data.relevant}✓</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════

export default function MalayalamNewsFeed() {
  const [data, setData]         = useState(null);
  const [loading, setLoading]   = useState(false);
  const [fetching, setFetching] = useState(false);
  const [error, setError]       = useState(null);
  const [apiOk, setApiOk]       = useState(false);
  const [filter, setFilter]     = useState("ALL");
  const [expanded, setExpanded] = useState(null);
  const [search, setSearch]     = useState("");
  const [lastSync, setLastSync] = useState(null);
  const [showSources, setShowSources] = useState(false);

  // ── Fetch data ──────────────────────────────────────────────

  const fetchData = useCallback(async () => {
    try {
      const h = await fetch(`${API}/api/health`,
        { signal: AbortSignal.timeout(3000) });
      if (!h.ok) throw new Error();
      setApiOk(true);

      setLoading(true);
      const res = await fetch(`${API}/api/malayalam/latest`);
      if (res.ok) {
        setData(await res.json());
        setLastSync(new Date());
        setError(null);
      } else if (res.status === 404) {
        setError("no_data");
      }
    } catch (e) {
      if (e.message !== "Failed to fetch") setApiOk(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // ── Trigger fresh fetch ──────────────────────────────────────

  const triggerFetch = async () => {
    setFetching(true);
    try {
      await fetch(`${API}/api/malayalam/fetch`, { method: "POST" });
      // Poll until data appears
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        await fetchData();
        if (attempts > 20) { clearInterval(poll); setFetching(false); }
      }, 3000);
    } catch {
      setFetching(false);
    }
  };

  // ── Filter articles ──────────────────────────────────────────

  const allArticles = data?.summaries || [];

  const filteredArticles = allArticles.filter(a => {
    const matchAngle =
      filter === "ALL"     ? true :
      filter === "BREAKING"? a.urgency === "BREAKING" :
      filter === "HIGH"    ? a.electoral_impact === "HIGH" :
      a.political_angle === filter;

    const matchSearch = search === "" ||
      a.title_english?.toLowerCase().includes(search.toLowerCase()) ||
      a.summary_english?.toLowerCase().includes(search.toLowerCase()) ||
      a.source?.toLowerCase().includes(search.toLowerCase());

    return matchAngle && matchSearch;
  });

  const filterCounts = {
    ALL:      allArticles.length,
    UDF:      allArticles.filter(a => a.political_angle === "UDF").length,
    LDF:      allArticles.filter(a => a.political_angle === "LDF").length,
    NDA:      allArticles.filter(a => a.political_angle === "NDA").length,
    NEUTRAL:  allArticles.filter(a => a.political_angle === "NEUTRAL").length,
    BREAKING: allArticles.filter(a => a.urgency === "BREAKING").length,
    HIGH:     allArticles.filter(a => a.electoral_impact === "HIGH").length,
  };

  return (
    <div style={{ background: T.bg, color: T.text,
      fontFamily: "'Courier New', monospace", fontSize: 13 }}>
      <style>{`
        @keyframes mlFade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
        @keyframes spin{to{transform:rotate(360deg)}}
        ::-webkit-scrollbar{width:3px;height:3px;background:${T.bg}}
        ::-webkit-scrollbar-thumb{background:${T.dim};border-radius:3px}
      `}</style>

      {/* ── Sub-header ── */}
      <div style={{ background: "#070F1E",
        borderBottom: `1px solid ${T.border}`,
        padding: "10px 18px", display: "flex",
        alignItems: "center", justifyContent: "space-between",
        flexWrap: "wrap", gap: 10 }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700,
            letterSpacing: 2, color: T.udf }}>
            📰 MALAYALAM NEWS INTELLIGENCE
          </div>
          <div style={{ fontSize: 9, color: T.muted, marginTop: 2 }}>
            12 Malayalam RSS feeds · GPT-4o translation + political analysis
          </div>
        </div>
        <div style={{ display: "flex", gap: 8,
          flexWrap: "wrap", alignItems: "center" }}>
          {/* API status */}
          <div style={{ display: "flex", alignItems: "center", gap: 6,
            background: apiOk ? `${T.green}10` : `${T.ldf}10`,
            border: `1px solid ${apiOk ? T.green + "30" : "#FF3F3F30"}`,
            borderRadius: 6, padding: "5px 10px" }}>
            <PulseDot color={apiOk ? T.green : "#FF3F3F"} />
            <span style={{ fontSize: 10,
              color: apiOk ? T.green : "#FF6666",
              fontFamily: "monospace" }}>
              {apiOk ? "API CONNECTED" : "API OFFLINE"}
            </span>
          </div>

          {lastSync && (
            <span style={{ fontSize: 9, color: T.dim }}>
              Synced {lastSync.toLocaleTimeString()}
            </span>
          )}

          <button onClick={fetchData}
            style={{ padding: "5px 10px", borderRadius: 5,
              background: "transparent", border: `1px solid ${T.border}`,
              color: T.muted, fontSize: 9, cursor: "pointer",
              fontFamily: "monospace" }}>
            ↺ REFRESH
          </button>

          <button onClick={triggerFetch} disabled={fetching}
            style={{ padding: "6px 14px", borderRadius: 6,
              background: fetching ? T.dim : `${T.udf}18`,
              border: `1px solid ${fetching ? T.dim : T.udf + "40"}`,
              color: fetching ? T.muted : T.udf,
              fontSize: 10, letterSpacing: 1,
              cursor: fetching ? "not-allowed" : "pointer",
              fontFamily: "monospace" }}>
            {fetching ? (
              <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%",
                  border: `1px solid ${T.udf}`,
                  borderTop: "1px solid transparent",
                  animation: "spin 0.8s linear infinite" }} />
                FETCHING...
              </span>
            ) : "📡 FETCH LATEST"}
          </button>
        </div>
      </div>

      {/* ── Offline banner ── */}
      {!apiOk && (
        <div style={{ background: "#FF3F3F08",
          borderBottom: `1px solid #FF3F3F20`,
          padding: "10px 18px" }}>
          <div style={{ fontSize: 11, color: "#FF8888",
            fontWeight: 700, marginBottom: 4 }}>
            ⚠️ FastAPI bridge offline
          </div>
          <div style={{ background: "#010609", borderRadius: 5,
            padding: "6px 12px", fontFamily: "monospace",
            fontSize: 11, color: T.green, display: "inline-block" }}>
            cd pipeline &nbsp;&&nbsp; uvicorn api:app --reload --port 8000
          </div>
        </div>
      )}

      <div style={{ padding: 14 }}>

        {/* Loading */}
        {loading && !data && (
          <div style={{ textAlign: "center", padding: 60 }}>
            <div style={{ width: 40, height: 40, borderRadius: "50%",
              border: `2px solid ${T.border}`,
              borderTop: `2px solid ${T.udf}`,
              animation: "spin 1s linear infinite",
              margin: "0 auto 16px" }} />
            <div style={{ fontSize: 12, color: T.muted }}>
              Loading Malayalam news...
            </div>
          </div>
        )}

        {/* No data yet */}
        {!loading && error === "no_data" && (
          <div style={{ textAlign: "center", padding: 60, color: T.muted }}>
            <div style={{ fontSize: 36, marginBottom: 14 }}>📭</div>
            <div style={{ fontSize: 13, marginBottom: 8 }}>
              No Malayalam news summaries yet
            </div>
            <div style={{ fontSize: 10, color: T.dim, marginBottom: 20 }}>
              Click 📡 FETCH LATEST to pull from 12 Malayalam RSS feeds
            </div>
            <div style={{ fontSize: 10, color: T.muted, marginBottom: 6 }}>
              Or run in terminal:
            </div>
            <div style={{ background: "#010609", borderRadius: 6,
              padding: "8px 16px", fontFamily: "monospace",
              fontSize: 11, color: T.green, display: "inline-block" }}>
              cd pipeline &amp;&amp; python malayalam_rss.py --fetch
            </div>
          </div>
        )}

        {/* ── Main content ── */}
        {data && (
          <div style={{ animation: "mlFade 0.4s ease" }}>

            {/* Date + meta */}
            <div style={{ display: "flex", justifyContent: "space-between",
              alignItems: "center", marginBottom: 12,
              flexWrap: "wrap", gap: 8 }}>
              <div>
                <span style={{ fontSize: 11, color: T.muted }}>
                  Intelligence date:{" "}
                </span>
                <span style={{ fontSize: 11, color: T.text, fontWeight: 700 }}>
                  {data.fetched_at?.slice(0, 10)}
                </span>
                <span style={{ fontSize: 10, color: T.dim, marginLeft: 8 }}>
                  {data.fetched_at?.slice(11, 16)} IST
                </span>
              </div>
              <button onClick={() => setShowSources(s => !s)}
                style={{ padding: "4px 10px", borderRadius: 5,
                  background: "transparent", border: `1px solid ${T.border}`,
                  color: T.muted, fontSize: 9, cursor: "pointer",
                  fontFamily: "monospace" }}>
                {showSources ? "▲ Hide Sources" : "▼ Show Sources"}
              </button>
            </div>

            {/* Stats strip */}
            <StatsStrip data={data} />

            {/* Source performance */}
            {showSources && (
              <SourceGrid stats={data.fetch_stats} />
            )}

            {/* Search bar */}
            <div style={{ marginBottom: 12 }}>
              <input
                type="text"
                placeholder="Search articles... (title, source, content)"
                value={search}
                onChange={e => setSearch(e.target.value)}
                style={{ width: "100%", padding: "8px 14px",
                  background: T.card, border: `1px solid ${T.border}`,
                  borderRadius: 6, color: T.text, fontSize: 11,
                  fontFamily: "monospace", outline: "none",
                  boxSizing: "border-box" }}
              />
            </div>

            {/* Angle filter tabs */}
            <AngleTabs
              active={filter}
              counts={filterCounts}
              onChange={f => { setFilter(f); setExpanded(null); }}
            />

            {/* Results count */}
            <div style={{ fontSize: 10, color: T.muted,
              marginBottom: 12 }}>
              Showing {filteredArticles.length} of {allArticles.length} articles
              {search && ` matching "${search}"`}
            </div>

            {/* Article grid */}
            {filteredArticles.length === 0 ? (
              <div style={{ textAlign: "center", padding: 40,
                color: T.muted, fontSize: 12 }}>
                No articles matching current filter
              </div>
            ) : (
              <div style={{ display: "grid",
                gridTemplateColumns: "repeat(auto-fill,minmax(380px,1fr))",
                gap: 10 }}>
                {filteredArticles.map((article, i) => (
                  <ArticleCard
                    key={i}
                    article={article}
                    expanded={expanded === i}
                    onClick={() => setExpanded(expanded === i ? null : i)}
                  />
                ))}
              </div>
            )}

            {/* RSS feed list */}
            <div style={{ marginTop: 20, background: T.card,
              border: `1px solid ${T.border}`,
              borderRadius: 8, padding: 14 }}>
              <div style={{ fontSize: 9, color: T.muted, letterSpacing: 2,
                textTransform: "uppercase", marginBottom: 10 }}>
                📡 ACTIVE RSS FEEDS (12 SOURCES)
              </div>
              <div style={{ display: "grid",
                gridTemplateColumns: "repeat(auto-fill,minmax(220px,1fr))",
                gap: 6 }}>
                {[
                  { name: "Mathrubhumi",    tier: 1, type: "Daily"   },
                  { name: "Manorama Online",tier: 1, type: "Daily"   },
                  { name: "Mangalam",       tier: 1, type: "Daily"   },
                  { name: "Deepika",        tier: 1, type: "Daily"   },
                  { name: "Asianet News",   tier: 2, type: "TV"      },
                  { name: "Media One",      tier: 2, type: "TV"      },
                  { name: "Reporter TV",    tier: 2, type: "TV"      },
                  { name: "Janam TV",       tier: 2, type: "TV"      },
                  { name: "Kerala Kaumudi", tier: 3, type: "Digital" },
                  { name: "Veekshanam",     tier: 3, type: "Digital" },
                  { name: "Deshabhimani",   tier: 3, type: "LDF aligned" },
                  { name: "Janayugom",      tier: 3, type: "CPI aligned" },
                ].map((s, i) => {
                  const c = s.tier === 1 ? T.udf : s.tier === 2 ? T.amber : T.muted;
                  return (
                    <div key={i} style={{ background: T.dark,
                      borderRadius: 5, padding: "7px 10px",
                      display: "flex", justifyContent: "space-between",
                      alignItems: "center",
                      border: `1px solid ${c}18` }}>
                      <div>
                        <div style={{ fontSize: 10, color: T.text }}>
                          {s.name}
                          {s.tier === 1 && " ★"}
                        </div>
                        <div style={{ fontSize: 8, color: T.dim }}>
                          {s.type}
                        </div>
                      </div>
                      <span style={{ fontSize: 8, padding: "1px 6px",
                        borderRadius: 8, background: `${c}15`,
                        color: c, border: `1px solid ${c}25` }}>
                        T{s.tier}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>
        )}
      </div>
    </div>
  );
}
