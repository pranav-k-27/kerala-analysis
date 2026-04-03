import { useState, useEffect, useRef, useCallback } from "react";

const T = {
  bg:"#03080F", panel:"#07111E", card:"#0B1929", border:"#162840",
  udf:"#00C8FF", ldf:"#FF3F3F", nda:"#FF9500",
  green:"#00E57A", amber:"#FFD600", muted:"#4A6A8A",
  text:"#D8EAF8", dim:"#2A4A6A", dark:"#050C1A",
};

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const NODES = [
  {id:"ingest_news",         label:"News Ingestion",       icon:"📡", desc:"Scrapes Mathrubhumi, Manorama, The Hindu, Deccan Herald, National Herald", layer:"INGESTION",     color:T.udf},
  {id:"ingest_social",       label:"Social Media",         icon:"📱", desc:"X/Twitter, Facebook, YouTube — Malayalam + English NLP signals",           layer:"INGESTION",     color:T.udf},
  {id:"ingest_field",        label:"Field Reports",        icon:"🗺️", desc:"WhatsApp / Telegram booth-level inputs from ground workers",               layer:"INGESTION",     color:T.udf},
  {id:"analyze_sentiment",   label:"Sentiment Analysis",   icon:"🧠", desc:"GPT-4o analyzes content for per-front, per-district sentiment scores",     layer:"AI PROCESSING", color:T.amber},
  {id:"cluster_topics",      label:"Topic Clustering",     icon:"🗂️", desc:"Detects rising/falling narratives — Inflation, Corruption, NDA Spoiler",  layer:"AI PROCESSING", color:T.amber},
  {id:"score_constituencies",label:"Constituency Scorer",  icon:"🎯", desc:"Updates UDF win probability for all swing seats from today's signals",     layer:"AI PROCESSING", color:T.amber},
  {id:"predict_swings",      label:"Swing Predictor",      icon:"📈", desc:"Identifies seats moving today and overall momentum direction",             layer:"AI PROCESSING", color:T.amber},
  {id:"detect_risks",        label:"Risk Detector",        icon:"⚠️", desc:"Scans for CRITICAL threats: NDA spoilers, LDF bounces, rebel candidates",  layer:"AI PROCESSING", color:"#FF6666"},
  {id:"recommend_actions",   label:"Action Recommender",   icon:"⚡", desc:"Generates today's tactical playbook for leadership and ground teams",      layer:"DECISION",      color:T.green},
  {id:"generate_report",     label:"Report Generator",     icon:"📋", desc:"Produces Daily War Brief saved to reports/ as JSON + Markdown",           layer:"OUTPUT",        color:T.green},
];

const MOCK_LOGS = [
  {node:"ingest_news",         status:"OK",   msg:"Collected 47 articles from 5 Malayalam + national sources"},
  {node:"ingest_social",       status:"OK",   msg:"Pulled 312 social signals (X/Twitter + Facebook + YouTube)"},
  {node:"ingest_field",        status:"OK",   msg:"Processed 8 field reports from ground coordinators"},
  {node:"analyze_sentiment",   status:"OK",   msg:"Generated 124 sentiment readings · UDF avg: +0.71, LDF avg: -0.68"},
  {node:"cluster_topics",      status:"OK",   msg:"Identified 8 narrative clusters · Top: Inflation Crisis (RISING)"},
  {node:"score_constituencies",status:"OK",   msg:"Scored 13 swing seats · Thrissur: 52% UDF (+1.2%), Nemom: 31%"},
  {node:"predict_swings",      status:"OK",   msg:"Momentum: UDF_SURGING · Confidence: 72% · Proj UDF: 78 seats"},
  {node:"detect_risks",        status:"WARN", msg:"2 CRITICAL risks: NDA spoiler in 4 seats + Turnout suppression"},
  {node:"recommend_actions",   status:"OK",   msg:"Playbook: Bipolar messaging in Thrissur + Attingal — IMMEDIATE"},
  {node:"generate_report",     status:"OK",   msg:"Brief saved to reports/brief_2026-03-31_XXXX.md"},
];

// ── Small components ─────────────────────────────────────────

function PulseDot({color=T.green}){
  const [b,setB]=useState(true);
  useEffect(()=>{const t=setInterval(()=>setB(x=>!x),800);return()=>clearInterval(t);},[]);
  return <div style={{width:8,height:8,borderRadius:"50%",flexShrink:0,
    background:b?color:`${color}44`,boxShadow:b?`0 0 8px ${color}`:"none",transition:"all 0.4s"}}/>;
}

