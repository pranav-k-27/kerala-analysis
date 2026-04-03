import { useState, useEffect, useRef } from "react";

const T = {
  bg:"#03080F", panel:"#07111E", card:"#0B1929", border:"#162840",
  udf:"#00C8FF", ldf:"#FF3F3F", nda:"#FF9500",
  green:"#00E57A", amber:"#FFD600", muted:"#4A6A8A", text:"#D8EAF8", dim:"#2A4A6A",
};

const CONSTITUENCIES=[
  {name:"Thrissur",       dist:"Thrissur",       base_udf:36,base_ldf:34,base_nda:28,type:"TOSS-UP",  swing_idx:0.82,minority_pct:28,ezhava_pct:22,christian_pct:24,incumbent:"LDF",margin21:4100},
  {name:"Nemom",          dist:"TVM",            base_udf:30,base_ldf:41,base_nda:27,type:"LEAN LDF", swing_idx:0.71,minority_pct:12,ezhava_pct:18,christian_pct:14,incumbent:"LDF",margin21:8820},
  {name:"Attingal",       dist:"TVM",            base_udf:35,base_ldf:34,base_nda:29,type:"TOSS-UP",  swing_idx:0.85,minority_pct:15,ezhava_pct:20,christian_pct:12,incumbent:"LDF",margin21:3200},
  {name:"Kazhakuttam",    dist:"TVM",            base_udf:33,base_ldf:32,base_nda:33,type:"TOSS-UP",  swing_idx:0.91,minority_pct:18,ezhava_pct:16,christian_pct:10,incumbent:"LDF",margin21:2600},
  {name:"Pala",           dist:"Kottayam",       base_udf:45,base_ldf:43,base_nda:10,type:"TOSS-UP",  swing_idx:0.78,minority_pct:10,ezhava_pct:8, christian_pct:52,incumbent:"LDF",margin21:1100},
  {name:"Chalakudy",      dist:"Thrissur",       base_udf:44,base_ldf:40,base_nda:14,type:"LEAN UDF", swing_idx:0.65,minority_pct:20,ezhava_pct:18,christian_pct:30,incumbent:"LDF",margin21:6700},
  {name:"Irinjalakkuda",  dist:"Thrissur",       base_udf:35,base_ldf:33,base_nda:30,type:"TOSS-UP",  swing_idx:0.88,minority_pct:25,ezhava_pct:20,christian_pct:18,incumbent:"LDF",margin21:2900},
  {name:"Aranmula",       dist:"Pathanamthitta", base_udf:46,base_ldf:38,base_nda:14,type:"LEAN UDF", swing_idx:0.60,minority_pct:8, ezhava_pct:10,christian_pct:48,incumbent:"LDF",margin21:5400},
  {name:"Kuthuparamba",   dist:"Kannur",         base_udf:38,base_ldf:45,base_nda:15,type:"LEAN LDF", swing_idx:0.55,minority_pct:32,ezhava_pct:14,christian_pct:8, incumbent:"LDF",margin21:9200},
  {name:"Beypore",        dist:"Kozhikode",      base_udf:47,base_ldf:38,base_nda:12,type:"LEAN UDF", swing_idx:0.58,minority_pct:44,ezhava_pct:12,christian_pct:6, incumbent:"LDF",margin21:7100},
  {name:"Palakkad",       dist:"Palakkad",       base_udf:38,base_ldf:36,base_nda:24,type:"TOSS-UP",  swing_idx:0.80,minority_pct:30,ezhava_pct:16,christian_pct:8, incumbent:"LDF",margin21:4500},
  {name:"Perumbavoor",    dist:"Ernakulam",      base_udf:52,base_ldf:35,base_nda:11,type:"SAFE UDF", swing_idx:0.35,minority_pct:22,ezhava_pct:15,christian_pct:35,incumbent:"UDF",margin21:12000},
  {name:"Kayamkulam",     dist:"Alappuzha",      base_udf:48,base_ldf:40,base_nda:10,type:"LEAN UDF", swing_idx:0.52,minority_pct:20,ezhava_pct:22,christian_pct:18,incumbent:"LDF",margin21:8300},
  {name:"Malampuzha",     dist:"Palakkad",       base_udf:32,base_ldf:28,base_nda:38,type:"LEAN NDA", swing_idx:0.76,minority_pct:8, ezhava_pct:24,christian_pct:6, incumbent:"LDF",margin21:5600},
  {name:"Thalassery",     dist:"Kannur",         base_udf:36,base_ldf:48,base_nda:14,type:"LEAN LDF", swing_idx:0.50,minority_pct:35,ezhava_pct:10,christian_pct:8, incumbent:"LDF",margin21:11200},
];

