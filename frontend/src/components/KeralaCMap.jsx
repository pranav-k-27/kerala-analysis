import { useState, useEffect, useCallback } from "react";

const T = {
  bg:"#03080F", panel:"#07111E", card:"#0B1929", border:"#162840",
  udf:"#00C8FF", ldf:"#FF3F3F", nda:"#FF9500",
  green:"#00E57A", amber:"#FFD600", muted:"#4A6A8A",
  text:"#D8EAF8", dim:"#2A4A6A", dark:"#050C1A",
};

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const DISTRICTS = [
  {name:"Kasaragod",         seats:5,  north:true  },
  {name:"Kannur",            seats:11, north:true  },
  {name:"Wayanad",           seats:3,  north:true  },
  {name:"Kozhikode",         seats:13, north:true  },
  {name:"Malappuram",        seats:16, north:true  },
  {name:"Palakkad",          seats:12, central:true},
  {name:"Thrissur",          seats:13, central:true},
  {name:"Ernakulam",         seats:14, central:true},
  {name:"Idukki",            seats:5,  central:true},
  {name:"Kottayam",          seats:9,  central:true},
  {name:"Alappuzha",         seats:9,  south:true  },
  {name:"Pathanamthitta",    seats:5,  south:true  },
  {name:"Kollam",            seats:11, south:true  },
  {name:"Thiruvananthapuram",seats:14, south:true  },
];

const DISTRICT_SVG = [
  {name:"Kasaragod",         x:60, y:10,  w:120, h:42 },
  {name:"Kannur",            x:50, y:54,  w:130, h:68 },
  {name:"Wayanad",           x:172,y:76,  w:78,  h:48 },
  {name:"Kozhikode",         x:40, y:124, w:130, h:62 },
  {name:"Malappuram",        x:50, y:188, w:140, h:68 },
  {name:"Palakkad",          x:132,y:200, w:118, h:78 },
  {name:"Thrissur",          x:48, y:258, w:140, h:58 },
  {name:"Ernakulam",         x:52, y:318, w:136, h:62 },
  {name:"Idukki",            x:162,y:288, w:94,  h:78 },
  {name:"Kottayam",          x:58, y:382, w:130, h:58 },
  {name:"Alappuzha",         x:34, y:442, w:108, h:52 },
  {name:"Pathanamthitta",    x:128,y:442, w:100, h:52 },
  {name:"Kollam",            x:42, y:496, w:122, h:58 },
  {name:"Thiruvananthapuram",x:38, y:556, w:130, h:62 },
];

const leanColor = l =>
  l==="UDF"?"#00C8FF":l==="LDF"?"#FF3F3F":l==="NDA"?"#FF9500":l==="SWING"?"#FFD600":T.muted;
const riskColor = r =>
  r==="CRITICAL"?"#FF3F3F":r==="HIGH"?"#FF9500":r==="MEDIUM"?"#FFD600":"#00E57A";

function PulseDot({color=T.green}){
  const [b,setB]=useState(true);
  useEffect(()=>{const t=setInterval(()=>setB(x=>!x),800);return()=>clearInterval(t);},[]);
  return <div style={{width:7,height:7,borderRadius:"50%",flexShrink:0,
    background:b?color:`${color}44`,boxShadow:b?`0 0 8px ${color}`:"none",transition:"all 0.4s"}}/>;
}

function Chip({label,color}){
  const c=color||T.muted;
  return <span style={{fontSize:9,padding:"2px 8px",borderRadius:20,
    background:`${c}18`,color:c,border:`1px solid ${c}35`,
    fontFamily:"monospace",letterSpacing:1,whiteSpace:"nowrap"}}>{label}</span>;
}