function Bar({val,max=100,color,height=5}){
  return(
    <div style={{height,background:T.dim,borderRadius:3,overflow:"hidden"}}>
      <div style={{width:`${Math.min(100,(val/max)*100)}%`,height:"100%",
        background:color,boxShadow:`0 0 6px ${color}50`,transition:"width 0.8s ease"}}/>
    </div>
  );
}

function Chip({label,color}){
  const c=color||(
    label==="CRITICAL"||label==="ERROR"?"#FF3F3F":
    label==="HIGH"||label==="WARN"?"#FF9500":
    label==="MEDIUM"?"#FFD600":
    label==="LOW"||label==="OK"||label==="COMPLETE"?"#00E57A":
    label?.includes("SURGING")||label?.includes("LEADING")?"#00E57A":
    label?.includes("NECK")?"#FFD600":"#4A6A8A"
  );
  return(
    <span style={{fontSize:9,padding:"2px 8px",borderRadius:20,
      background:`${c}18`,color:c,border:`1px solid ${c}35`,
      fontFamily:"monospace",letterSpacing:1,whiteSpace:"nowrap"}}>
      {label}
    </span>
  );
}

function NodeCard({node,active,done,onClick}){
  const bg=node.layer==="INGESTION"?`${T.udf}06`:node.layer==="AI PROCESSING"?`${T.amber}06`:`${T.green}06`;
  return(
    <div onClick={onClick} style={{background:done?bg:T.card,
      border:`1px solid ${active?node.color:done?node.color+"50":T.border}`,
      borderRadius:8,padding:"10px 12px",cursor:"pointer",transition:"all 0.3s",
      boxShadow:active?`0 0 16px ${node.color}30`:"none"}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:5}}>
        <div style={{display:"flex",alignItems:"center",gap:7}}>
          <span style={{fontSize:15}}>{node.icon}</span>
          <div>
            <div style={{fontSize:11,fontWeight:700,color:done||active?node.color:T.text}}>{node.label}</div>
            <div style={{fontSize:8,color:T.muted,letterSpacing:1}}>{node.layer}</div>
          </div>
        </div>
        {done&&<span style={{color:T.green,fontSize:11}}>✓</span>}
        {active&&<PulseDot color={node.color}/>}
      </div>
      <div style={{fontSize:10,color:T.muted,lineHeight:1.5}}>{node.desc}</div>
    </div>
  );
}

// ── Live Report Display ───────────────────────────────────────

