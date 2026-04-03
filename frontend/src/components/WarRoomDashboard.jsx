import { useState, useEffect, useCallback } from "react";

const C = {
  udf:"#00C2FF", ldf:"#FF4444", nda:"#FF9800",
  bg:"#050C1A",  panel:"#0A1628", border:"#1A2E4A",
  text:"#E0EAF8", muted:"#5A7A9A", dark:"#070F1E",
  green:"#00E57A", amber:"#FFD600", dim:"#1A2E4A",
};

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const SURVEYS_STATIC = [
  {name:"Poll Tracker",      udf:92, ldf:46, nda:2,  n:"—",      date:"Mar 2026"},
  {name:"ElectionTracker7",  udf:91, ldf:46, nda:3,  n:"—",      date:"Mar 2026"},
  {name:"Poll Mantra",       udf:85, ldf:50, nda:5,  n:"26,000", date:"Mar 2026"},
  {name:"Manorama C-Voter",  udf:75, ldf:63, nda:3,  n:"89,693", date:"Mar 14-26"},
  {name:"Mathrubhumi",       udf:62, ldf:66, nda:2,  n:"—",      date:"Feb 16-26"},
  {name:"Political Vibe",    udf:59, ldf:68, nda:13, n:"2,500",  date:"Mar 2026"},
];

const VOTE_SHARES_STATIC = [
  {s:"Poll Mantra",    udf:38.2, ldf:33.7, nda:20.4},
  {s:"Manorama C-Vtr", udf:40.0, ldf:36.0, nda:15.0},
  {s:"Political Vibe", udf:38.5, ldf:39.5, nda:17.0},
  {s:"Mathrubhumi",    udf:42.0, ldf:38.0, nda:14.0},
  {s:"Local Body '25", udf:43.0, ldf:40.0, nda:16.0},
];

const ISSUES_STATIC = [
  {label:"Employment",    pct:17.32, udf:70},
  {label:"Inflation",     pct:15.21, udf:80},
  {label:"Infrastructure",pct:12.58, udf:55},
  {label:"Healthcare",    pct:11.84, udf:52},
  {label:"Corruption",    pct:11.16, udf:75},
  {label:"Drug Menace",   pct:9.80,  udf:72},
  {label:"Women Safety",  pct:8.42,  udf:65},
  {label:"Education",     pct:7.10,  udf:60},
];

const DISTRICTS_STATIC = [
  {n:"Thiruvananthapuram", seats:14, l21:13, u21:1,  u24:8,  u25:2,  proj:"UDF 6-8",   lean:"SWING"},
  {n:"Kollam",             seats:11, l21:9,  u21:1,  u24:8,  u25:5,  proj:"UDF 7-9",   lean:"LEAN UDF"},
  {n:"Pathanamthitta",     seats:5,  l21:5,  u21:0,  u24:5,  u25:5,  proj:"UDF 4-5",   lean:"STRONG UDF"},
  {n:"Alappuzha",          seats:9,  l21:8,  u21:1,  u24:8,  u25:7,  proj:"UDF 5-7",   lean:"LEAN UDF"},
  {n:"Kottayam",           seats:9,  l21:5,  u21:4,  u24:8,  u25:6,  proj:"UDF 6-7",   lean:"LEAN UDF"},
  {n:"Idukki",             seats:5,  l21:4,  u21:1,  u24:5,  u25:4,  proj:"UDF 3-4",   lean:"LEAN UDF"},
  {n:"Ernakulam",          seats:14, l21:5,  u21:9,  u24:14, u25:14, proj:"UDF 11-13", lean:"STRONG UDF"},
  {n:"Thrissur",           seats:13, l21:12, u21:1,  u24:3,  u25:2,  proj:"UDF 4-7",   lean:"SWING"},
  {n:"Palakkad",           seats:12, l21:9,  u21:3,  u24:5,  u25:4,  proj:"UDF 5-7",   lean:"SWING"},
  {n:"Malappuram",         seats:16, l21:3,  u21:13, u24:16, u25:14, proj:"UDF 13-16", lean:"STRONG UDF"},
  {n:"Kozhikode",          seats:13, l21:11, u21:2,  u24:7,  u25:7,  proj:"UDF 6-8",   lean:"SWING"},
  {n:"Wayanad",            seats:3,  l21:2,  u21:1,  u24:3,  u25:2,  proj:"UDF 2-3",   lean:"LEAN UDF"},
  {n:"Kannur",             seats:11, l21:9,  u21:2,  u24:5,  u25:5,  proj:"UDF 3-5",   lean:"LEAN LDF"},
  {n:"Kasaragod",          seats:5,  l21:3,  u21:2,  u24:5,  u25:3,  proj:"UDF 3-4",   lean:"SWING"},
];

const LEADERS_STATIC = [
  {name:"V.D. Satheesan",   party:"Congress / UDF — Leader of Opposition", cm:27.77, apr:70, f:"udf"},
  {name:"R. Chennithala",   party:"Congress / UDF — Senior Leader",         cm:12.06, apr:78, f:"udf"},
  {name:"Rahul Gandhi",     party:"INC — National Influence",               cm:44.20, apr:82, f:"udf"},
  {name:"Pinarayi Vijayan", party:"CPI(M) / LDF — Chief Minister",          cm:27.85, apr:48, f:"ldf"},
  {name:"K.K. Shailaja",   party:"CPI(M) / LDF — Peravoor",                cm:12.10, apr:76, f:"ldf"},
  {name:"M.V. Govindan",   party:"CPI(M) — State Secretary",               cm:6.40,  apr:42, f:"ldf"},
  {name:"Rajeev Chandrasekhar",party:"BJP President Kerala / NDA",          cm:52.10, apr:42, f:"nda"},
  {name:"Suresh Gopi",     party:"BJP / NDA — Thrissur",                    cm:8.50,  apr:55, f:"nda"},
];