function DistrictMap({seats,selected,onSelect}){
  const [hov,setHov]=useState(null);

  // Compute district stats from live seat data
  const distStats={};
  DISTRICTS.forEach(d=>{
    const ds=seats.filter(s=>s.district===d.name||s.dist===d.name);
    const udfN=ds.filter(s=>s.lean==="UDF").length;
    const ldfN=ds.filter(s=>s.lean==="LDF").length;
    const swN=ds.filter(s=>s.lean==="SWING").length;
    const ndaN=ds.filter(s=>s.lean==="NDA").length;
    distStats[d.name]={udf:udfN,ldf:ldfN,swing:swN,nda:ndaN,total:ds.length,
      lean:udfN>=ldfN?"UDF":"LDF"};
  });

  return(
    <div>
      <div style={{fontSize:9,color:T.muted,textAlign:"center",marginBottom:8,letterSpacing:1}}>
        CLICK DISTRICT TO EXPLORE SEATS
      </div>
      <svg viewBox="0 0 270 630" style={{width:"100%",maxWidth:240,display:"block",margin:"0 auto"}}>
        {DISTRICT_SVG.map((d,i)=>{
          const stats=distStats[d.name]||{};
          const lean=stats.lean||"LDF";
          const c=leanColor(lean);
          const isSel=selected===d.name;
          const isHov=hov===d.name;
          return(
            <g key={i}
              onClick={()=>onSelect(isSel?null:d.name)}
              onMouseEnter={()=>setHov(d.name)}
              onMouseLeave={()=>setHov(null)}
              style={{cursor:"pointer"}}>
              <rect x={d.x} y={d.y} width={d.w} height={d.h} rx="4"
                fill={isSel?c:`${c}28`}
                stroke={isSel||hov===d.name?c:`${c}55`}
                strokeWidth={isSel?2:1}
                style={{transition:"all 0.2s",
                  filter:isSel?`drop-shadow(0 0 6px ${c}80)`:"none"}}/>
              <text x={d.x+d.w/2} y={d.y+d.h/2-6}
                textAnchor="middle" fontSize="7.5"
                fill={isSel?"#fff":c} fontFamily="monospace"
                fontWeight={isSel?"700":"400"}>
                {d.name.length>14?d.name.slice(0,13)+"…":d.name}
              </text>
              <text x={d.x+d.w/2} y={d.y+d.h/2+7}
                textAnchor="middle" fontSize="6.5"
                fill={isSel?"#ffffffaa":`${c}99`} fontFamily="monospace">
                {stats.udf||0}U · {stats.ldf||0}L · {stats.total||0}
              </text>
              {stats.swing>0&&(
                <g>
                  <circle cx={d.x+d.w-9} cy={d.y+9} r="6" fill={T.amber} opacity="0.9"/>
                  <text x={d.x+d.w-9} y={d.y+12} textAnchor="middle"
                    fontSize="7" fill="#000" fontFamily="monospace" fontWeight="700">
                    {stats.swing}
                  </text>
                </g>
              )}
            </g>
          );
        })}
        <g transform="translate(5,605)">
          {[["UDF",T.udf],["LDF",T.ldf],["NDA",T.nda],["SWING",T.amber]].map(([l,c],i)=>(
            <g key={i} transform={`translate(${i*62},0)`}>
              <rect width="10" height="10" rx="2" fill={`${c}40`} stroke={c} strokeWidth="1"/>
              <text x="13" y="9" fontSize="7" fill={c} fontFamily="monospace">{l}</text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
}

function SeatCell({seat,selected,onClick}){
  const c=leanColor(seat.lean);
  const rc=riskColor(seat.risk);
  const isSel=selected?.id===seat.id;
  const swingStr=seat.swing_vs_2021!=null
    ?(seat.swing_vs_2021>=0?"+":"")+seat.swing_vs_2021.toFixed(1)+"%"
    :"";
  return(
    <div onClick={()=>onClick(isSel?null:seat)}
      title={seat.name}
      style={{background:isSel?`${c}28`:`${c}10`,
        border:`1px solid ${isSel?c:c+"38"}`,
        borderRadius:4,padding:"5px 6px",cursor:"pointer",
        transition:"all 0.15s",
        boxShadow:isSel?`0 0 10px ${c}28`:"none",
        position:"relative"}}>
      {seat.risk!=="LOW"&&(
        <div style={{position:"absolute",top:2,right:2,
          width:5,height:5,borderRadius:"50%",background:rc}}/>
      )}
      <div style={{fontSize:9,fontWeight:700,color:c,lineHeight:1.3,marginBottom:2}}>
        {seat.name.length>12?seat.name.slice(0,11)+"…":seat.name}
      </div>
      <div style={{display:"flex",justifyContent:"space-between",
        fontSize:8,color:T.muted,fontFamily:"monospace"}}>
        <span style={{color:T.udf}}>{seat.udf}%</span>
        <span style={{color:T.ldf}}>{seat.ldf}%</span>
        <span style={{color:T.nda}}>{seat.nda}%</span>
      </div>
      {swingStr&&(
        <div style={{fontSize:7,color:seat.swing_vs_2021>=0?T.green:T.ldf,
          fontFamily:"monospace",marginTop:1}}>
          {swingStr} vs '21
        </div>
      )}
    </div>
  );
}

function SeatDetail({ seat, onClose }) {
  if (!seat) return null;

  const T = {
    bg:"#03080F", panel:"#07111E", card:"#0B1929", border:"#162840",
    udf:"#00C8FF", ldf:"#FF3F3F", nda:"#FF9500",
    green:"#00E57A", amber:"#FFD600", muted:"#4A6A8A",
    text:"#D8EAF8", dim:"#2A4A6A", dark:"#050C1A",
  };

  const leanColor = l =>
    l==="UDF"?T.udf:l==="LDF"?T.ldf:l==="NDA"?T.nda:l==="SWING"?T.amber:T.muted;
  const riskColor = r =>
    r==="CRITICAL"?T.ldf:r==="HIGH"?T.nda:r==="MEDIUM"?T.amber:T.green;

  const c  = leanColor(seat.lean);
  const rc = riskColor(seat.risk);

  return (
    <div style={{
      background: T.panel,
      border: `1px solid ${c}40`,
      borderRadius: 10, padding: 18, marginTop: 14,
      boxShadow: `0 0 24px ${c}18`,
      animation: "sdetFade 0.3s ease",
    }}>
      <style>{`@keyframes sdetFade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}`}</style>

      {/* ── Header ── */}
      <div style={{ display:"flex", justifyContent:"space-between",
        alignItems:"flex-start", marginBottom:16 }}>
        <div>
          <div style={{ fontSize:18, fontWeight:800, color:c,
            marginBottom:3 }}>{seat.name}</div>
          <div style={{ fontSize:10, color:T.muted }}>
            {seat.district || seat.dist} · Constituency #{seat.id}
          </div>
        </div>
        <button onClick={onClose} style={{ background:"none", border:"none",
          color:T.muted, fontSize:18, cursor:"pointer", padding:"0 4px" }}>✕</button>
      </div>

      {/* ── Stats row ── */}
      <div style={{ display:"grid",
        gridTemplateColumns:"repeat(auto-fit,minmax(100px,1fr))",
        gap:8, marginBottom:16 }}>
        {[
          { l:"UDF WIN PROB",    v:`${seat.win_prob_udf||seat.udf}%`, c },
          { l:"RISK LEVEL",      v:seat.risk,                         c:rc },
          { l:"SWING vs 2021",   v:(seat.swing_vs_2021!=null
              ?(seat.swing_vs_2021>=0?"+":"")+seat.swing_vs_2021.toFixed(1)+"%"
              :"N/A"),
            c:seat.swing_vs_2021>=0?T.green:T.ldf },
          { l:"INCUMBENT",       v:seat.incumbent||"LDF",
            c:leanColor(seat.incumbent||"LDF") },
        ].map((k,i)=>(
          <div key={i} style={{ background:`${k.c}08`,
            border:`1px solid ${k.c}25`, borderRadius:7,
            padding:"9px 12px", textAlign:"center" }}>
            <div style={{ fontSize:8, color:T.muted, letterSpacing:1,
              marginBottom:4, textTransform:"uppercase" }}>{k.l}</div>
            <div style={{ fontSize:16, fontWeight:800, color:k.c,
              fontFamily:"monospace" }}>{k.v}</div>
          </div>
        ))}
      </div>

      {/* ── Candidate Names ── */}
      {(seat.candidate_udf || seat.candidate_ldf || seat.candidate_nda) && (
        <div style={{ background:T.dark, borderRadius:8,
          padding:"10px 14px", marginBottom:14,
          border:`1px solid ${T.border}` }}>
          <div style={{ fontSize:9, color:T.muted, letterSpacing:2,
            textTransform:"uppercase", marginBottom:8 }}>
            🏃 CANDIDATES 2026
          </div>
          <div style={{ display:"grid",
            gridTemplateColumns:"repeat(3,1fr)", gap:8 }}>
            {[
              ["UDF", seat.candidate_udf, T.udf],
              ["LDF", seat.candidate_ldf, T.ldf],
              ["NDA", seat.candidate_nda, T.nda],
            ].map(([party, name, col])=>(
              <div key={party} style={{ background:`${col}0A`,
                border:`1px solid ${col}30`, borderRadius:6,
                padding:"7px 10px" }}>
                <div style={{ fontSize:8, color:col, fontWeight:700,
                  letterSpacing:1, marginBottom:3 }}>{party}</div>
                <div style={{ fontSize:10, color:T.text,
                  lineHeight:1.4 }}>{name || "TBA"}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Vote share bars ── */}
      <div style={{ marginBottom:14 }}>
        <div style={{ fontSize:9, color:T.muted, letterSpacing:2,
          textTransform:"uppercase", marginBottom:8 }}>
          AI-COMPUTED VOTE SHARE
        </div>
        {[["UDF",seat.udf,T.udf],["LDF",seat.ldf,T.ldf],["NDA",seat.nda,T.nda]].map(([l,v,col])=>(
          <div key={l} style={{ marginBottom:8 }}>
            <div style={{ display:"flex", justifyContent:"space-between",
              marginBottom:3 }}>
              <span style={{ fontSize:10, color:col }}>{l}</span>
              <span style={{ fontSize:12, fontWeight:700, color:col,
                fontFamily:"monospace" }}>{v}%</span>
            </div>
            <div style={{ height:5, background:T.dim, borderRadius:3,
              overflow:"hidden" }}>
              <div style={{ width:`${v}%`, height:"100%", background:col,
                boxShadow:`0 0 6px ${col}60`,
                transition:"width 0.8s ease" }}/>
            </div>
          </div>
        ))}
      </div>

      {/* ── Community Composition ── */}
      <div style={{ background:T.dark, borderRadius:8,
        padding:"10px 14px", marginBottom:14,
        border:`1px solid ${T.border}` }}>
        <div style={{ fontSize:9, color:T.muted, letterSpacing:2,
          textTransform:"uppercase", marginBottom:8 }}>
          👥 COMMUNITY COMPOSITION
        </div>
        <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
          {[
            ["Minority",  seat.minority_pct,  T.udf   ],
            ["Ezhava",    seat.ezhava_pct,     T.nda   ],
            ["Nair",      seat.nair_pct,       "#AA88FF"],
            ["Christian", seat.christian_pct,  T.green  ],
            ["SC/ST",     seat.sc_st_pct,      T.amber  ],
          ].filter(([,v])=>v).map(([label,val,col])=>(
            <div key={label} style={{ background:`${col}10`,
              border:`1px solid ${col}30`, borderRadius:20,
              padding:"3px 10px", display:"flex",
              alignItems:"center", gap:5 }}>
              <span style={{ fontSize:9, color:col }}>{label}</span>
              <span style={{ fontSize:10, fontWeight:700, color:col,
                fontFamily:"monospace" }}>{val}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Prediction Rationale ── */}
      {seat.rationale && (
        <div style={{ background:`${c}08`,
          border:`1px solid ${c}25`, borderRadius:8,
          padding:"10px 14px", marginBottom:14 }}>
          <div style={{ fontSize:9, color:c, letterSpacing:2,
            textTransform:"uppercase", marginBottom:6 }}>
            🧠 PREDICTION RATIONALE
          </div>
          <div style={{ fontSize:11, color:T.text, lineHeight:1.7 }}>
            {seat.rationale}
          </div>
        </div>
      )}

      {/* ── Local Issues ── */}
      {seat.local_issues?.length > 0 && (
        <div style={{ background:T.dark, borderRadius:8,
          padding:"10px 14px", marginBottom:14,
          border:`1px solid ${T.border}` }}>
          <div style={{ fontSize:9, color:T.muted, letterSpacing:2,
            textTransform:"uppercase", marginBottom:8 }}>
            📍 LOCAL POLITICAL ISSUES
          </div>
          {seat.local_issues.filter(Boolean).map((issue, i) => (
            <div key={i} style={{ display:"flex", gap:8,
              alignItems:"flex-start", marginBottom:7 }}>
              <div style={{ width:20, height:20, borderRadius:5,
                background:`${T.amber}18`,
                border:`1px solid ${T.amber}30`,
                display:"flex", alignItems:"center",
                justifyContent:"center", flexShrink:0,
                fontSize:10, color:T.amber,
                fontWeight:700 }}>{i+1}</div>
              <div style={{ fontSize:11, color:T.text,
                lineHeight:1.5 }}>{issue}</div>
            </div>
          ))}
        </div>
      )}

      {/* ── War Room Action ── */}
      <div style={{ background:`${T.green}08`,
        border:`1px solid ${T.green}25`, borderRadius:8,
        padding:"10px 14px" }}>
        <div style={{ fontSize:9, color:T.green, letterSpacing:2,
          textTransform:"uppercase", marginBottom:6 }}>
          ⚡ WAR ROOM ACTION
        </div>
        <div style={{ fontSize:11, color:T.text, lineHeight:1.7 }}>
          {seat.war_room_action ||
            (seat.risk==="CRITICAL"
              ? "⚡ URGENT: Deploy star campaigner immediately. Counter NDA spoiler with bipolar messaging."
              : seat.risk==="HIGH"
              ? `🎯 Priority seat. ${seat.lean==="UDF"?"Protect lead — boost turnout.":"Within striking range — surge resources."}`
              : seat.lean==="UDF"
              ? "✅ Safe UDF. Maintain ground presence and ensure voter turnout."
              : "📊 LDF hold. Monitor for late swing — reallocate resources if needed.")}
        </div>
      </div>

    </div>
  );
}

export default function KeralaCMap(){
  const [seats,setSeats]         = useState([]);
  const [summary,setSummary]     = useState(null);
  const [loading,setLoading]     = useState(true);
  const [apiOk,setApiOk]         = useState(false);
  const [lastSync,setLastSync]   = useState(null);
  const [runDate,setRunDate]     = useState(null);
  const [selDist,setSelDist]     = useState(null);
  const [selSeat,setSelSeat]     = useState(null);
  const [viewMode,setViewMode]   = useState("map");
  const [filterLean,setFilterLean] = useState("ALL");
  const [filterRisk,setFilterRisk] = useState("ALL");
  const [search,setSearch]       = useState("");

  const fetchSeats = useCallback(async()=>{
    try{
      const h=await fetch(`${API}/api/health`,{signal:AbortSignal.timeout(3000)});
      if(!h.ok) throw new Error();
      setApiOk(true);
      const res=await fetch(`${API}/api/constituencies`);
      if(res.ok){
        const data=await res.json();
        setSeats(data.seats||[]);
        setSummary(data.summary||null);
        setRunDate(data.date||null);
        setLastSync(new Date());
      }
    }catch{
      setApiOk(false);
    }finally{
      setLoading(false);
    }
  },[]);

  useEffect(()=>{
    fetchSeats();
    const id=setInterval(fetchSeats,60000);
    return()=>clearInterval(id);
  },[fetchSeats]);

  const getSeatField=(s,f)=>s[f]??s[f.replace("district","dist")]??null;

  const distSeats = selDist
    ? seats.filter(s=>(s.district||s.dist)===selDist)
    : seats;

  const filtered = distSeats.filter(s=>{
    const ml=filterLean==="ALL"||s.lean===filterLean;
    const mr=filterRisk==="ALL"||s.risk===filterRisk;
    const ms=search===""||
      s.name.toLowerCase().includes(search.toLowerCase())||
      (s.district||s.dist||"").toLowerCase().includes(search.toLowerCase());
    return ml&&mr&&ms;
  });

  const stats = summary || {
    udf_leading:seats.filter(s=>s.lean==="UDF").length,
    ldf_leading:seats.filter(s=>s.lean==="LDF").length,
    nda_leading:seats.filter(s=>s.lean==="NDA").length,
    swing:seats.filter(s=>s.lean==="SWING").length,
    critical:seats.filter(s=>s.risk==="CRITICAL").length,
    high_risk:seats.filter(s=>s.risk==="HIGH").length,
    majority_needed:71,
  };

  return(
    <div style={{background:T.bg,color:T.text,fontFamily:"'Courier New',monospace",fontSize:13}}>
      <style>{`
        ::-webkit-scrollbar{width:3px;height:3px;background:${T.bg}}
        ::-webkit-scrollbar-thumb{background:${T.dim};border-radius:3px}
        @keyframes mapFade{from{opacity:0}to{opacity:1}}
      `}</style>

      {/* Sub-header */}
      <div style={{background:"#070F1E",borderBottom:`1px solid ${T.border}`,
        padding:"10px 18px",display:"flex",alignItems:"center",
        justifyContent:"space-between",flexWrap:"wrap",gap:10}}>
        <div>
          <div style={{fontSize:13,fontWeight:700,letterSpacing:2,color:T.udf}}>
            🗺️ KERALA CONSTITUENCY MAP — 140 SEATS
          </div>
          <div style={{fontSize:9,color:T.muted,marginTop:2}}>
            {apiOk&&seats.length>0
              ? `AI-scored · Pipeline run: ${runDate||"today"} · Auto-refreshes every 60s`
              : "Connect FastAPI bridge for live AI scores"}
          </div>
        </div>
        <div style={{display:"flex",gap:8,flexWrap:"wrap",alignItems:"center"}}>
          <div style={{display:"flex",alignItems:"center",gap:6,
            background:apiOk&&seats.length>0?`${T.green}10`:`${T.amber}10`,
            border:`1px solid ${apiOk&&seats.length>0?T.green+"30":T.amber+"30"}`,
            borderRadius:6,padding:"5px 10px"}}>
            <PulseDot color={apiOk&&seats.length>0?T.green:T.amber}/>
            <span style={{fontSize:10,fontFamily:"monospace",
              color:apiOk&&seats.length>0?T.green:T.amber}}>
              {apiOk&&seats.length>0?"AI SCORES LIVE":"WAITING FOR PIPELINE"}
            </span>
          </div>
          {lastSync&&<span style={{fontSize:9,color:T.dim}}>
            Synced {lastSync.toLocaleTimeString()}
          </span>}
          <button onClick={fetchSeats} style={{padding:"5px 10px",borderRadius:5,
            background:"transparent",border:`1px solid ${T.border}`,
            color:T.muted,fontSize:9,cursor:"pointer",fontFamily:"monospace"}}>
            ↺ REFRESH
          </button>
          {[["map","🗺️ Map"],["grid","⊞ Grid"],["list","☰ List"]].map(([m,l])=>(
            <button key={m} onClick={()=>setViewMode(m)}
              style={{padding:"5px 10px",borderRadius:5,
                background:viewMode===m?`${T.udf}18`:"transparent",
                border:`1px solid ${viewMode===m?T.udf+"40":T.border}`,
                color:viewMode===m?T.udf:T.muted,
                fontSize:9,cursor:"pointer",fontFamily:"monospace"}}>
              {l}
            </button>
          ))}
        </div>
      </div>

      {/* Offline banner */}
      {!apiOk&&(
        <div style={{background:"#FF3F3F08",borderBottom:`1px solid #FF3F3F20`,
          padding:"10px 18px"}}>
          <div style={{fontSize:11,color:"#FF8888",fontWeight:700,marginBottom:6}}>
            ⚠️ FastAPI bridge offline — run pipeline first for AI scores
          </div>
          <div style={{background:"#010609",borderRadius:5,padding:"6px 12px",
            fontFamily:"monospace",fontSize:11,color:T.green,display:"inline-block"}}>
            cd pipeline &nbsp;&&nbsp; uvicorn api:app --reload --port 8000 &nbsp;&nbsp;then&nbsp;&nbsp;
            python kerala_intelligence_pipeline.py --run-now
          </div>
        </div>
      )}

      {/* KPI Strip */}
      <div style={{display:"grid",
        gridTemplateColumns:"repeat(auto-fit,minmax(95px,1fr))",
        gap:1,background:T.border}}>
        {[
          {l:"Total Seats",  v:seats.length||140,    c:T.text  },
          {l:"UDF Leading",  v:stats.udf_leading,    c:T.udf   },
          {l:"LDF Leading",  v:stats.ldf_leading,    c:T.ldf   },
          {l:"NDA Leading",  v:stats.nda_leading,    c:T.nda   },
          {l:"SWING",        v:stats.swing,           c:T.amber },
          {l:"CRITICAL",     v:stats.critical,        c:T.ldf   },
          {l:"HIGH RISK",    v:stats.high_risk,       c:T.nda   },
          {l:"MAJORITY",     v:stats.majority_needed||71,c:"#FFD600"},
        ].map((k,i)=>(
          <div key={i} style={{background:T.panel,padding:"10px 12px"}}>
            <div style={{fontSize:8,color:T.muted,textTransform:"uppercase",
              letterSpacing:1,marginBottom:3}}>{k.l}</div>
            <div style={{fontSize:18,fontWeight:800,color:k.c,
              fontFamily:"monospace"}}>{k.v??0}</div>
          </div>
        ))}
      </div>

      {/* Loading */}
      {loading&&(
        <div style={{textAlign:"center",padding:60}}>
          <div style={{width:36,height:36,borderRadius:"50%",
            border:`2px solid ${T.border}`,borderTop:`2px solid ${T.udf}`,
            animation:"spin 1s linear infinite",margin:"0 auto 16px"}}/>
          <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
          <div style={{fontSize:12,color:T.muted}}>Loading constituency data...</div>
        </div>
      )}

      {/* Filters */}
      {!loading&&(
        <div style={{background:"#070F1E",borderBottom:`1px solid ${T.border}`,
          padding:"8px 18px",display:"flex",
          alignItems:"center",gap:8,flexWrap:"wrap"}}>
          <div style={{display:"flex",gap:3}}>
            {["ALL","UDF","LDF","NDA","SWING"].map(l=>(
              <button key={l} onClick={()=>setFilterLean(l)}
                style={{padding:"4px 10px",borderRadius:20,
                  background:filterLean===l?`${leanColor(l)}22`:"transparent",
                  border:`1px solid ${filterLean===l?leanColor(l)+"50":T.border}`,
                  color:filterLean===l?leanColor(l):T.muted,
                  fontSize:9,cursor:"pointer",fontFamily:"monospace"}}>
                {l}
              </button>
            ))}
          </div>
          <div style={{width:1,height:20,background:T.border}}/>
          {["ALL","CRITICAL","HIGH","MEDIUM"].map(r=>(
            <button key={r} onClick={()=>setFilterRisk(r)}
              style={{padding:"4px 10px",borderRadius:20,
                background:filterRisk===r?`${riskColor(r)}18`:"transparent",
                border:`1px solid ${filterRisk===r?riskColor(r)+"50":T.border}`,
                color:filterRisk===r?riskColor(r):T.muted,
                fontSize:9,cursor:"pointer",fontFamily:"monospace"}}>
              {r}
            </button>
          ))}
          <div style={{marginLeft:"auto"}}>
            <input type="text" placeholder="Search seat..."
              value={search} onChange={e=>setSearch(e.target.value)}
              style={{padding:"5px 12px",background:T.card,
                border:`1px solid ${T.border}`,borderRadius:6,
                color:T.text,fontSize:10,fontFamily:"monospace",
                outline:"none",width:160}}/>
          </div>
        </div>
      )}

      {!loading&&(
        <div style={{padding:14}}>
          {/* MAP + GRID */}
          {(viewMode==="map"||viewMode==="grid")&&(
            <div style={{display:"grid",
              gridTemplateColumns:viewMode==="map"?"240px 1fr":"1fr",
              gap:16,alignItems:"start"}}>
              {/* District SVG map */}
              {viewMode==="map"&&(
                <div style={{position:"sticky",top:90}}>
                  <DistrictMap seats={seats}
                    selected={selDist}
                    onSelect={d=>{setSelDist(d);setSelSeat(null);}}/>
                  {selDist&&(
                    <button onClick={()=>{setSelDist(null);setSelSeat(null);}}
                      style={{width:"100%",marginTop:8,padding:"6px",
                        background:"transparent",border:`1px solid ${T.border}`,
                        color:T.muted,fontSize:9,cursor:"pointer",
                        borderRadius:6,fontFamily:"monospace"}}>
                      ✕ Clear ({selDist})
                    </button>
                  )}
                </div>
              )}

              {/* Seat grid */}
              <div>
                {viewMode==="map"&&!selDist&&(
                  <div style={{textAlign:"center",padding:40,color:T.muted,fontSize:11}}>
                    <div style={{fontSize:28,marginBottom:8}}>👈</div>
                    Click a district on the map to explore its seats
                  </div>
                )}

                {(selDist||viewMode==="grid")&&(
                  <>
                    {selDist&&(
                      <div style={{marginBottom:10}}>
                        <div style={{fontSize:12,fontWeight:700,color:T.udf,marginBottom:4}}>
                          {selDist}
                        </div>
                        <div style={{display:"flex",gap:10,fontSize:10}}>
                          <span style={{color:T.udf}}>UDF: {distSeats.filter(s=>s.lean==="UDF").length}</span>
                          <span style={{color:T.ldf}}>LDF: {distSeats.filter(s=>s.lean==="LDF").length}</span>
                          <span style={{color:T.amber}}>Swing: {distSeats.filter(s=>s.lean==="SWING").length}</span>
                        </div>
                      </div>
                    )}
                    <div style={{fontSize:9,color:T.muted,marginBottom:8,letterSpacing:1}}>
                      {filtered.length} SEATS
                      {seats.length>0&&" · AI SCORED"}
                      {apiOk&&runDate&&` · Run: ${runDate}`}
                    </div>

                    {viewMode==="grid"&&!selDist
                      ? DISTRICTS.map(dist=>{
                          const ds=filtered.filter(s=>(s.district||s.dist)===dist.name);
                          if(!ds.length) return null;
                          return(
                            <div key={dist.name} style={{marginBottom:16}}>
                              <div style={{fontSize:11,fontWeight:700,color:T.muted,
                                marginBottom:6,display:"flex",alignItems:"center",gap:8}}>
                                <span>{dist.name}</span>
                                <span style={{fontSize:9,color:T.dim}}>{ds.length} seats</span>
                              </div>
                              <div style={{display:"grid",
                                gridTemplateColumns:"repeat(auto-fill,minmax(130px,1fr))",gap:5}}>
                                {ds.map(s=><SeatCell key={s.id} seat={s}
                                  selected={selSeat} onClick={x=>setSelSeat(x)}/>)}
                              </div>
                            </div>
                          );
                        })
                      :(
                        <div style={{display:"grid",
                          gridTemplateColumns:"repeat(auto-fill,minmax(130px,1fr))",gap:5}}>
                          {filtered.map(s=><SeatCell key={s.id} seat={s}
                            selected={selSeat} onClick={x=>setSelSeat(x)}/>)}
                        </div>
                      )
                    }
                    <SeatDetail seat={selSeat} onClose={()=>setSelSeat(null)}/>
                  </>
                )}
              </div>
            </div>
          )}

          {/* LIST view */}
          {viewMode==="list"&&(
            <div>
              <div style={{fontSize:9,color:T.muted,marginBottom:10}}>
                {filtered.length} seats
                {seats.length>0&&" · AI-scored"}
              </div>
              <div style={{overflowX:"auto"}}>
                <table style={{width:"100%",borderCollapse:"collapse",fontSize:11}}>
                  <thead>
                    <tr style={{borderBottom:`1px solid ${T.border}`}}>
                      {["#","Constituency","District","Lean","UDF%","LDF%","NDA%",
                        "Win Prob","Swing vs'21","Risk","Incumbent","Action"].map(h=>(
                        <th key={h} style={{textAlign:"left",padding:"7px 8px",
                          fontSize:8,color:T.muted,textTransform:"uppercase",
                          letterSpacing:1,whiteSpace:"nowrap"}}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((s,i)=>{
                      const lc=leanColor(s.lean);
                      const rc=riskColor(s.risk);
                      return(
                        <tr key={s.id}
                          onClick={()=>setSelSeat(selSeat?.id===s.id?null:s)}
                          style={{borderBottom:`1px solid ${T.border}12`,
                            background:selSeat?.id===s.id?`${lc}10`:i%2===0?"transparent":T.dark+"44",
                            cursor:"pointer"}}>
                          <td style={{padding:"7px 8px",color:T.dim,fontFamily:"monospace"}}>{s.id}</td>
                          <td style={{padding:"7px 8px",fontWeight:700,color:lc}}>{s.name}</td>
                          <td style={{padding:"7px 8px",color:T.muted}}>{s.district||s.dist}</td>
                          <td style={{padding:"7px 8px"}}>
                            <span style={{fontSize:9,padding:"2px 7px",borderRadius:20,
                              background:`${lc}18`,color:lc,border:`1px solid ${lc}35`,
                              fontFamily:"monospace"}}>{s.lean}</span>
                          </td>
                          <td style={{padding:"7px 8px",color:T.udf,fontFamily:"monospace",fontWeight:700}}>{s.udf}%</td>
                          <td style={{padding:"7px 8px",color:T.ldf,fontFamily:"monospace"}}>{s.ldf}%</td>
                          <td style={{padding:"7px 8px",color:T.nda,fontFamily:"monospace"}}>{s.nda}%</td>
                          <td style={{padding:"7px 8px",color:lc,fontFamily:"monospace",fontWeight:700}}>
                            {s.win_prob_udf??s.udf}%
                          </td>
                          <td style={{padding:"7px 8px",fontFamily:"monospace",
                            color:s.swing_vs_2021>=0?T.green:T.ldf}}>
                            {s.swing_vs_2021!=null
                              ?(s.swing_vs_2021>=0?"+":"")+s.swing_vs_2021.toFixed(1)+"%"
                              :"—"}
                          </td>
                          <td style={{padding:"7px 8px"}}>
                            <span style={{fontSize:9,color:rc,fontFamily:"monospace"}}>{s.risk}</span>
                          </td>
                          <td style={{padding:"7px 8px",color:leanColor(s.incumbent||"LDF"),
                            fontFamily:"monospace"}}>{s.incumbent||"LDF"}</td>
                          <td style={{padding:"7px 8px",fontSize:9,color:T.muted}}>
                            {s.risk==="CRITICAL"?"⚡ NOW":s.risk==="HIGH"?"🎯 Priority":
                             s.lean==="UDF"?"✅ Protect":"📊 Monitor"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              {selSeat&&<SeatDetail seat={selSeat} onClose={()=>setSelSeat(null)}/>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