function LiveReport({report}){
  if(!report) return null;
  const proj=report.seat_projection||{};
  const momentum=report.overall_status||"—";
  const mc=momentum.includes("SURGING")||momentum.includes("LEADING")?T.green:
            momentum.includes("NECK")?T.amber:T.ldf;

  return(
    <div style={{display:"flex",flexDirection:"column",gap:12,animation:"pmFade 0.4s ease"}}>

      {/* Hero card */}
      <div style={{background:`linear-gradient(135deg,${T.udf}08,${T.panel})`,
        border:`1px solid ${T.udf}25`,borderRadius:10,padding:16}}>
        <div style={{display:"flex",justifyContent:"space-between",
          alignItems:"flex-start",flexWrap:"wrap",gap:12}}>
          <div>
            <div style={{fontSize:9,color:T.muted,letterSpacing:2,marginBottom:4}}>LATEST REPORT</div>
            <div style={{fontSize:14,fontWeight:700,color:T.udf}}>
              Run ID: {report.run_id||"—"}
            </div>
            <div style={{fontSize:9,color:T.muted,marginTop:3}}>
              {report.date} · {report.generated_at?.split("T")[1]?.slice(0,5)} IST
            </div>
            <div style={{marginTop:8}}><Chip label={momentum} color={mc}/></div>
          </div>
          <div style={{background:`${mc}12`,border:`1px solid ${mc}30`,
            borderRadius:8,padding:"10px 16px",textAlign:"center"}}>
            <div style={{fontSize:9,color:T.muted,marginBottom:3}}>UDF MAJORITY CONFIDENCE</div>
            <div style={{fontSize:28,fontWeight:800,color:mc,fontFamily:"monospace"}}>
              {report.majority_confidence}%
            </div>
          </div>
        </div>
      </div>

      {/* Seat projection */}
      <div style={{background:T.card,border:`1px solid ${T.border}`,borderRadius:8,padding:14}}>
        <div style={{fontSize:9,color:T.muted,letterSpacing:2,textTransform:"uppercase",marginBottom:12}}>
          SEAT PROJECTION — AI COMPUTED
        </div>
        {[["UDF",proj.udf,T.udf],["LDF",proj.ldf,T.ldf],["NDA",proj.nda,T.nda]].map(([l,v,c])=>(
          <div key={l} style={{marginBottom:10}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}>
              <span style={{fontSize:11,color:T.text}}>{l}</span>
              <span style={{fontSize:19,fontWeight:800,color:c,fontFamily:"monospace"}}>{v??"—"}</span>
            </div>
            <Bar val={v||0} max={140} color={c} height={7}/>
          </div>
        ))}
        <div style={{textAlign:"right",marginTop:4}}>
          <span style={{fontSize:9,color:"#FFD600"}}>━ Majority: 71 of 140</span>
        </div>
      </div>

      {/* Narrative clusters */}
      {report.topic_clusters?.length>0&&(
        <div style={{background:T.card,border:`1px solid ${T.border}`,borderRadius:8,padding:14}}>
          <div style={{fontSize:9,color:T.muted,letterSpacing:2,textTransform:"uppercase",marginBottom:10}}>
            NARRATIVE CLUSTERS TODAY
          </div>
          {report.topic_clusters.slice(0,5).map((c,i)=>{
            const fc=c.front_benefiting==="UDF"?T.udf:c.front_benefiting==="LDF"?T.ldf:T.muted;
            const mc2=c.momentum==="RISING"?T.green:c.momentum==="FALLING"?T.ldf:T.amber;
            return(
              <div key={i} style={{marginBottom:9,padding:"8px 10px",
                background:`${fc}06`,borderRadius:6,border:`1px solid ${fc}18`}}>
                <div style={{display:"flex",justifyContent:"space-between",
                  alignItems:"center",marginBottom:4}}>
                  <span style={{fontSize:11,fontWeight:700,color:fc}}>{c.theme}</span>
                  <div style={{display:"flex",gap:5}}>
                    <span style={{fontSize:8,color:mc2,border:`1px solid ${mc2}40`,
                      borderRadius:10,padding:"1px 6px",background:`${mc2}12`}}>
                      {c.momentum}
                    </span>
                    <span style={{fontSize:8,color:T.muted,fontFamily:"monospace"}}>{c.front_benefiting}</span>
                  </div>
                </div>
                <div style={{fontSize:10,color:T.muted,lineHeight:1.5}}>
                  {c.narrative?.slice(0,130)}...
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Risk alerts */}
      {report.top_risks?.length>0&&(
        <div style={{background:T.card,border:`1px solid ${T.border}`,borderRadius:8,padding:14}}>
          <div style={{fontSize:9,color:T.muted,letterSpacing:2,textTransform:"uppercase",marginBottom:10}}>
            RISK ALERTS
          </div>
          {report.top_risks.map((r,i)=>{
            const rc=r.severity==="CRITICAL"?"#FF3F3F":r.severity==="HIGH"?T.nda:T.amber;
            return(
              <div key={i} style={{marginBottom:8,padding:"9px 11px",
                background:`${rc}08`,borderRadius:6,border:`1px solid ${rc}22`}}>
                <div style={{display:"flex",justifyContent:"space-between",
                  alignItems:"center",marginBottom:5}}>
                  <span style={{fontSize:11,fontWeight:700,color:rc}}>
                    {r.severity==="CRITICAL"?"🔴":"🟡"} {r.title}
                  </span>
                  <Chip label={r.severity} color={rc}/>
                </div>
                {r.description&&(
                  <div style={{fontSize:10,color:T.muted,lineHeight:1.5,marginBottom:5}}>
                    {r.description.slice(0,150)}
                  </div>
                )}
                {r.counter_action&&(
                  <div style={{fontSize:9,color:T.green}}>
                    → {r.counter_action.slice(0,120)}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Tactical playbook */}
      {report.action_playbook&&(
        <div style={{background:`${T.green}06`,border:`1px solid ${T.green}22`,
          borderRadius:8,padding:14}}>
          <div style={{fontSize:9,color:T.green,letterSpacing:2,
            textTransform:"uppercase",marginBottom:10}}>
            TODAY'S TACTICAL PLAYBOOK
          </div>
          {report.action_playbook.priority_message_of_day&&(
            <div style={{fontSize:12,fontWeight:700,color:T.text,lineHeight:1.6,
              fontStyle:"italic",marginBottom:12,padding:"8px 12px",
              background:`${T.udf}08`,borderRadius:6,border:`1px solid ${T.udf}20`}}>
              "{report.action_playbook.priority_message_of_day}"
            </div>
          )}
          {report.action_playbook.ground_actions?.priority_constituencies&&(
            <div style={{marginBottom:10}}>
              <div style={{fontSize:9,color:T.muted,marginBottom:6}}>PRIORITY SEATS</div>
              <div style={{display:"flex",gap:6,flexWrap:"wrap"}}>
                {report.action_playbook.ground_actions.priority_constituencies.map((s,i)=>(
                  <span key={i} style={{fontSize:10,padding:"3px 10px",borderRadius:20,
                    background:`${T.udf}15`,color:T.udf,border:`1px solid ${T.udf}30`}}>
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}
          {report.action_playbook.counter_narrative&&(
            <div style={{background:`${T.ldf}08`,borderRadius:6,
              padding:"8px 12px",border:`1px solid ${T.ldf}20`}}>
              <div style={{fontSize:9,color:T.ldf,marginBottom:4}}>COUNTER-NARRATIVE</div>
              <div style={{fontSize:10,color:T.text,fontStyle:"italic",lineHeight:1.6}}>
                "{report.action_playbook.counter_narrative}"
              </div>
            </div>
          )}
        </div>
      )}

      {/* Constituency scores - now shown in dedicated Map tab */}
      {report.constituency_scores?.length>0&&(
        <div style={{background:`${T.udf}08`,border:`1px solid ${T.udf}25`,
          borderRadius:8,padding:"10px 14px",display:"flex",
          alignItems:"center",justifyContent:"space-between"}}>
          <div>
            <div style={{fontSize:10,fontWeight:700,color:T.udf,marginBottom:3}}>
              🗺️ {report.constituency_scores.length} constituencies AI-scored
            </div>
            <div style={{fontSize:9,color:T.muted}}>
              View full analysis in the Constituency Map tab →
            </div>
          </div>
          <div style={{fontSize:24,fontWeight:800,color:T.udf,fontFamily:"monospace"}}>
            {report.constituency_scores.filter(s=>s.lean==="UDF").length} UDF
          </div>
        </div>
      )}

      <div style={{fontSize:9,color:T.dim,textAlign:"right"}}>
        Generated by Kerala 2026 War Room AI Pipeline · LangGraph + GPT-4o ·{" "}
        {report._meta?.total_reports} total reports archived
      </div>
    </div>
  );
}

// ═════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═════════════════════════════════════════════════════════════

export default function PipelineMonitor(){
  const [apiOk,setApiOk]           = useState(false);
  const [report,setReport]         = useState(null);
  const [reports,setReports]       = useState([]);
  const [pipeStatus,setPipeStatus] = useState(null);
  const [lastSync,setLastSync]     = useState(null);
  const [activeTab,setActiveTab]   = useState("report");
  const [simulating,setSimulating] = useState(false);
  const [activeNode,setActiveNode] = useState(null);
  const [doneNodes,setDoneNodes]   = useState([]);
  const [simLogs,setSimLogs]       = useState([]);
  const [selNode,setSelNode]       = useState(null);
  const [triggering,setTriggering] = useState(false);
  const logRef = useRef(null);

  // ── Fetch ────────────────────────────────────────────────

  const fetchAll = useCallback(async()=>{
    try{
      const h=await fetch(`${API}/api/health`,{signal:AbortSignal.timeout(3000)});
      if(!h.ok) throw new Error();
      setApiOk(true);
      const [rr,lr,sr]=await Promise.all([
        fetch(`${API}/api/latest-report`),
        fetch(`${API}/api/reports`),
        fetch(`${API}/api/pipeline/status`),
      ]);
      if(rr.ok) setReport(await rr.json());
      if(lr.ok){const d=await lr.json();setReports(d.reports||[]);}
      if(sr.ok) setPipeStatus(await sr.json());
      setLastSync(new Date());
    }catch{setApiOk(false);}
  },[]);

  useEffect(()=>{
    fetchAll();
    const id=setInterval(fetchAll,30000);
    return()=>clearInterval(id);
  },[fetchAll]);

  useEffect(()=>{
    if(logRef.current) logRef.current.scrollTop=logRef.current.scrollHeight;
  },[pipeStatus?.log]);

  // ── Trigger real run ──────────────────────────────────────

  const triggerRun=async()=>{
    if(!apiOk||triggering) return;
    setTriggering(true);
    try{
      await fetch(`${API}/api/pipeline/run`,{method:"POST"});
      setTimeout(fetchAll,2000);
    }finally{setTriggering(false);}
  };

  // ── Simulate ──────────────────────────────────────────────

  const simulate=async()=>{
    setSimulating(true);setDoneNodes([]);setSimLogs([]);setActiveNode(null);
    for(let i=0;i<NODES.length;i++){
      const n=NODES[i];
      setActiveNode(n.id);
      await new Promise(r=>setTimeout(r,700+Math.random()*500));
      const log=MOCK_LOGS[i]||{node:n.id,status:"OK",msg:`${n.label} completed`};
      setSimLogs(p=>[...p,{...log,t:new Date().toTimeString().slice(0,8)}]);
      setDoneNodes(p=>[...p,n.id]);
      setActiveNode(null);
      await new Promise(r=>setTimeout(r,100));
    }
    setSimulating(false);
  };

  const TABS=["report","nodes","logs","history"];
  const TLABELS={report:"📊 Live Report",nodes:"⚙️ Nodes",logs:"📜 Logs",history:"📁 History"};

  return(
    <div style={{background:T.bg,color:T.text,fontFamily:"'Courier New',monospace",fontSize:13}}>
      <style>{`
        @keyframes pmPulse{0%{opacity:1}50%{opacity:0.3}100%{opacity:1}}
        @keyframes pmFade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
        @keyframes spin{to{transform:rotate(360deg)}}
        ::-webkit-scrollbar{width:3px;height:3px;background:${T.bg}}
        ::-webkit-scrollbar-thumb{background:${T.dim};border-radius:3px}
      `}</style>

      {/* Sub-header */}
      <div style={{background:"#070F1E",borderBottom:`1px solid ${T.border}`,
        padding:"10px 18px",display:"flex",alignItems:"center",
        justifyContent:"space-between",flexWrap:"wrap",gap:10}}>
        <div>
          <div style={{fontSize:13,fontWeight:700,letterSpacing:2,color:T.udf}}>
            ⚙️ PIPELINE MONITOR — LIVE INTELLIGENCE FEED
          </div>
          <div style={{fontSize:9,color:T.muted,marginTop:2}}>
            Auto-refreshes every 30s · FastAPI bridge port 8000 · LangGraph + GPT-4o
          </div>
        </div>
        <div style={{display:"flex",gap:8,flexWrap:"wrap",alignItems:"center"}}>
          {/* API status */}
          <div style={{display:"flex",alignItems:"center",gap:6,
            background:apiOk?`${T.green}10`:`${T.ldf}10`,
            border:`1px solid ${apiOk?T.green+"30":"#FF3F3F30"}`,
            borderRadius:6,padding:"5px 10px"}}>
            <PulseDot color={apiOk?T.green:"#FF3F3F"}/>
            <span style={{fontSize:10,color:apiOk?T.green:"#FF6666",fontFamily:"monospace"}}>
              {apiOk?"FastAPI ONLINE · :8000":"FastAPI OFFLINE"}
            </span>
          </div>
          {lastSync&&<span style={{fontSize:9,color:T.dim}}>Synced {lastSync.toLocaleTimeString()}</span>}
          <button onClick={fetchAll} style={{padding:"5px 10px",borderRadius:5,
            background:"transparent",border:`1px solid ${T.border}`,
            color:T.muted,fontSize:9,cursor:"pointer",fontFamily:"monospace"}}>
            ↺ SYNC
          </button>
        </div>
      </div>

      {/* Offline banner */}
      {!apiOk&&(
        <div style={{background:"#FF3F3F08",borderBottom:`1px solid #FF3F3F20`,
          padding:"10px 18px"}}>
          <div style={{fontSize:11,color:"#FF8888",fontWeight:700,marginBottom:6}}>
            ⚠️ FastAPI bridge is offline — showing simulation mode only
          </div>
          <div style={{fontSize:10,color:T.muted,marginBottom:6}}>
            Open a NEW terminal in VS Code and run:
          </div>
          <div style={{background:"#010609",borderRadius:6,padding:"8px 14px",
            fontFamily:"monospace",fontSize:11,color:T.green,display:"inline-block"}}>
            cd pipeline &nbsp;&nbsp;&&nbsp;&nbsp; uvicorn api:app --reload --port 8000
          </div>
          <div style={{fontSize:9,color:T.dim,marginTop:6}}>
            Keep this running alongside npm run dev · Then click ↺ SYNC above
          </div>
        </div>
      )}

      {/* Live KPI strip */}
      {apiOk&&report&&(
        <div style={{display:"grid",
          gridTemplateColumns:"repeat(auto-fit,minmax(120px,1fr))",
          gap:1,background:T.border,animation:"pmFade 0.4s ease"}}>
          {[
            {l:"Momentum",  v:(report.overall_status||"—").replace(/_/g," "),
              c:report.overall_status?.includes("SURGING")||report.overall_status?.includes("LEADING")?T.green:T.amber},
            {l:"UDF Seats", v:report.seat_projection?.udf, c:T.udf},
            {l:"LDF Seats", v:report.seat_projection?.ldf, c:T.ldf},
            {l:"NDA Seats", v:report.seat_projection?.nda, c:T.nda},
            {l:"Confidence",v:`${report.majority_confidence}%`, c:T.green},
            {l:"Risks",     v:report.top_risks?.length||0, c:"#FF6666"},
          ].map((k,i)=>(
            <div key={i} style={{background:T.panel,padding:"10px 12px"}}>
              <div style={{fontSize:8,color:T.muted,textTransform:"uppercase",
                letterSpacing:1,marginBottom:3}}>{k.l}</div>
              <div style={{fontSize:17,fontWeight:800,color:k.c,
                fontFamily:"monospace"}}>{k.v??"—"}</div>
            </div>
          ))}
        </div>
      )}

      {/* Tab bar + action buttons */}
      <div style={{background:"#070F1E",borderBottom:`1px solid ${T.border}`,
        padding:"0 18px",display:"flex",gap:0,overflowX:"auto",alignItems:"center"}}>
        {TABS.map(t=>(
          <button key={t} onClick={()=>setActiveTab(t)} style={{
            background:"none",border:"none",
            color:activeTab===t?T.udf:T.muted,
            padding:"10px 16px",fontSize:10,letterSpacing:2,
            textTransform:"uppercase",cursor:"pointer",
            borderBottom:activeTab===t?`2px solid ${T.udf}`:"2px solid transparent",
            transition:"all 0.2s",whiteSpace:"nowrap",
            fontFamily:"'Courier New',monospace"}}>
            {TLABELS[t]}
          </button>
        ))}
        <div style={{marginLeft:"auto",display:"flex",gap:6,padding:"0 4px"}}>
          {apiOk&&(
            <button onClick={triggerRun}
              disabled={triggering||pipeStatus?.status==="running"}
              style={{padding:"6px 14px",borderRadius:6,
                background:triggering||pipeStatus?.status==="running"?T.dim:`${T.green}18`,
                border:`1px solid ${triggering||pipeStatus?.status==="running"?T.dim:T.green+"40"}`,
                color:triggering||pipeStatus?.status==="running"?T.muted:T.green,
                fontSize:10,letterSpacing:1,cursor:"pointer",fontFamily:"monospace"}}>
              {pipeStatus?.status==="running"?"⚙️ RUNNING...":"▶ RUN PIPELINE"}
            </button>
          )}
          <button onClick={simulate} disabled={simulating}
            style={{padding:"6px 14px",borderRadius:6,
              background:simulating?T.dim:`${T.udf}15`,
              border:`1px solid ${simulating?T.dim:T.udf+"40"}`,
              color:simulating?T.muted:T.udf,
              fontSize:10,letterSpacing:1,cursor:"pointer",fontFamily:"monospace"}}>
            {simulating?"⚙️ SIMULATING...":"▷ SIMULATE"}
          </button>
        </div>
      </div>

      <div style={{padding:14}}>

        {/* ══ TAB: LIVE REPORT ══ */}
        {activeTab==="report"&&(
          apiOk&&report
            ? <LiveReport report={report}/>
            : <div style={{textAlign:"center",padding:50,color:T.muted}}>
                <div style={{fontSize:36,marginBottom:14}}>{apiOk?"📭":"🔌"}</div>
                <div style={{fontSize:13,marginBottom:8}}>
                  {apiOk?"No reports yet":"FastAPI bridge is offline"}
                </div>
                <div style={{fontSize:10,color:T.dim}}>
                  {apiOk
                    ?"Click ▶ RUN PIPELINE above, or run pipeline in terminal"
                    :"cd pipeline → uvicorn api:app --reload --port 8000"}
                </div>
              </div>
        )}

        {/* ══ TAB: NODES ══ */}
        {activeTab==="nodes"&&(
          <div>
            <div style={{display:"flex",gap:10,marginBottom:12,
              flexWrap:"wrap",alignItems:"center"}}>
              {[["INGESTION",T.udf],["AI PROCESSING",T.amber],
                ["DECISION",T.green],["OUTPUT",T.green]].map(([l,c])=>(
                <div key={l} style={{display:"flex",alignItems:"center",gap:5}}>
                  <div style={{width:7,height:7,borderRadius:2,background:c}}/>
                  <span style={{fontSize:9,color:T.muted}}>{l}</span>
                </div>
              ))}
              {simulating&&<div style={{marginLeft:"auto",display:"flex",
                alignItems:"center",gap:6}}>
                <PulseDot color={T.amber}/>
                <span style={{fontSize:9,color:T.amber}}>SIMULATING...</span>
              </div>}
            </div>
            <div style={{display:"grid",
              gridTemplateColumns:"repeat(auto-fill,minmax(250px,1fr))",gap:9}}>
              {NODES.map(n=>(
                <NodeCard key={n.id} node={n}
                  active={activeNode===n.id}
                  done={doneNodes.includes(n.id)}
                  onClick={()=>setSelNode(selNode?.id===n.id?null:n)}/>
              ))}
            </div>
            {selNode&&(
              <div style={{marginTop:12,background:`${selNode.color}08`,
                border:`1px solid ${selNode.color}30`,borderRadius:8,padding:14}}>
                <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:8}}>
                  <span style={{fontSize:18}}>{selNode.icon}</span>
                  <div style={{fontSize:13,fontWeight:700,color:selNode.color}}>
                    {selNode.label}
                  </div>
                  <Chip label={selNode.layer} color={selNode.color}/>
                </div>
                <div style={{background:"#010609",borderRadius:6,
                  padding:"10px 12px",fontFamily:"monospace",fontSize:10,color:"#7EC8E3"}}>
                  <span style={{color:"#FF7B72"}}>async def </span>
                  <span style={{color:"#79C0FF"}}>{selNode.id}</span>
                  <span style={{color:T.muted}}>(state: PipelineState) -{">"} dict:</span>
                  <br/><span style={{color:"#8B949E",paddingLeft:16}}>
                    # Node {NODES.findIndex(n=>n.id===selNode.id)+1} of {NODES.length} · Layer: {selNode.layer}
                  </span>
                  <br/><span style={{color:"#8B949E",paddingLeft:16}}>
                    # See: pipeline/kerala_intelligence_pipeline.py
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ══ TAB: LOGS ══ */}
        {activeTab==="logs"&&(
          <div>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12,marginBottom:12}}>
              {/* Simulated log */}
              <div>
                <div style={{fontSize:9,color:T.muted,letterSpacing:2,marginBottom:8}}>
                  SIMULATED LOG
                </div>
                <div style={{background:"#010609",border:`1px solid ${T.border}`,
                  borderRadius:8,padding:12,height:360,overflowY:"auto",
                  fontFamily:"monospace"}}>
                  {simLogs.length===0&&!simulating&&(
                    <div style={{color:T.dim,fontSize:10,textAlign:"center",marginTop:70}}>
                      Click ▷ SIMULATE to watch pipeline execute
                    </div>
                  )}
                  {simLogs.map((l,i)=>(
                    <div key={i} style={{marginBottom:5,display:"flex",gap:7,
                      alignItems:"flex-start",animation:"pmFade 0.3s ease"}}>
                      <span style={{color:T.dim,fontSize:9,flexShrink:0}}>{l.t}</span>
                      <span style={{fontSize:9,padding:"1px 5px",borderRadius:3,flexShrink:0,
                        background:l.status==="OK"?`${T.green}20`:`${T.nda}20`,
                        color:l.status==="OK"?T.green:T.nda}}>{l.status}</span>
                      <div>
                        <span style={{color:T.udf,fontSize:10}}>[{l.node}] </span>
                        <span style={{color:T.muted,fontSize:10}}>{l.msg}</span>
                      </div>
                    </div>
                  ))}
                  {simulating&&activeNode&&(
                    <div style={{display:"flex",gap:7,alignItems:"center",
                      animation:"pmPulse 0.8s infinite"}}>
                      <span style={{color:T.dim,fontSize:9}}>
                        {new Date().toTimeString().slice(0,8)}
                      </span>
                      <span style={{fontSize:9,padding:"1px 5px",borderRadius:3,
                        background:`${T.amber}20`,color:T.amber}}>RUN</span>
                      <span style={{color:T.amber,fontSize:10}}>[{activeNode}] running...</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Real pipeline log */}
              <div>
                <div style={{fontSize:9,color:T.muted,letterSpacing:2,marginBottom:8,
                  display:"flex",alignItems:"center",gap:8}}>
                  REAL PIPELINE LOG
                  {pipeStatus?.status&&<Chip label={pipeStatus.status.toUpperCase()}/>}
                </div>
                <div ref={logRef} style={{background:"#010609",
                  border:`1px solid ${T.border}`,borderRadius:8,padding:12,
                  height:360,overflowY:"auto",fontFamily:"monospace"}}>
                  {!apiOk&&(
                    <div style={{color:"#FF6666",fontSize:10,textAlign:"center",marginTop:70}}>
                      FastAPI offline.<br/>
                      <span style={{color:T.dim,fontSize:9}}>
                        Run: uvicorn api:app --reload --port 8000
                      </span>
                    </div>
                  )}
                  {apiOk&&!pipeStatus?.log?.length&&(
                    <div style={{color:T.dim,fontSize:10,textAlign:"center",marginTop:70}}>
                      Click ▶ RUN PIPELINE to start a real run
                    </div>
                  )}
                  {pipeStatus?.log?.map((line,i)=>(
                    <div key={i} style={{fontSize:10,marginBottom:3,lineHeight:1.5,
                      color:line.includes("ERROR")||line.includes("failed")?T.ldf:
                        line.includes("WARNING")?T.nda:
                        line.includes("COMPLETE")||line.includes("✅")?T.green:T.muted}}>
                      {line}
                    </div>
                  ))}
                  {pipeStatus?.status==="running"&&(
                    <div style={{display:"flex",alignItems:"center",gap:6,marginTop:4,
                      animation:"pmPulse 0.8s infinite"}}>
                      <div style={{width:8,height:8,borderRadius:"50%",
                        border:`1px solid ${T.amber}`,borderTop:"1px solid transparent",
                        animation:"spin 0.8s linear infinite"}}/>
                      <span style={{color:T.amber,fontSize:10}}>Pipeline running...</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* CLI commands */}
            <div style={{fontSize:9,color:T.muted,letterSpacing:2,marginBottom:8}}>
              CLI COMMANDS
            </div>
            {[
              {cmd:"uvicorn api:app --reload --port 8000",           desc:"Start FastAPI bridge (run from pipeline/ folder)"},
              {cmd:"python kerala_intelligence_pipeline.py --run-now",desc:"Run pipeline immediately"},
              {cmd:"python kerala_intelligence_pipeline.py --schedule 06:00",desc:"Schedule daily 6AM IST"},
              {cmd:"npm run pipeline:run",                            desc:"Run via npm from project root"},
            ].map((c,i)=>(
              <div key={i} style={{background:"#010609",border:`1px solid ${T.border}`,
                borderRadius:6,padding:"9px 12px",marginBottom:6}}>
                <div style={{fontSize:10,color:T.green,fontFamily:"monospace",marginBottom:3}}>
                  $ {c.cmd}
                </div>
                <div style={{fontSize:9,color:T.muted}}>{c.desc}</div>
              </div>
            ))}
          </div>
        )}

        {/* ══ TAB: HISTORY ══ */}
        {activeTab==="history"&&(
          !apiOk
            ? <div style={{textAlign:"center",padding:40,color:T.muted}}>
                <div style={{fontSize:32,marginBottom:12}}>🔌</div>
                <div>FastAPI required · uvicorn api:app --reload --port 8000</div>
              </div>
            : reports.length===0
            ? <div style={{textAlign:"center",padding:40,color:T.muted}}>
                <div style={{fontSize:32,marginBottom:12}}>📭</div>
                <div>No reports yet — run the pipeline first</div>
              </div>
            : <div>
                <div style={{fontSize:10,color:T.muted,marginBottom:12}}>
                  {reports.length} reports archived in pipeline/reports/
                </div>
                <div style={{display:"grid",
                  gridTemplateColumns:"repeat(auto-fill,minmax(270px,1fr))",gap:9}}>
                  {reports.map((r,i)=>(
                    <div key={i} style={{background:T.card,
                      border:`1px solid ${i===0?T.udf+"50":T.border}`,
                      borderRadius:8,padding:"12px 14px"}}>
                      <div style={{display:"flex",justifyContent:"space-between",
                        alignItems:"flex-start",marginBottom:7}}>
                        <div>
                          <div style={{fontSize:13,fontWeight:700,
                            color:i===0?T.udf:T.text}}>
                            {r.date} {i===0&&<span style={{fontSize:9,color:T.udf}}>(LATEST)</span>}
                          </div>
                          <div style={{fontSize:9,color:T.muted,marginTop:2}}>
                            Run: {r.run_id}
                          </div>
                        </div>
                        <div style={{fontSize:9,color:T.muted,fontFamily:"monospace"}}>
                          {r.size_kb} KB
                        </div>
                      </div>
                      <div style={{fontSize:9,color:T.dim,fontFamily:"monospace",
                        wordBreak:"break-all",marginBottom:5}}>{r.filename}</div>
                      <div style={{fontSize:9,color:T.muted}}>
                        {new Date(r.created_at).toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
        )}

      </div>
    </div>
  );
}