const STRATEGIES_STATIC = [
  {id:1,icon:"🏠",title:"Kitchen Table Economics",   pri:"CRITICAL",st:"ACTIVE",      desc:"Hyper-local inflation scorecards. Kerala #1 inflation state for 7 months. ₹10,000/month burden narrative per constituency. WhatsApp + SHG network."},
  {id:2,icon:"🎯",title:"Vision Over Attack",         pri:"HIGH",   st:"ACTIVE",      desc:"Shift to Kerala 2031 Vision document. 3 concrete promises per district. Oommen Chandy Health Insurance — ₹25L/household. ₹1000/month for college girls."},
  {id:3,icon:"👤",title:"Satheesan as CM Brand",      pri:"CRITICAL",st:"IN PROGRESS", desc:"CM preference tied — Vijayan 27.85% vs Satheesan 27.77%. Open sabhas + constituency documentaries. Accessible vs Imperial framing drives the gap."},
  {id:4,icon:"⚡",title:"Women + Youth Mobilisation", pri:"HIGH",   st:"ACTIVE",      desc:"15L women via Indira Guarantees messaging. 8-10L first-time voters via Instagram/Shorts. Gulf diaspora family outreach critical in Malabar."},
  {id:5,icon:"🗺️",title:"30 Swing Seat Blitz",        pri:"CRITICAL",st:"PLANNING",    desc:"Manorama C-Voter: 69-81 range — need floor of 71 for majority. Surgical resource deploy. Political Vibe shows NDA 8-17 — bipolar anti-NDA drive in 12 spoiler seats."},
  {id:6,icon:"📊",title:"NDA Spoiler Containment",    pri:"HIGH",   st:"ACTIVE",      desc:"Thrissur·Attingal·Kazhakkoottam·Irinjalakuda·Nemom·Malampuzha. Message: Vote NDA = gift for LDF. Deploy Suresh Gopi-specific counter-messaging in Thrissur."},
];

const leanColor = l =>
  l==="STRONG UDF"?"#00C2FF":l==="LEAN UDF"?"#00FF88":
  l==="SWING"?"#FFD700":l==="LEAN LDF"?"#FF8800":"#FF4444";

const riskColor = r =>
  r==="CRITICAL"||r==="NDA Spoiler"?"#FF4444":
  r==="HIGH"||r==="Hard"?"#FF9800":
  r==="MEDIUM"||r==="Tight"?"#FFD700":"#00E57A";

function Badge({label}){
  const c =
    label==="CRITICAL"||label==="LEAN LDF"||label==="TOSS-UP"?C.ldf:
    label==="HIGH"||label==="SWING"||label==="IN PROGRESS"?"#FFD700":
    label==="ACTIVE"||label==="LEAN UDF"||label==="STRONG UDF"||label==="LIVE"||label==="SAFE UDF"?"#00E57A":
    label==="NDA Spoiler"?C.nda:label==="PLANNING"||label==="COMPILED"||label==="6 POLLS"?C.udf:C.muted;
  return <span style={{fontSize:9,padding:"2px 7px",borderRadius:20,background:`${c}20`,color:c,border:`1px solid ${c}40`,letterSpacing:1,whiteSpace:"nowrap",fontFamily:"monospace"}}>{label}</span>;
}

function Panel({title,badge,children,style={}}){
  return(
    <div style={{background:C.panel,border:`1px solid ${C.border}`,borderRadius:8,padding:16,...style}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12,paddingBottom:10,borderBottom:`1px solid ${C.border}`}}>
        <span style={{fontSize:10,fontWeight:700,textTransform:"uppercase",letterSpacing:2,color:C.muted}}>{title}</span>
        {badge&&<Badge label={badge}/>}
      </div>
      {children}
    </div>
  );
}

function Bar({val,max=100,color,height=6}){
  return(
    <div style={{height,background:"#0A1E3A",borderRadius:4,overflow:"hidden",border:`1px solid ${C.border}`}}>
      <div style={{width:`${Math.min(100,(val/max)*100)}%`,height:"100%",background:color,boxShadow:`0 0 6px ${color}60`,transition:"width 1.2s ease"}}/>
    </div>
  );
}

function LiveDot({color=C.green}){
  const [b,setB]=useState(true);
  useEffect(()=>{const t=setInterval(()=>setB(x=>!x),800);return()=>clearInterval(t);},[]);
  return <div style={{width:7,height:7,borderRadius:"50%",flexShrink:0,background:b?color:`${color}44`,boxShadow:b?`0 0 8px ${color}`:"none",transition:"all 0.4s"}}/>;
}

function computeProjection(scores){
  if(!scores||scores.length===0) return null;
  return {
    udf:scores.filter(s=>s.lean==="UDF").length,
    ldf:scores.filter(s=>s.lean==="LDF").length,
    nda:scores.filter(s=>s.lean==="NDA").length,
    swing:scores.filter(s=>s.lean==="SWING").length,
  };
}

function computeSwingSeats(scores){
  if(!scores||scores.length===0) return [];
  return scores
    .filter(s=>s.risk==="CRITICAL"||s.risk==="HIGH")
    .sort((a,b)=>(a.risk==="CRITICAL"?0:1)-(b.risk==="CRITICAL"?0:1))
    .slice(0,20)
    .map(s=>({
      seat:s.name, dist:s.district||s.dist,
      status:s.lean==="SWING"?"TOSS-UP":s.lean==="UDF"?"LEAN UDF":s.lean==="LDF"?"LEAN LDF":"LEAN NDA",
      udf:s.udf, ldf:s.ldf, nda:s.nda,
      risk:s.nda>25?"NDA Spoiler":s.risk==="CRITICAL"?"Hard":"Tight",
      action:s.war_room_action||"", win_prob_udf:s.win_prob_udf,
    }));
}