const SIGNALS=[
  {key:"inflation_anger",    label:"Inflation Anger",        default:7, tip:"Local price rise intensity (0=low, 10=severe)"},
  {key:"candidate_strength", label:"UDF Candidate Strength", default:6, tip:"Quality & recognition of UDF candidate"},
  {key:"nda_spoiler_risk",   label:"NDA Spoiler Risk",       default:5, tip:"How much NDA splits anti-LDF vote"},
  {key:"minority_consolid",  label:"Minority Consolidation", default:7, tip:"How solidly Muslim/Christian vote goes UDF"},
  {key:"cadre_fatigue",      label:"LDF Cadre Fatigue",      default:6, tip:"Degree of LDF worker disenchantment"},
  {key:"youth_mobilization", label:"Youth Mobilisation",     default:5, tip:"Effectiveness of UDF's first-time voter drive"},
  {key:"anti_incumbency",    label:"Anti-Incumbency Wave",   default:7, tip:"Local anti-LDF sentiment strength"},
  {key:"rahul_factor",       label:"Rahul Gandhi Effect",    default:7, tip:"Rahul brand resonance in this constituency"},
];

function buildPrompt(seat,signals){
  return `You are a senior AI political analyst for the 2026 Kerala Assembly Elections, acting as the AI brain of a UDF War Room.

CONSTITUENCY PROFILE:
- Name: ${seat.name}, District: ${seat.dist}
- 2021 Incumbent: ${seat.incumbent} (won by ~${seat.margin21.toLocaleString()} votes)
- Base Vote Share: UDF ${seat.base_udf}% | LDF ${seat.base_ldf}% | NDA ${seat.base_nda}%
- Type: ${seat.type} | Swing Index: ${seat.swing_idx}
- Community Mix: Minority ${seat.minority_pct}% | Ezhava ${seat.ezhava_pct}% | Christian ${seat.christian_pct}%

INTELLIGENCE SIGNALS (0-10):
${SIGNALS.map(s=>`- ${s.label}: ${signals[s.key]}/10`).join('\n')}

MACRO CONTEXT:
- Kerala inflation 9.49% — India #1 for 7 consecutive months
- UDF swept Dec 2025 local bodies: 43% vs LDF 40%
- LDF seeking unprecedented 3rd consecutive term (no front has done this in 65 years)
- NDA structural spoiler in South/Central Kerala
- CM preference: Vijayan 27.85% vs Satheesan 27.77% — near-tied
- Rahul Gandhi: 44.2% national influence among Kerala voters

Respond ONLY in this exact JSON (no markdown, no extra text):
{
  "win_probability_udf": <integer 0-100>,
  "projected_margin": "<string like '+3,200 votes'>",
  "swing_direction": "<'UDF_GAIN'|'LDF_HOLD'|'NDA_SPOILER'|'UDF_SAFE'>",
  "confidence": "<'HIGH'|'MEDIUM'|'LOW'>",
  "risk_level": "<'CRITICAL'|'HIGH'|'MEDIUM'|'LOW'>",
  "headline": "<one sharp sentence summarizing the prediction>",
  "key_factors": ["<factor 1>","<factor 2>","<factor 3>"],
  "top_threat": "<single biggest threat to UDF>",
  "top_opportunity": "<single biggest UDF opportunity>",
  "tactical_actions": ["<action 1>","<action 2>","<action 3>"],
  "vote_shift_estimate": {"udf_adjusted":<int>,"ldf_adjusted":<int>,"nda_adjusted":<int>},
  "scenario_best": "<best case for UDF>",
  "scenario_worst": "<worst case for UDF>",
  "analyst_note": "<2 sentence sharp analytical insight>"
}`;
}

