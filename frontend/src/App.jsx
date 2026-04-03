import { useState, useEffect } from "react";
import WarRoomDashboard from "./components/WarRoomDashboard.jsx";
import SwingPredictionEngine from "./components/SwingPredictionEngine.jsx";
import PipelineMonitor from "./components/PipelineMonitor.jsx";
import MalayalamNewsFeed from "./components/MalayalamNewsFeed.jsx";
import KeralaCMap from "./components/KeralaCMap.jsx";

const T = {
  bg: "#03080F", border: "#162840", text: "#D8EAF8",
  udf: "#00C8FF", muted: "#4A6A8A", panel: "#07111E",
};

const MODULES = [
  { id: "warroom",   icon: "🗳️",  label: "War Room",          sub: "Live Intelligence Dashboard"     },
  { id: "swing",     icon: "🤖",  label: "Swing AI Engine",   sub: "Constituency Prediction"         },
  { id: "pipeline",  icon: "⚙️",  label: "Pipeline Monitor",  sub: "LangGraph Intelligence Feed"     },
  { id: "malayalam", icon: "📰", label: "Malayalam News", sub: "12 RSS Feeds · GPT-4o Translated"},
  { id: "map", icon: "🗺️", label: "Constituency Map", sub: "140 Seats · Interactive"},
];

function TopBar({ active, setActive }) {
  const [pulse, setPulse] = useState(true);
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const p = setInterval(() => setPulse(b => !b), 900);
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => { clearInterval(p); clearInterval(t); };
  }, []);

  return (
    <div style={{
      background: "linear-gradient(135deg,#03080F,#07111E)",
      borderBottom: `1px solid ${T.border}`,
      position: "sticky", top: 0, zIndex: 100,
    }}>
      {/* Brand row */}
      <div style={{
        display: "flex", alignItems: "center",
        justifyContent: "space-between", padding: "10px 20px",
        borderBottom: `1px solid ${T.border}40`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ position: "relative" }}>
            <div style={{
              width: 38, height: 38, borderRadius: 10,
              background: `linear-gradient(135deg,${T.udf}25,${T.udf}08)`,
              border: `1px solid ${T.udf}40`,
              display: "flex", alignItems: "center",
              justifyContent: "center", fontSize: 18,
            }}>🗳️</div>
            <div style={{
              position: "absolute", top: 0, right: 0,
              width: 9, height: 9, borderRadius: "50%",
              background: pulse ? "#00E57A" : "#00E57A55",
              boxShadow: pulse ? "0 0 8px #00E57A" : "none",
              transition: "all 0.4s",
            }} />
          </div>
          <div>
            <div style={{
              fontSize: 15, fontWeight: 700, letterSpacing: 3,
              color: T.udf, fontFamily: "monospace",
              textShadow: `0 0 20px ${T.udf}40`,
            }}>
              KERALA WAR ROOM 2026
            </div>
            <div style={{ fontSize: 9, color: T.muted, letterSpacing: 2, fontFamily: "monospace" }}>
              UDF STRATEGIC INTELLIGENCE CENTRE · DEVELOPED BY PRANAV 
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          {/* Live clock */}
          <div style={{
            background: "#0A1E3A", border: `1px solid ${T.border}`,
            borderRadius: 6, padding: "5px 12px", textAlign: "center",
          }}>
            <div style={{ fontSize: 9, color: T.muted, letterSpacing: 1 }}>IST</div>
            <div style={{ fontSize: 13, fontFamily: "monospace", color: T.text, fontWeight: 700 }}>
              {time.toLocaleTimeString("en-IN", { hour12: false })}
            </div>
          </div>

          {/* Days to polling */}
          <DaysCounter />

          {/* Status badge */}
          <div style={{
            display: "flex", alignItems: "center", gap: 6,
            background: "#00E57A10", border: "1px solid #00E57A30",
            borderRadius: 6, padding: "6px 12px",
          }}>
            <div style={{
              width: 7, height: 7, borderRadius: "50%",
              background: "#00E57A", boxShadow: "0 0 8px #00E57A",
            }} />
            <span style={{ fontSize: 10, color: "#00E57A", fontFamily: "monospace" }}>
              ALL SYSTEMS LIVE
            </span>
          </div>
        </div>
      </div>

      {/* Module nav */}
      <div style={{
        display: "flex", padding: "0 20px",
        overflowX: "auto", gap: 0,
      }}>
        {MODULES.map(m => (
          <button key={m.id} onClick={() => setActive(m.id)}
            style={{
              background: "none", border: "none",
              borderBottom: active === m.id
                ? `2px solid ${T.udf}` : "2px solid transparent",
              color: active === m.id ? T.udf : T.muted,
              padding: "10px 22px", cursor: "pointer",
              fontFamily: "monospace", transition: "all 0.2s",
              display: "flex", flexDirection: "column",
              alignItems: "flex-start", gap: 2, whiteSpace: "nowrap",
            }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 14 }}>{m.icon}</span>
              <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1 }}>
                {m.label}
              </span>
            </div>
            <span style={{ fontSize: 8, letterSpacing: 1, opacity: 0.6 }}>
              {m.sub}
            </span>
          </button>
        ))}

        {/* Polling day indicator */}
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", padding: "0 4px" }}>
          <div style={{
            background: "#FF444412", border: "1px solid #FF444440",
            borderRadius: 5, padding: "4px 12px",
          }}>
            <span style={{ fontSize: 9, color: "#FF6666", fontFamily: "monospace" }}>
              POLL: APR 9 · RESULTS: MAY 4 · 140 SEATS
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function DaysCounter() {
  const [days, setDays] = useState(0);
  useEffect(() => {
    const poll = new Date("2026-04-09T07:00:00+05:30");
    const diff = Math.max(0, poll - Date.now());
    setDays(Math.floor(diff / 86400000));
  }, []);
  return (
    <div style={{
      background: days <= 7 ? "#FF444412" : "#00C8FF12",
      border: `1px solid ${days <= 7 ? "#FF444440" : "#00C8FF30"}`,
      borderRadius: 6, padding: "5px 12px", textAlign: "center",
    }}>
      <div style={{ fontSize: 9, color: T.muted }}>POLLING IN</div>
      <div style={{
        fontSize: 16, fontWeight: 800, fontFamily: "monospace",
        color: days <= 7 ? "#FF6666" : T.udf,
      }}>{days}d</div>
    </div>
  );
}

export default function App() {
  const [active, setActive] = useState("warroom");

  return (
    <div style={{ background: T.bg, minHeight: "100vh", fontFamily: "monospace" }}>
      <TopBar active={active} setActive={setActive} />
      <div>
        {active === "warroom"  && <WarRoomDashboard />}
        {active === "swing"    && <SwingPredictionEngine />}
        {active === "pipeline" && <PipelineMonitor />}
        {active === "malayalam" && <MalayalamNewsFeed />}
        {active === "map" && <KeralaCMap />}
      </div>
    </div>
  );
}