const STATIC_SWING = [
  {seat:"Thrissur",     dist:"Thrissur", status:"TOSS-UP",  udf:36,ldf:34,nda:28,risk:"NDA Spoiler",win_prob_udf:40},
  {seat:"Kazhakkoottam",dist:"TVM",      status:"TOSS-UP",  udf:33,ldf:32,nda:33,risk:"NDA Spoiler",win_prob_udf:38},
  {seat:"Nemom",        dist:"TVM",      status:"LEAN LDF", udf:30,ldf:41,nda:27,risk:"NDA Spoiler",win_prob_udf:32},
  {seat:"Attingal",     dist:"TVM",      status:"TOSS-UP",  udf:35,ldf:34,nda:29,risk:"NDA Spoiler",win_prob_udf:42},
  {seat:"Irinjalakuda", dist:"Thrissur", status:"TOSS-UP",  udf:35,ldf:33,nda:30,risk:"NDA Spoiler",win_prob_udf:41},
  {seat:"Malampuzha",   dist:"Palakkad", status:"LEAN NDA", udf:32,ldf:28,nda:38,risk:"NDA Spoiler",win_prob_udf:28},
  {seat:"Pala",         dist:"Kottayam", status:"TOSS-UP",  udf:45,ldf:43,nda:10,risk:"Tight",      win_prob_udf:52},
  {seat:"Palakkad",     dist:"Palakkad", status:"TOSS-UP",  udf:38,ldf:36,nda:24,risk:"NDA Spoiler",win_prob_udf:45},
  {seat:"Chelakkara",   dist:"Thrissur", status:"TOSS-UP",  udf:42,ldf:40,nda:16,risk:"Tight",      win_prob_udf:50},
  {seat:"Peravoor",     dist:"Kannur",   status:"TOSS-UP",  udf:44,ldf:46,nda:8, risk:"Hard",       win_prob_udf:46},
  {seat:"Vamanapuram",  dist:"TVM",      status:"TOSS-UP",  udf:42,ldf:41,nda:15,risk:"Hard",       win_prob_udf:50},
  {seat:"Aruvikkara",   dist:"TVM",      status:"TOSS-UP",  udf:44,ldf:43,nda:11,risk:"Hard",       win_prob_udf:51},
];