function Slider({sig,value,onChange}){
  const pct=(value/10)*100;
  const color=pct>66?T.green:pct>33?T.amber:T.ldf;
  return(
    <div style={{marginBottom:14}}>
      <div style={{display:"flex",justifyContent:"space-between",marginBottom:5}}>
        <div>
          <div style={{fontSize:11,color:T.text,fontWeight:600}}>{sig.label}</div>
          <div style={{fontSize:9,color:T.muted,marginTop:1,maxWidth:190}}>{sig.tip}</div>
        </div>
        <div style={{textAlign:"right"}}>
          <span style={{fontSize:20,fontWeight:800,color,fontFamily:"monospace",textShadow:`0 0 12px ${color}60`}}>{value}</span>
          <span style={{fontSize:9,color:T.muted}}>/10</span>
        </div>
      </div>
      <div style={{position:"relative",height:6,background:T.dim,borderRadius:3,cursor:"pointer"}}
        onClick={e=>{
          const rect=e.currentTarget.getBoundingClientRect();
          onChange(Math.round(((e.clientX-rect.left)/rect.width)*10));
        }}>
        <div style={{width:`${pct}%`,height:"100%",background:color,borderRadius:3,boxShadow:`0 0 8px ${color}80`,transition:"width 0.15s"}}/>
        <div style={{position:"absolute",top:"50%",left:`${pct}%`,transform:"translate(-50%,-50%)",width:14,height:14,borderRadius:"50%",background:color,border:`2px solid ${T.bg}`,boxShadow:`0 0 10px ${color}`,cursor:"grab",zIndex:2}}/>
      </div>
    </div>
  );
}

function ProbabilityArc({value,color}){
  const r=58,cx=80,cy=80;
  const circumference=Math.PI*r;
  const dashOffset=circumference*(1-value/100);
  const angle=Math.PI*(value/100);
  const dotX=cx+r*Math.cos(Math.PI-angle);
  const dotY=cy-r*Math.sin(Math.PI-angle)+r;
  return(
    <svg width="160" height="100" viewBox="0 0 160 100">
      <defs>
        <linearGradient id="speArcGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={T.ldf}/><stop offset="50%" stopColor={T.amber}/><stop offset="100%" stopColor={T.green}/>
        </linearGradient>
        <filter id="speGlow"><feGaussianBlur stdDeviation="2" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <path d={`M ${cx-r} ${cy} A ${r} ${r} 0 0 1 ${cx+r} ${cy}`} fill="none" stroke={T.dim} strokeWidth="6" strokeLinecap="round"/>
      <path d={`M ${cx-r} ${cy} A ${r} ${r} 0 0 1 ${cx+r} ${cy}`} fill="none" stroke="url(#speArcGrad)" strokeWidth="6" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={dashOffset} filter="url(#speGlow)" style={{transition:"stroke-dashoffset 0.8s ease"}}/>
      <circle cx={dotX} cy={dotY} r="7" fill={color} stroke={T.bg} strokeWidth="2" filter="url(#speGlow)" style={{transition:"all 0.8s ease"}}/>
      <text x={cx} y={cy+2} textAnchor="middle" fontSize="26" fontWeight="800" fill={color} fontFamily="monospace" filter="url(#speGlow)">{value}%</text>
      <text x={cx} y={cy+18} textAnchor="middle" fontSize="9" fill={T.muted} fontFamily="monospace">WIN PROB</text>
    </svg>
  );
}