export default function WarRoomDashboard(){
  const [tab,setTab]         = useState("overview");
  const [selDist,setSelDist] = useState(null);
  const [report,setReport]   = useState(null);
  const [scores,setScores]   = useState([]);
  const [apiOk,setApiOk]     = useState(false);
  const [lastSync,setLastSync] = useState(null);
  const [isLive,setIsLive]   = useState(false);
  const TABS = ["overview","districts","swing seats","strategy","leaders"];

  const fetchLive = useCallback(async()=>{
      try{
        const h=await fetch(`${API}/api/health`,{
          signal:AbortSignal.timeout(3000),
          headers:{"ngrok-skip-browser-warning":"true"}
        });
        if(!h.ok) throw new Error();
        setApiOk(true);
        const rr=await fetch(`${API}/api/latest-report`,{
          headers:{"ngrok-skip-browser-warning":"true"}
        });
        if(rr.ok){
          const data=await rr.json();
          setReport(data);
          if(data.constituency_scores?.length>0){setScores(data.constituency_scores);setIsLive(true);}
          setLastSync(new Date());
        }
        const cr=await fetch(`${API}/api/constituencies`,{
          headers:{"ngrok-skip-browser-warning":"true"}
        });
        if(cr.ok){
          const cd=await cr.json();
          if(cd.seats?.length>0){setScores(cd.seats);setIsLive(true);}
        }
      }catch{setApiOk(false);}
    },[]);

  useEffect(()=>{fetchLive();const id=setInterval(fetchLive,60000);return()=>clearInterval(id);},[fetchLive]);

  const liveProj = computeProjection(scores);
  const surveyMedian = {
    udf:Math.round(SURVEYS_STATIC.reduce((a,s)=>a+s.udf,0)/SURVEYS_STATIC.length),
    ldf:Math.round(SURVEYS_STATIC.reduce((a,s)=>a+s.ldf,0)/SURVEYS_STATIC.length),
    nda:Math.round(SURVEYS_STATIC.reduce((a,s)=>a+s.nda,0)/SURVEYS_STATIC.length),
  };
  const displayProj = liveProj || surveyMedian;
  const swingSeats  = isLive ? computeSwingSeats(scores) : STATIC_SWING;

  const districtData = DISTRICTS_STATIC.map(d=>{
    if(!isLive||!scores.length) return d;
    const ds=scores.filter(s=>(s.district||s.dist)===d.n);
    if(!ds.length) return d;
    const u=ds.filter(s=>s.lean==="UDF").length;
    const l=ds.filter(s=>s.lean==="LDF").length;
    const sw=ds.filter(s=>s.lean==="SWING").length;
    const nd=ds.filter(s=>s.lean==="NDA").length;
    const lean=u>=l+2?(u>=d.seats*0.7?"STRONG UDF":"LEAN UDF"):l>=u+2?"LEAN LDF":sw>=3?"SWING":d.lean;
    return{...d,proj:`UDF ${u} · LDF ${l}${nd>0?` · NDA ${nd}`:""}`,lean,ai_udf:u,ai_ldf:l,ai_swing:sw};
  });

  const avgUDF = scores.length>0?scores.reduce((a,s)=>a+(s.win_prob_udf||0),0)/scores.length:68;
  const sentValues = [
    {l:"UDF Positive Sentiment",  v:Math.round(avgUDF),   c:C.udf},
    {l:"LDF Positive Sentiment",  v:Math.round(100-avgUDF),c:C.ldf},
    {l:"NDA Positive Sentiment",  v:41,                    c:C.nda},
    {l:"Anti-Incumbency vs LDF",  v:62,                    c:"#FF6666"},
    {l:"Rahul Gandhi Influence",  v:74,                    c:C.udf},
    {l:"UDF Dev Trust Index",     v:68,                    c:C.green},
  ];

  const verdict = report?.overall_status
    ? `${report.overall_status}. AI scored ${scores.length} seats. UDF projection: ${displayProj.udf} seats.`
    : "UDF most likely to form government. Anti-incumbency + local body momentum + Inflation narrative all point to Congress-led return. Manorama C-Voter (n=89,693): UDF 69-81 seats. Third LDF term would defy 65 years of Kerala political history.";

  const ticker = [
    ...(report?.top_risks?.slice(0,3).map(r=>`⚠️ ${r.title}: ${(r.description||"").slice(0,55)}`)||[]),
    "🔥 Kerala Inflation #1 in India — 9.49% for 7 months",
    "✅ UDF swept Dec 2025 Local Bodies: 43% vs LDF 40%",
    "🎯 CM Race TIED: Vijayan 27.85% vs Satheesan 27.77%",
    "📊 Manorama C-Voter (n=89,693): UDF 69-81 seats",
    "🗳️ Political Vibe: NDA surge 8-17 seats — spoiler risk",
    "📈 Rahul Gandhi — most influential national leader: 44.2%",
    "⚡ Ezhava drift toward BJP accelerating in South Kerala",
    "💰 UDF: Oommen Chandy Health Insurance ₹25L/household",
    isLive&&scores.length>0?`🤖 AI Pipeline: ${scores.filter(s=>s.lean==="UDF").length}U ${scores.filter(s=>s.lean==="LDF").length}L ${scores.filter(s=>s.lean==="NDA").length}N scored`:"📅 Polling: April 9 · Results: May 4 · 7 days remaining",
  ].filter(Boolean).join("   ·   ");

  return(
    <div style={{background:C.bg,color:C.text,fontFamily:"'Courier New',monospace",fontSize:13}}>
      <style>{`@keyframes wrticker{from{transform:translateX(0)}to{transform:translateX(-50%)}} @keyframes wrFade{from{opacity:0}to{opacity:1}} ::-webkit-scrollbar{width:3px;height:3px;background:${C.bg}} ::-webkit-scrollbar-thumb{background:${C.dim};border-radius:3px}`}</style>

      {/* Ticker */}
      <div style={{background:"#020810",borderBottom:`1px solid ${C.border}`,padding:"7px 0",overflow:"hidden"}}>
        <div style={{whiteSpace:"nowrap",animation:"wrticker 70s linear infinite",fontSize:11,color:C.udf,letterSpacing:0.5}}>
          {(ticker+"   ·   "+ticker+"   ·   ")}
        </div>
      </div>

      {/* KPI Strip */}
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(130px,1fr))",gap:1,background:C.border}}>
        {[
          {l:"UDF Projection", v:isLive?`~${displayProj.udf}`:"75-92",  sub:isLive?"AI Pipeline":"Survey Range",  c:C.udf},
          {l:"LDF Projection", v:isLive?`~${displayProj.ldf}`:"46-66",  sub:isLive?"AI Pipeline":"Survey Range",  c:C.ldf},
          {l:"NDA Projection", v:isLive?`~${displayProj.nda}`:"2-17",   sub:isLive?"AI Pipeline":"Survey Range",  c:C.nda},
          {l:"Majority Mark",  v:"71",          sub:"of 140 seats",       c:"#FFD700"},
          {l:"UDF Vote Share", v:"38.2%",        sub:"Poll Mantra n=26K", c:C.udf},
          {l:"Anti-Incumbency",v:"62%",          sub:"vs LDF",            c:"#FF6666"},
        ].map((k,i)=>(
          <div key={i} style={{background:C.panel,padding:"12px 14px"}}>
            <div style={{fontSize:9,color:C.muted,textTransform:"uppercase",letterSpacing:1,marginBottom:3}}>{k.l}</div>
            <div style={{fontSize:21,fontWeight:800,color:k.c,fontFamily:"monospace"}}>{k.v}</div>
            <div style={{fontSize:9,color:C.muted,marginTop:2}}>{k.sub}</div>
          </div>
        ))}
      </div>

      {/* Live status bar */}
      <div style={{background:"#040C1A",borderBottom:`1px solid ${C.border}`,padding:"5px 18px",display:"flex",alignItems:"center",gap:10,flexWrap:"wrap"}}>
        <div style={{display:"flex",alignItems:"center",gap:6,background:apiOk&&isLive?`${C.green}10`:`${C.amber}10`,border:`1px solid ${apiOk&&isLive?C.green+"30":C.amber+"30"}`,borderRadius:6,padding:"3px 9px"}}>
          <LiveDot color={apiOk&&isLive?C.green:C.amber}/>
          <span style={{fontSize:9,fontFamily:"monospace",color:apiOk&&isLive?C.green:C.amber}}>
            {apiOk&&isLive?"LIVE — AI Pipeline Connected":apiOk?"API Connected — Run Pipeline for Live Data":"API Offline — Showing static data"}
          </span>
        </div>
        {isLive&&<span style={{fontSize:9,color:C.muted}}>{scores.length} seats scored · {report?.date||"today"}</span>}
        {lastSync&&<span style={{fontSize:9,color:C.dim,marginLeft:"auto"}}>Synced {lastSync.toLocaleTimeString()}</span>}
        <button onClick={fetchLive} style={{padding:"3px 8px",borderRadius:4,background:"transparent",border:`1px solid ${C.border}`,color:C.muted,fontSize:9,cursor:"pointer",fontFamily:"monospace"}}>↺</button>
      </div>

      {/* Sub-tabs */}
      <div style={{background:C.dark,borderBottom:`1px solid ${C.border}`,padding:"0 16px",display:"flex",gap:0,overflowX:"auto"}}>
        {TABS.map(t=>(
          <button key={t} onClick={()=>setTab(t)} style={{background:"none",border:"none",color:tab===t?C.udf:C.muted,padding:"10px 16px",fontSize:10,letterSpacing:2,textTransform:"uppercase",cursor:"pointer",borderBottom:tab===t?`2px solid ${C.udf}`:"2px solid transparent",transition:"all 0.2s",whiteSpace:"nowrap",fontFamily:"'Courier New',monospace"}}>{t}</button>
        ))}
      </div>

      <div style={{padding:14}}>

        {/* OVERVIEW */}
        {tab==="overview"&&(
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(290px,1fr))",gap:12,animation:"wrFade 0.4s ease"}}>

            <Panel title="Seat Projection" badge={isLive?"LIVE":"COMPILED"}>
              <div style={{marginBottom:8,display:"flex",justifyContent:"space-between"}}>
                <span style={{fontSize:10,color:C.muted}}>Total: 140 seats</span>
                <span style={{fontSize:10,color:"#FFD700"}}>━ Majority: 71</span>
              </div>
              {[["UDF — United Democratic Front",displayProj.udf,C.udf],["LDF — Left Democratic Front",displayProj.ldf,C.ldf],["NDA — BJP Alliance",displayProj.nda,C.nda]].map(([l,v,c])=>(
                <div key={l} style={{marginBottom:12}}>
                  <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}>
                    <span style={{fontSize:10,color:C.muted}}>{l}</span>
                    <span style={{fontSize:18,fontWeight:800,color:c,fontFamily:"monospace"}}>{v}</span>
                  </div>
                  <Bar val={v} max={140} color={c} height={8}/>
                </div>
              ))}
              {isLive&&liveProj&&(
                <div style={{background:C.dark,borderRadius:5,padding:"7px 10px",border:`1px solid ${C.green}20`,marginBottom:8}}>
                  <div style={{fontSize:9,color:C.green,marginBottom:2}}>🤖 AI SOURCE</div>
                  <div style={{fontSize:9,color:C.muted}}>GPT-4o scored all {scores.length} seats using 2021 results + today's news sentiment + community composition</div>
                </div>
              )}
              <div style={{background:C.dark,borderRadius:6,padding:"10px 12px",border:`1px solid ${C.udf}20`}}>
                <div style={{fontSize:9,color:C.udf,marginBottom:4}}>📊 STRATEGIC VERDICT</div>
                <div style={{fontSize:10,color:C.text,lineHeight:1.7}}>{verdict}</div>
              </div>
            </Panel>

            <Panel title="Multi-Survey Seat Comparison" badge="6 POLLS">
              {SURVEYS_STATIC.map((s,i)=>(
                <div key={i} style={{marginBottom:10}}>
                  <div style={{display:"flex",justifyContent:"space-between",marginBottom:3,flexWrap:"wrap",gap:3}}>
                    <div>
                      <span style={{fontSize:10,color:C.muted}}>{s.name}</span>
                      <span style={{fontSize:8,color:C.dim,marginLeft:5}}>{s.n!=="—"?`n=${s.n}`:""} {s.date}</span>
                    </div>
                    <div style={{display:"flex",gap:7}}>
                      {[["U",s.udf,C.udf],["L",s.ldf,C.ldf],["N",s.nda,C.nda]].map(([k,v,c])=>(
                        <span key={k} style={{fontSize:10,color:c,fontFamily:"monospace",fontWeight:700}}>{k}:{v}</span>
                      ))}
                    </div>
                  </div>
                  <div style={{height:6,background:"#0A1E3A",borderRadius:3,overflow:"hidden",display:"flex",gap:1}}>
                    <div style={{flex:s.udf,background:C.udf}}/><div style={{flex:s.ldf,background:C.ldf}}/><div style={{flex:s.nda,background:C.nda}}/>
                  </div>
                </div>
              ))}
              <div style={{borderTop:`1px solid ${C.border}`,paddingTop:8,marginTop:4}}>
                <div style={{fontSize:9,color:C.muted,marginBottom:5}}>VOTE SHARE AGGREGATES</div>
                <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",fontSize:9,gap:2}}>
                  <span style={{color:C.muted}}>Survey</span>
                  <span style={{color:C.udf,textAlign:"center"}}>UDF</span>
                  <span style={{color:C.ldf,textAlign:"center"}}>LDF</span>
                  <span style={{color:C.nda,textAlign:"center"}}>NDA</span>
                  {VOTE_SHARES_STATIC.map((v,i)=>[
                    <span key={`s${i}`} style={{color:C.muted,padding:"2px 0",fontSize:8}}>{v.s}</span>,
                    <span key={`u${i}`} style={{color:C.udf,textAlign:"center",fontFamily:"monospace",fontWeight:700}}>{v.udf}%</span>,
                    <span key={`l${i}`} style={{color:C.ldf,textAlign:"center",fontFamily:"monospace"}}>{v.ldf}%</span>,
                    <span key={`n${i}`} style={{color:C.nda,textAlign:"center",fontFamily:"monospace"}}>{v.nda}%</span>,
                  ])}
                </div>
              </div>
            </Panel>

            <Panel title="Issue Ownership — UDF vs LDF" badge="VOTER SURVEY">
              {ISSUES_STATIC.map((iss,i)=>(
                <div key={i} style={{marginBottom:9}}>
                  <div style={{display:"flex",justifyContent:"space-between",marginBottom:3}}>
                    <span style={{fontSize:11,color:C.text}}>{iss.label}</span>
                    <span style={{fontSize:10,color:C.muted,fontFamily:"monospace"}}>{iss.pct}%</span>
                  </div>
                  <div style={{height:6,background:"#0A1E3A",borderRadius:3,overflow:"hidden",display:"flex"}}>
                    <div style={{width:`${iss.udf}%`,height:"100%",background:`linear-gradient(90deg,${C.udf}cc,${C.udf}77)`}}/>
                    <div style={{width:`${100-iss.udf}%`,height:"100%",background:`linear-gradient(90deg,${C.ldf}66,${C.ldf}cc)`}}/>
                  </div>
                  <div style={{display:"flex",justifyContent:"space-between",marginTop:2}}>
                    <span style={{fontSize:8,color:`${C.udf}aa`}}>UDF {iss.udf}%</span>
                    <span style={{fontSize:8,color:`${C.ldf}aa`}}>LDF {100-iss.udf}%</span>
                  </div>
                </div>
              ))}
            </Panel>

            <Panel title="Sentiment Gauges" badge={isLive?"LIVE":"COMPILED"}>
              {sentValues.map((g,i)=>(
                <div key={i} style={{marginBottom:10}}>
                  <div style={{display:"flex",justifyContent:"space-between",marginBottom:3}}>
                    <span style={{fontSize:10,color:C.text}}>{g.l}</span>
                    <span style={{fontSize:12,fontWeight:700,color:g.c,fontFamily:"monospace"}}>{g.v}%</span>
                  </div>
                  <Bar val={g.v} color={g.c}/>
                </div>
              ))}
              {isLive&&<div style={{fontSize:9,color:C.green,marginTop:4}}>🤖 UDF/LDF sentiment from {scores.length} AI-scored seats</div>}
            </Panel>

            {isLive&&report?.top_risks?.length>0&&(
              <Panel title="Live Risk Alerts" badge="PIPELINE" style={{borderColor:C.ldf+"40"}}>
                {report.top_risks.slice(0,5).map((r,i)=>{
                  const rc=r.severity==="CRITICAL"?"#FF3F3F":r.severity==="HIGH"?C.nda:C.amber;
                  return(
                    <div key={i} style={{marginBottom:8,padding:"8px 10px",background:`${rc}08`,borderRadius:6,border:`1px solid ${rc}22`}}>
                      <div style={{display:"flex",justifyContent:"space-between",marginBottom:3}}>
                        <span style={{fontSize:11,fontWeight:700,color:rc}}>{r.severity==="CRITICAL"?"🔴":"🟡"} {r.title}</span>
                        <Badge label={r.severity}/>
                      </div>
                      {r.counter_action&&<div style={{fontSize:9,color:C.green}}>→ {r.counter_action?.slice(0,100)}</div>}
                    </div>
                  );
                })}
              </Panel>
            )}

            {isLive&&report?.action_playbook&&(
              <Panel title="Today's Tactical Playbook" badge="LIVE" style={{borderColor:C.green+"40"}}>
                {report.action_playbook.priority_message_of_day&&(
                  <div style={{fontSize:11,fontWeight:700,color:C.text,lineHeight:1.6,fontStyle:"italic",marginBottom:10,padding:"8px 12px",background:`${C.udf}08`,borderRadius:6,border:`1px solid ${C.udf}20`}}>
                    "{report.action_playbook.priority_message_of_day}"
                  </div>
                )}
                {report.action_playbook.ground_actions?.priority_constituencies&&(
                  <div style={{marginBottom:8}}>
                    <div style={{fontSize:9,color:C.muted,marginBottom:5}}>PRIORITY SEATS TODAY</div>
                    <div style={{display:"flex",gap:5,flexWrap:"wrap"}}>
                      {report.action_playbook.ground_actions.priority_constituencies.map((s,i)=>(
                        <span key={i} style={{fontSize:9,padding:"2px 8px",borderRadius:20,background:`${C.udf}15`,color:C.udf,border:`1px solid ${C.udf}30`}}>{s}</span>
                      ))}
                    </div>
                  </div>
                )}
                {report.action_playbook.counter_narrative&&(
                  <div style={{background:`${C.ldf}08`,borderRadius:5,padding:"8px 11px",border:`1px solid ${C.ldf}20`}}>
                    <div style={{fontSize:9,color:C.ldf,marginBottom:3}}>COUNTER-NARRATIVE</div>
                    <div style={{fontSize:10,color:C.text,fontStyle:"italic",lineHeight:1.6}}>"{report.action_playbook.counter_narrative}"</div>
                  </div>
                )}
              </Panel>
            )}
          </div>
        )}

        {/* DISTRICTS */}
        {tab==="districts"&&(
          <div style={{animation:"wrFade 0.4s ease"}}>
            <div style={{display:"flex",gap:10,marginBottom:12,flexWrap:"wrap",alignItems:"center"}}>
              {["STRONG UDF","LEAN UDF","SWING","LEAN LDF"].map(l=>(
                <div key={l} style={{display:"flex",alignItems:"center",gap:5}}>
                  <div style={{width:8,height:8,borderRadius:2,background:leanColor(l)}}/>
                  <span style={{fontSize:9,color:C.muted}}>{l}</span>
                </div>
              ))}
              {isLive&&<div style={{marginLeft:"auto",display:"flex",alignItems:"center",gap:5}}><LiveDot color={C.green}/><span style={{fontSize:9,color:C.green}}>AI-scored · {scores.length} seats</span></div>}
            </div>
            <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(250px,1fr))",gap:9}}>
              {districtData.map((d,i)=>{
                const lc=leanColor(d.lean),open=selDist===d.n;
                return(
                  <div key={i} onClick={()=>setSelDist(open?null:d.n)} style={{background:C.panel,border:`1px solid ${open?lc:lc+"30"}`,borderRadius:7,padding:"12px 14px",cursor:"pointer",transition:"all 0.25s",boxShadow:open?`0 0 18px ${lc}25`:"none"}}>
                    <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:8}}>
                      <div>
                        <div style={{fontSize:13,fontWeight:700,color:C.text}}>{d.n}</div>
                        <div style={{fontSize:9,color:C.muted,marginTop:2}}>{d.seats} seats</div>
                      </div>
                      <Badge label={d.lean}/>
                    </div>
                    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:5}}>
                      {[["'21 LDF",d.l21,C.ldf],["'24 UDF",d.u24,C.udf],["'25 UDF",d.u25,C.udf]].map(([l,v,c])=>(
                        <div key={l} style={{textAlign:"center",background:C.dark,borderRadius:4,padding:"5px 3px"}}>
                          <div style={{fontSize:8,color:C.muted}}>{l}</div>
                          <div style={{fontSize:15,fontWeight:700,color:c,fontFamily:"monospace"}}>{v}</div>
                        </div>
                      ))}
                    </div>
                    {open&&<div style={{borderTop:`1px solid ${C.border}`,paddingTop:8,marginTop:10}}>
                      <div style={{fontSize:9,color:C.muted,marginBottom:4}}>{isLive?"AI PROJECTION":"2026 PROJECTION"}</div>
                      <div style={{fontSize:14,fontWeight:700,color:lc}}>{d.proj}</div>
                      {isLive&&d.ai_swing>0&&<div style={{fontSize:9,color:C.amber,marginTop:3}}>⚡ {d.ai_swing} swing seat{d.ai_swing>1?"s":""} — monitor closely</div>}
                    </div>}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* SWING SEATS */}
        {tab==="swing seats"&&(
          <div style={{animation:"wrFade 0.4s ease"}}>
            <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:12}}>
              <LiveDot color={isLive?C.green:C.amber}/>
              <span style={{fontSize:9,color:isLive?C.green:C.amber}}>
                {isLive?`AI-identified ${swingSeats.length} critical/high risk seats`:"Static swing seat analysis — run pipeline for AI seats"}
              </span>
            </div>
            <div style={{overflowX:"auto",marginBottom:12}}>
              <table style={{width:"100%",borderCollapse:"collapse",fontSize:11}}>
                <thead>
                  <tr style={{borderBottom:`1px solid ${C.border}`}}>
                    {["#","Constituency","District","Status","UDF%","LDF%","NDA%","Win Prob","Risk","Action"].map(h=>(
                      <th key={h} style={{textAlign:"left",padding:"8px 9px",fontSize:9,color:C.muted,textTransform:"uppercase",letterSpacing:1,whiteSpace:"nowrap"}}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {swingSeats.map((s,i)=>(
                    <tr key={i} style={{borderBottom:`1px solid ${C.border}18`,background:i%2===0?"transparent":C.dark+"44"}}>
                      <td style={{padding:"9px 9px",color:C.muted,fontFamily:"monospace"}}>{i+1}</td>
                      <td style={{padding:"9px 9px",fontWeight:700,color:C.text}}>{s.seat}</td>
                      <td style={{padding:"9px 9px",color:C.muted}}>{s.dist}</td>
                      <td style={{padding:"9px 9px"}}><Badge label={s.status}/></td>
                      <td style={{padding:"9px 9px",color:C.udf,fontFamily:"monospace",fontWeight:700}}>{s.udf}%</td>
                      <td style={{padding:"9px 9px",color:C.ldf,fontFamily:"monospace"}}>{s.ldf}%</td>
                      <td style={{padding:"9px 9px",color:C.nda,fontFamily:"monospace"}}>{s.nda}%</td>
                      <td style={{padding:"9px 9px",color:s.win_prob_udf>=55?C.green:s.win_prob_udf>=45?C.amber:C.ldf,fontFamily:"monospace",fontWeight:700}}>{s.win_prob_udf}%</td>
                      <td style={{padding:"9px 9px"}}><span style={{fontSize:9,color:riskColor(s.risk),fontFamily:"monospace"}}>{s.risk}</span></td>
                      <td style={{padding:"9px 9px",fontSize:9,color:C.muted,maxWidth:160}}>{s.action?.slice(0,70)||s.risk==="NDA Spoiler"?"⚡ Bipolar messaging":s.status==="TOSS-UP"?"🎯 Star campaigner":s.status==="LEAN LDF"?"🔴 Breach strategy":"✅ Turnout drive"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Panel title="NDA Spoiler Counter-Strategy" badge="ACTION REQUIRED" style={{borderColor:C.nda+"40"}}>
              <div style={{fontSize:11,color:C.text,lineHeight:1.7,marginBottom:10}}>In <span style={{color:C.udf,fontWeight:700}}>Thrissur · Attingal · Kazhakkoottam · Irinjalakuda · Nemom · Malampuzha</span> — NDA polls 27–38%, creating genuine 3-way contests. Political Vibe projects NDA 8-17 seats — highest ever.</div>
              <div style={{background:`${C.nda}10`,border:`1px solid ${C.nda}30`,borderRadius:5,padding:"10px 12px"}}>
                <div style={{fontSize:9,color:C.nda,marginBottom:4}}>BIPOLAR SCRIPT</div>
                <div style={{fontSize:11,color:C.text,fontStyle:"italic",lineHeight:1.6}}>"BJP has never won here. A vote for NDA only helps LDF stay in power. The real fight is UDF vs LDF — choose the side that can actually win for Kerala."</div>
              </div>
            </Panel>
          </div>
        )}

        {/* STRATEGY */}
        {tab==="strategy"&&(
          <div style={{animation:"wrFade 0.4s ease"}}>
            <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(280px,1fr))",gap:11,marginBottom:14}}>
              {STRATEGIES_STATIC.map(s=>(
                <div key={s.id} style={{background:C.panel,border:`1px solid ${C.border}`,borderRadius:8,padding:14}}>
                  <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:10}}>
                    <div style={{display:"flex",alignItems:"center",gap:10}}>
                      <span style={{fontSize:22}}>{s.icon}</span>
                      <div>
                        <div style={{fontSize:9,color:C.muted}}>Strategy #{s.id}</div>
                        <div style={{fontSize:12,fontWeight:700,color:C.udf,marginTop:2}}>{s.title}</div>
                      </div>
                    </div>
                    <div style={{display:"flex",flexDirection:"column",gap:4,alignItems:"flex-end"}}>
                      <Badge label={s.pri}/><Badge label={s.st}/>
                    </div>
                  </div>
                  <div style={{fontSize:11,color:C.muted,lineHeight:1.7,background:C.dark,borderRadius:5,padding:"9px 11px"}}>{s.desc}</div>
                </div>
              ))}
            </div>
            <Panel title="Latest Survey Intelligence — April 2026" badge="UPDATED">
              <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(220px,1fr))",gap:8}}>
                {[
                  {title:"Manorama C-Voter",detail:"n=89,693 · Mar 14-26",text:"UDF: 69-81 · LDF: 57-69 · NDA: 1-5. Largest sample. UDF clear favourite. Pathanamthitta reversal — LDF swept 2021, UDF leads now."},
                  {title:"Political Vibe",  detail:"n=2,500 · Mar 2026",  text:"LDF: 59-78 · UDF: 49-69 · NDA: 8-17. Highest ever NDA projection. Nemom, Malampuzha, TVM as BJP wins. Closest to 3-way contest."},
                  {title:"Poll Tracker",   detail:"Tracker poll · Mar",   text:"UDF: 92 · LDF: 46 · NDA: 2. Most bullish on UDF. Rolling tracker captures momentum. UDF surging post-local body wins."},
                  {title:"Mathrubhumi",   detail:"Feb 16-26 sample",      text:"LDF: 66 · UDF: 62. LDF ahead — oldest survey, Feb data. Pathanamthitta and Ernakulam swing toward UDF noted."},
                ].map((item,i)=>(
                  <div key={i} style={{background:C.dark,borderRadius:6,padding:"10px 12px",border:`1px solid ${C.border}`}}>
                    <div style={{fontSize:11,fontWeight:700,color:C.udf,marginBottom:2}}>{item.title}</div>
                    <div style={{fontSize:9,color:C.dim,marginBottom:5}}>{item.detail}</div>
                    <div style={{fontSize:10,color:C.muted,lineHeight:1.6}}>{item.text}</div>
                  </div>
                ))}
              </div>
            </Panel>
          </div>
        )}

        {/* LEADERS */}
        {tab==="leaders"&&(
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(280px,1fr))",gap:12,animation:"wrFade 0.4s ease"}}>
            {["udf","ldf","nda"].map(front=>(
              <Panel key={front} title={`${front.toUpperCase()} Leadership`} badge={front==="udf"?"FRONT":front==="ldf"?"INCUMBENT":"SPOILER"}>
                {LEADERS_STATIC.filter(l=>l.f===front).map((l,i)=>{
                  const fc=l.f==="udf"?C.udf:l.f==="ldf"?C.ldf:C.nda;
                  return(
                    <div key={i} style={{background:C.dark,border:`1px solid ${fc}25`,borderRadius:6,padding:"11px 13px",marginBottom:8}}>
                      <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}>
                        <div>
                          <div style={{fontSize:12,fontWeight:700,color:C.text}}>{l.name}</div>
                          <div style={{fontSize:9,color:C.muted,marginTop:2}}>{l.party}</div>
                        </div>
                        <div style={{textAlign:"right"}}>
                          <div style={{fontSize:9,color:C.muted}}>CM Pref.</div>
                          <div style={{fontSize:17,fontWeight:800,color:fc,fontFamily:"monospace"}}>{l.cm}%</div>
                        </div>
                      </div>
                      <div>
                        <div style={{display:"flex",justifyContent:"space-between",marginBottom:3}}>
                          <span style={{fontSize:9,color:C.muted}}>Approval</span>
                          <span style={{fontSize:9,color:fc}}>{l.apr}%</span>
                        </div>
                        <Bar val={l.apr} color={fc} height={5}/>
                      </div>
                    </div>
                  );
                })}
              </Panel>
            ))}
            <Panel title="National Influence in Kerala" badge="KEY METRIC">
              {[{n:"Rahul Gandhi",v:44.2,c:C.udf},{n:"Narendra Modi",v:19.5,c:C.nda},{n:"Pinarayi Vijayan",v:16.8,c:C.ldf},{n:"K.C. Venugopal",v:12.4,c:C.udf},{n:"Sonia Gandhi",v:8.2,c:C.udf}].map((x,i)=>(
                <div key={i} style={{marginBottom:10}}>
                  <div style={{display:"flex",justifyContent:"space-between",marginBottom:3}}>
                    <span style={{fontSize:11,color:C.text}}>{x.n}</span>
                    <span style={{fontSize:13,fontWeight:700,color:x.c,fontFamily:"monospace"}}>{x.v}%</span>
                  </div>
                  <Bar val={x.v} max={50} color={x.c} height={5}/>
                </div>
              ))}
              <div style={{background:C.dark,borderRadius:5,padding:"8px 10px",border:`1px solid ${C.udf}20`,marginTop:8}}>
                <div style={{fontSize:9,color:C.udf,marginBottom:3}}>CM PREFERENCE — RAZOR THIN</div>
                <div style={{fontSize:10,color:C.text}}>Vijayan 27.85% vs Satheesan 27.77% — 0.08% gap. Every Satheesan open sabha event is decisive.</div>
              </div>
            </Panel>
          </div>
        )}

      </div>

      <div style={{background:"#020810",borderTop:`1px solid ${C.border}`,padding:"8px 18px",display:"flex",justifyContent:"space-between",flexWrap:"wrap",gap:6}}>
        <span style={{fontSize:9,color:C.muted}}>Sources: Mathrubhumi · Poll Mantra (n=26K) · Political Vibe (n=2.5K) · Manorama C-Voter (n=89,693) · ElectionTracker7 · Poll Tracker · CPPR · Onmanorama</span>
        <span style={{fontSize:9,color:C.muted}}>Kerala Assembly Elections · April 9, 2026 · Results: May 4, 2026</span>
      </div>
    </div>
  );
}