function Tag({label,color}){
  return <span style={{fontSize:9,padding:"2px 8px",borderRadius:20,background:`${color}18`,color,border:`1px solid ${color}35`,fontFamily:"monospace",letterSpacing:1,whiteSpace:"nowrap"}}>{label}</span>;
}

function StreamText({text}){
  const [d,setD]=useState("");
  const idx=useRef(0);
  useEffect(()=>{
    idx.current=0;setD("");
    if(!text)return;
    const id=setInterval(()=>{if(idx.current<text.length){setD(text.slice(0,++idx.current));}else clearInterval(id);},8);
    return()=>clearInterval(id);
  },[text]);
  return <span>{d}</span>;
}

function PulseDot({color=T.green}){
  const [b,setB]=useState(true);
  useEffect(()=>{const t=setInterval(()=>setB(x=>!x),700);return()=>clearInterval(t);},[]);
  return <div style={{width:8,height:8,borderRadius:"50%",background:b?color:`${color}55`,boxShadow:b?`0 0 8px ${color}`:"none",transition:"all 0.4s",flexShrink:0}}/>;
}

export default function SwingPredictionEngine(){
  const [seat,setSeat]=useState(CONSTITUENCIES[0]);
  const [signals,setSignals]=useState(Object.fromEntries(SIGNALS.map(s=>[s.key,s.default])));
  const [result,setResult]=useState(null);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState(null);
  const [loadMsg,setLoadMsg]=useState("");

  const MSGS=["📡 Ingesting constituency intelligence...","🧠 Calibrating voter segment models...","⚙️ Running swing probability engine...","📊 Synthesizing multi-factor prediction...","🎯 Generating tactical recommendations..."];

  const run=async()=>{
    setLoading(true);setResult(null);setError(null);
    let mi=0;setLoadMsg(MSGS[0]);
    const msgId=setInterval(()=>{mi=Math.min(mi+1,MSGS.length-1);setLoadMsg(MSGS[mi]);},1200);
    try{
      const apiKey=import.meta.env.VITE_OPENAI_API_KEY;
      if(!apiKey){throw new Error("VITE_ANTHROPIC_API_KEY not set in .env file. See README.md for setup.");}
      const resp=await fetch("https://api.openai.com/v1/chat/completions",{
        method:"POST",
        headers:{
          "Content-Type":"application/json",
          // "x-api-key":apiKey,
          // "anthropic-version":"2023-06-01",
          // "anthropic-dangerous-direct-browser-access":"true",
          "Authorization": `Bearer ${apiKey}`,
        },
        body:JSON.stringify({
          model: "gpt-4o",
                      max_tokens: 1000,
                      messages: [
                        { role: "system", content: "You are a senior AI political analyst for Kerala elections 2026. Respond ONLY with valid JSON, no markdown, no backticks." },
                        { role: "user", content: buildPrompt(seat, signals) }
                      ]
        })
      });
      const data=await resp.json();
      clearInterval(msgId);
      if(data.error)throw new Error(data.error.message);

      const raw = data.choices[0].message.content.trim();
      const cleaned = raw.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
      const parsed = JSON.parse(cleaned);
      setResult(parsed);
    }catch(e){
      clearInterval(msgId);
      setError(e.message);
    }finally{setLoading(false);}
  };

  const winColor=result?(result.win_probability_udf>=60?T.green:result.win_probability_udf>=45?T.amber:T.ldf):T.udf;
  const riskColor=r=>r==="CRITICAL"?T.ldf:r==="HIGH"?T.nda:r==="MEDIUM"?T.amber:T.green;
  const confColor=c=>c==="HIGH"?T.green:c==="MEDIUM"?T.amber:T.ldf;

  return(
    <div style={{background:T.bg,color:T.text,fontFamily:"'Courier New',monospace",fontSize:13}}>
      <style>{`
        @keyframes spin{to{transform:rotate(360deg)}}
        @keyframes speSlideUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
        @keyframes speScan{0%{opacity:0.3}50%{opacity:1}100%{opacity:0.3}}
      `}</style>

      {/* Sub-header */}
      <div style={{background:"#070F1E",borderBottom:`1px solid ${T.border}`,padding:"10px 20px",display:"flex",alignItems:"center",justifyContent:"space-between",flexWrap:"wrap",gap:8}}>
        <div>
          <div style={{fontSize:13,fontWeight:700,letterSpacing:2,color:T.udf}}>🤖 AI SWING PREDICTION ENGINE</div>
          <div style={{fontSize:9,color:T.muted,letterSpacing:1}}>Select constituency · Tune signals · Run Claude AI prediction</div>
        </div>
        <div style={{display:"flex",gap:8}}>
          <div style={{display:"flex",alignItems:"center",gap:6,background:`${T.green}12`,border:`1px solid ${T.green}30`,borderRadius:6,padding:"5px 10px"}}>
            <PulseDot color={T.green}/><span style={{fontSize:10,color:T.green,letterSpacing:1}}>CLAUDE SONNET 4</span>
          </div>
          <div style={{background:`${T.udf}12`,border:`1px solid ${T.udf}30`,borderRadius:6,padding:"5px 10px"}}>
            <span style={{fontSize:10,color:T.udf}}>{CONSTITUENCIES.length} SEATS LOADED</span>
          </div>
        </div>
      </div>

      <div style={{display:"grid",gridTemplateColumns:"320px 1fr",minHeight:"calc(100vh - 130px)"}}>

        {/* LEFT — Controls */}
        <div style={{borderRight:`1px solid ${T.border}`,overflowY:"auto",padding:14}}>
          {/* Seat list */}
          <div style={{marginBottom:16}}>
            <div style={{fontSize:9,color:T.muted,letterSpacing:2,textTransform:"uppercase",marginBottom:8}}>SELECT CONSTITUENCY</div>
            <div style={{display:"grid",gap:3}}>
              {CONSTITUENCIES.map((c,i)=>{
                const sel=seat.name===c.name;
                const tc=c.type==="TOSS-UP"?T.amber:c.type==="LEAN UDF"?T.green:c.type==="SAFE UDF"?T.udf:c.type==="LEAN NDA"?T.nda:T.ldf;
                return(
                  <div key={i} onClick={()=>{setSeat(c);setResult(null);setError(null);}} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"7px 11px",borderRadius:6,background:sel?`${T.udf}12`:"transparent",border:`1px solid ${sel?T.udf+"40":T.border+"80"}`,cursor:"pointer",transition:"all 0.15s"}}>
                    <div>
                      <div style={{fontSize:11,fontWeight:700,color:sel?T.udf:T.text}}>{c.name}</div>
                      <div style={{fontSize:9,color:T.muted}}>{c.dist}</div>
                    </div>
                    <div style={{display:"flex",flexDirection:"column",alignItems:"flex-end",gap:2}}>
                      <span style={{fontSize:8,color:tc,border:`1px solid ${tc}40`,borderRadius:10,padding:"1px 6px",background:`${tc}12`}}>{c.type}</span>
                      <span style={{fontSize:9,color:T.muted,fontFamily:"monospace"}}>SI:{c.swing_idx}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Seat profile */}
          <div style={{background:`${T.udf}08`,border:`1px solid ${T.udf}20`,borderRadius:8,padding:"12px 14px",marginBottom:16}}>
            <div style={{fontSize:9,color:T.udf,letterSpacing:2,marginBottom:8}}>SEAT PROFILE</div>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:5,marginBottom:8}}>
              {[["UDF",seat.base_udf,T.udf],["LDF",seat.base_ldf,T.ldf],["NDA",seat.base_nda,T.nda]].map(([l,v,c])=>(
                <div key={l} style={{textAlign:"center",background:T.panel,borderRadius:5,padding:"6px 4px"}}>
                  <div style={{fontSize:8,color:T.muted}}>{l}</div>
                  <div style={{fontSize:16,fontWeight:800,color:c,fontFamily:"monospace"}}>{v}%</div>
                </div>
              ))}
            </div>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:4,fontSize:9}}>
              {[["Incumbent",seat.incumbent],["2021 Margin",seat.margin21.toLocaleString()],["Swing Index",seat.swing_idx],["Minority %",`${seat.minority_pct}%`]].map(([l,v])=>(
                <div key={l} style={{display:"flex",justifyContent:"space-between",padding:"3px 6px",background:T.panel,borderRadius:4}}>
                  <span style={{color:T.muted}}>{l}</span>
                  <span style={{color:T.text,fontFamily:"monospace"}}>{v}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Signals */}
          <div style={{marginBottom:16}}>
            <div style={{fontSize:9,color:T.muted,letterSpacing:2,textTransform:"uppercase",marginBottom:10}}>INTELLIGENCE SIGNALS</div>
            {SIGNALS.map(sig=><Slider key={sig.key} sig={sig} value={signals[sig.key]} onChange={v=>setSignals(p=>({...p,[sig.key]:Math.max(0,Math.min(10,v))}))}/>)}
          </div>

          <button onClick={run} disabled={loading} style={{width:"100%",padding:"14px",borderRadius:8,background:loading?T.dim:`linear-gradient(135deg,${T.udf},#0088CC)`,border:"none",color:"#fff",fontSize:12,fontWeight:700,letterSpacing:2,cursor:loading?"not-allowed":"pointer",fontFamily:"'Courier New',monospace",textTransform:"uppercase",boxShadow:loading?"none":`0 0 20px ${T.udf}40`,transition:"all 0.3s"}}>
            {loading?"⚙️ ANALYZING...":"🤖 RUN AI PREDICTION"}
          </button>
        </div>

        {/* RIGHT — Results */}
        <div style={{overflowY:"auto",padding:16}}>

          {!loading&&!result&&!error&&(
            <div style={{display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",minHeight:400,textAlign:"center",opacity:0.5}}>
              <div style={{fontSize:48,marginBottom:16}}>🎯</div>
              <div style={{fontSize:14,color:T.muted,letterSpacing:2}}>SELECT A CONSTITUENCY</div>
              <div style={{fontSize:11,color:T.dim,marginTop:8}}>Adjust intelligence signals and run AI prediction</div>
            </div>
          )}

          {loading&&(
            <div style={{display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",minHeight:400}}>
              <div style={{width:64,height:64,borderRadius:"50%",border:`2px solid ${T.border}`,borderTop:`2px solid ${T.udf}`,animation:"spin 1s linear infinite",marginBottom:20,boxShadow:`0 0 20px ${T.udf}30`}}/>
              <div style={{fontSize:13,color:T.udf,letterSpacing:1,animation:"speScan 1.5s ease-in-out infinite",textAlign:"center",maxWidth:300}}>{loadMsg}</div>
              <div style={{fontSize:10,color:T.muted,marginTop:10}}>Analyzing {seat.name} · {seat.dist}</div>
            </div>
          )}

          {error&&(
            <div style={{background:`${T.ldf}10`,border:`1px solid ${T.ldf}30`,borderRadius:8,padding:20,margin:10}}>
              <div style={{fontSize:12,color:T.ldf,marginBottom:8}}>⚠️ PREDICTION ENGINE ERROR</div>
              <div style={{fontSize:11,color:T.muted,lineHeight:1.6}}>{error}</div>
              {error.includes("VITE_ANTHROPIC_API_KEY")&&(
                <div style={{marginTop:12,background:`${T.udf}10`,border:`1px solid ${T.udf}30`,borderRadius:6,padding:"10px 12px"}}>
                  <div style={{fontSize:10,color:T.udf,marginBottom:6}}>📋 SETUP REQUIRED</div>
                  <div style={{fontSize:10,color:T.text,lineHeight:1.7,fontFamily:"monospace"}}>
                    1. Create <span style={{color:T.amber}}>frontend/.env</span><br/>
                    2. Add: <span style={{color:T.green}}>VITE_ANTHROPIC_API_KEY=sk-ant-...</span><br/>
                    3. Restart: <span style={{color:T.amber}}>npm run dev</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {result&&!loading&&(
            <div style={{animation:"speSlideUp 0.4s ease"}}>
              {/* Top card */}
              <div style={{background:`linear-gradient(135deg,${T.card},${T.panel})`,border:`1px solid ${winColor}30`,borderRadius:12,padding:20,marginBottom:14,boxShadow:`0 0 30px ${winColor}15`}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",flexWrap:"wrap",gap:16}}>
                  <div style={{flex:1}}>
                    <div style={{fontSize:10,color:T.muted,letterSpacing:2,marginBottom:6}}>{seat.name.toUpperCase()} · {seat.dist.toUpperCase()}</div>
                    <div style={{fontSize:15,fontWeight:700,color:T.text,lineHeight:1.5,maxWidth:400}}><StreamText text={result.headline}/></div>
                    <div style={{display:"flex",gap:8,marginTop:12,flexWrap:"wrap"}}>
                      <Tag label={result.swing_direction} color={winColor}/>
                      <Tag label={`RISK: ${result.risk_level}`} color={riskColor(result.risk_level)}/>
                      <Tag label={`CONF: ${result.confidence}`} color={confColor(result.confidence)}/>
                    </div>
                  </div>
                  <div style={{display:"flex",flexDirection:"column",alignItems:"center"}}>
                    <ProbabilityArc value={result.win_probability_udf} color={winColor}/>
                    <div style={{fontSize:12,fontWeight:700,color:winColor,marginTop:4}}>{result.projected_margin}</div>
                    <div style={{fontSize:9,color:T.muted}}>projected margin</div>
                  </div>
                </div>
              </div>

              {/* Adjusted shares */}
              <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:10,marginBottom:14}}>
                {[["UDF Adjusted",result.vote_shift_estimate?.udf_adjusted,T.udf],["LDF Adjusted",result.vote_shift_estimate?.ldf_adjusted,T.ldf],["NDA Adjusted",result.vote_shift_estimate?.nda_adjusted,T.nda]].map(([l,v,c])=>(
                  <div key={l} style={{background:T.card,border:`1px solid ${c}25`,borderRadius:8,padding:"12px 14px"}}>
                    <div style={{fontSize:9,color:T.muted,marginBottom:4}}>{l}</div>
                    <div style={{fontSize:26,fontWeight:800,color:c,fontFamily:"monospace",textShadow:`0 0 12px ${c}50`}}>{v}%</div>
                    <div style={{height:3,background:T.dim,borderRadius:2,marginTop:8}}>
                      <div style={{width:`${v}%`,height:"100%",background:c,boxShadow:`0 0 6px ${c}60`}}/>
                    </div>
                  </div>
                ))}
              </div>

              {/* Grid cards */}
              <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(280px,1fr))",gap:12}}>
                {/* Key factors */}
                <div style={{background:T.card,border:`1px solid ${T.border}`,borderRadius:8,padding:14}}>
                  <div style={{fontSize:9,fontWeight:700,color:T.muted,letterSpacing:2,marginBottom:12,textTransform:"uppercase"}}>KEY DETERMINING FACTORS</div>
                  {(result.key_factors||[]).map((f,i)=>(
                    <div key={i} style={{display:"flex",gap:10,marginBottom:10,alignItems:"flex-start"}}>
                      <div style={{width:20,height:20,borderRadius:5,background:`${T.udf}15`,border:`1px solid ${T.udf}30`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:10,color:T.udf,flexShrink:0,fontFamily:"monospace",fontWeight:700}}>{i+1}</div>
                      <div style={{fontSize:11,color:T.text,lineHeight:1.5}}>{f}</div>
                    </div>
                  ))}
                </div>

                {/* Tactical actions */}
                <div style={{background:T.card,border:`1px solid ${T.border}`,borderRadius:8,padding:14}}>
                  <div style={{fontSize:9,fontWeight:700,color:T.muted,letterSpacing:2,marginBottom:12,textTransform:"uppercase"}}>TACTICAL ACTIONS FOR UDF</div>
                  {(result.tactical_actions||[]).map((a,i)=>(
                    <div key={i} style={{display:"flex",gap:10,marginBottom:10,alignItems:"flex-start"}}>
                      <span style={{fontSize:14,flexShrink:0}}>{i===0?"🎯":i===1?"⚡":"🛡️"}</span>
                      <div style={{fontSize:11,color:T.text,lineHeight:1.5}}>{a}</div>
                    </div>
                  ))}
                </div>

                {/* Threat & Opportunity */}
                <div style={{background:T.card,border:`1px solid ${T.border}`,borderRadius:8,padding:14}}>
                  <div style={{marginBottom:14}}>
                    <div style={{fontSize:9,color:T.ldf,letterSpacing:2,marginBottom:6}}>⚠️ TOP THREAT</div>
                    <div style={{fontSize:11,color:T.text,lineHeight:1.6,background:`${T.ldf}08`,borderRadius:5,padding:"8px 10px",border:`1px solid ${T.ldf}20`}}>{result.top_threat}</div>
                  </div>
                  <div>
                    <div style={{fontSize:9,color:T.green,letterSpacing:2,marginBottom:6}}>💡 TOP OPPORTUNITY</div>
                    <div style={{fontSize:11,color:T.text,lineHeight:1.6,background:`${T.green}08`,borderRadius:5,padding:"8px 10px",border:`1px solid ${T.green}20`}}>{result.top_opportunity}</div>
                  </div>
                </div>

                {/* Scenarios */}
                <div style={{background:T.card,border:`1px solid ${T.border}`,borderRadius:8,padding:14}}>
                  <div style={{marginBottom:14}}>
                    <div style={{fontSize:9,color:T.green,letterSpacing:2,marginBottom:6}}>🏆 BEST CASE</div>
                    <div style={{fontSize:11,color:T.text,lineHeight:1.6,background:`${T.green}08`,borderRadius:5,padding:"8px 10px",border:`1px solid ${T.green}20`}}>{result.scenario_best}</div>
                  </div>
                  <div>
                    <div style={{fontSize:9,color:T.ldf,letterSpacing:2,marginBottom:6}}>💀 WORST CASE</div>
                    <div style={{fontSize:11,color:T.text,lineHeight:1.6,background:`${T.ldf}08`,borderRadius:5,padding:"8px 10px",border:`1px solid ${T.ldf}20`}}>{result.scenario_worst}</div>
                  </div>
                </div>
              </div>

              {/* Analyst note */}
              {result.analyst_note&&(
                <div style={{marginTop:14,background:`linear-gradient(135deg,${T.udf}08,${T.panel})`,border:`1px solid ${T.udf}25`,borderRadius:8,padding:"14px 16px",display:"flex",gap:12,alignItems:"flex-start"}}>
                  <span style={{fontSize:20,flexShrink:0}}>🧠</span>
                  <div>
                    <div style={{fontSize:9,color:T.udf,letterSpacing:2,marginBottom:6}}>ANALYST NOTE</div>
                    <div style={{fontSize:12,color:T.text,lineHeight:1.7,fontStyle:"italic"}}>{result.analyst_note}</div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
