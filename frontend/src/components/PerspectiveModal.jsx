import { useState } from "react";
import { X, ExternalLink, Volume2, Info, Shield } from "lucide-react";
import axios from "axios";
import DeepAnalysis from "./DeepAnalysis";
import ExplainPolarization from "./ExplainPolarization";
import NarrativeTimeline from "./NarrativeTimeline";

const PC = ["#15803d", "#b91c1c", "#1d4ed8"];
const PE = ["\u{1F7E2}", "\u{1F534}", "\u{1F535}"];

export default function PerspectiveModal({ story, onClose, apiBase }) {
  const [vl, setVl] = useState(false);
  const [tab, setTab] = useState("perspectives");

  const say = async (text, lang = "en") => {
    if (vl) return; setVl(true);
    try {
      const r = await axios.get(`${apiBase}/api/tts?text=${encodeURIComponent(text.slice(0, 500))}&lang=${lang}`, { responseType: "blob", timeout: 25000 });
      const a = new Audio(URL.createObjectURL(r.data)); a.play(); a.onended = () => setVl(false);
    } catch { setVl(false); }
  };
  const p = story.polarization;
  const pc = p.score > 65 ? "#b91c1c" : p.score > 45 ? "#a16207" : p.score > 25 ? "#666" : "#15803d";

  const TABS = [
    { key: "perspectives", label: "Perspectives" },
    { key: "explain", label: "⚡ Why Polarized" },
    { key: "deep", label: "🔍 Deep Analysis" },
    { key: "timeline", label: "📊 Timeline" },
  ];

  return (
    <div onClick={onClose} style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)",
      display: "flex", justifyContent: "center", alignItems: "flex-start",
      zIndex: 1000, padding: "16px", overflowY: "auto",
      backdropFilter: "blur(4px)", animation: "fadeIn 0.2s ease",
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        background: "#fff", borderRadius: 14, maxWidth: 860, width: "100%",
        boxShadow: "0 24px 80px rgba(0,0,0,0.15)", marginBottom: 40, animation: "fadeUp 0.25s ease",
      }}>
        {/* Header */}
        <div style={{ padding: "16px 24px", borderBottom: "2px solid #111", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div style={{ flex: 1, marginRight: 16 }}>
            <h2 className="serif" style={{ fontSize: 22, fontWeight: 700, color: "#111", marginBottom: 8, lineHeight: 1.3 }}>{story.headline}</h2>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              <T c={story.is_adverse ? "#b91c1c" : "#15803d"} bg={story.is_adverse ? "#fef2f2" : "#f0fdf4"}>{story.is_adverse ? "⚠ ADVERSE" : "✓ NON-ADVERSE"}</T>
              <T c="#111" bg="#f5f5f5">{story.category}</T>
              <T c="#666" bg="#fafafa">{story.severity} severity</T>
              <span style={{ fontSize: 12, color: "#555" }}>{story.source_count} sources</span>
              {story.credibility_weighted_pol != null && (
                <T c="#1d4ed8" bg="#eff6ff">Cred-weighted: {story.credibility_weighted_pol}/100</T>
              )}
            </div>
          </div>
          <button onClick={onClose} className="abtn" style={{ background: "#f5f5f5", border: "1px solid #eee", borderRadius: 8, padding: 6 }}>
            <X size={18} color="#888" />
          </button>
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", borderBottom: "1px solid #eee", padding: "0 24px", overflowX: "auto" }}>
          {TABS.map(t => (
            <button key={t.key} onClick={() => setTab(t.key)} style={{
              padding: "10px 16px", border: "none", background: "transparent",
              fontSize: 12, fontWeight: tab === t.key ? 700 : 400,
              color: tab === t.key ? "#111" : "#888",
              borderBottom: tab === t.key ? "2px solid #111" : "2px solid transparent",
              cursor: "pointer", whiteSpace: "nowrap",
            }}>{t.label}</button>
          ))}
        </div>

        <div style={{ padding: "20px 24px" }}>

          {/* TAB: Perspectives */}
          {tab === "perspectives" && (
            <>
              {/* Polarization */}
              <div style={{ background: "#fafafa", borderRadius: 12, padding: "16px 20px", marginBottom: 20, border: "1px solid #eee" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 12 }}>
                  <div style={{ width: 52, height: 52, borderRadius: 12, background: pc, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: 20, fontWeight: 900, fontFamily: "Georgia" }}>{p.score}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 15, fontWeight: 700, color: "#111" }}>Polarization Index — {p.level}</div>
                    <div style={{ fontSize: 12, color: "#555", marginTop: 2 }}>{p.insight}</div>
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8 }}><G l="Sentiment" v={p.components.sentiment_variance} /><G l="Language Bias" v={p.components.language_bias} /><G l="Divergence" v={p.components.content_divergence} /></div>
              </div>

              {/* Source Credibility */}
              {story.source_credibility?.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                  <h4 style={{ fontSize: 11, fontWeight: 800, color: "#111", textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>Source Credibility Weights</h4>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {story.source_credibility.map((sc, i) => (
                      <div key={i} style={{ background: "#fafafa", border: "1px solid #eee", borderRadius: 6, padding: "6px 10px", fontSize: 11, display: "flex", alignItems: "center", gap: 6 }}>
                        <Shield size={10} color={sc.credibility > 0.8 ? "#15803d" : sc.credibility > 0.6 ? "#a16207" : "#b91c1c"} />
                        <span style={{ fontWeight: 600, color: "#111" }}>{sc.source}</span>
                        <span style={{ color: "#888" }}>{Math.round(sc.credibility * 100)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Key Facts */}
              {story.key_facts && <Sec t="Key Facts">
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                  {Object.entries(story.key_facts).map(([k, v]) => v && v !== "N/A" ? (
                    <div key={k} style={{ background: "#fafafa", padding: "10px 14px", borderRadius: 8, border: "1px solid #eee" }}>
                      <div style={{ fontWeight: 700, textTransform: "uppercase", fontSize: 9, color: "#aaa", marginBottom: 2, letterSpacing: 0.5 }}>{k}</div>
                      <div style={{ color: "#222", fontSize: 13, lineHeight: 1.5 }}>{v}</div>
                    </div>
                  ) : null)}
                </div>
              </Sec>}

              {/* Perspectives */}
              {story.perspectives?.length > 0 && <Sec t="Multiple Viewpoints">
                {story.perspectives.map((pr, i) => (
                  <div key={i} className="pcard" style={{ background: "#fafafa", borderLeft: `3px solid ${PC[i%3]}`, borderRadius: "0 10px 10px 0", padding: "14px 18px", marginBottom: 10 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                      <span style={{ fontWeight: 700, fontSize: 14, color: PC[i%3] }}>{PE[i%3]} {pr.label}</span>
                      <div style={{ display: "flex", gap: 3 }}>
                        {[["en","EN"],["hi","HI"],["es","ES"],["fr","FR"]].map(([c,l]) => (
                          <button key={c} onClick={() => say(`${pr.label}. ${pr.summary}`,c)} disabled={vl} className="abtn" style={{ background:"#fff",border:"1px solid #eee",borderRadius:5,padding:"2px 7px",fontSize:9,color:"#888" }}><Volume2 size={8}/> {l}</button>
                        ))}
                      </div>
                    </div>
                    <p style={{ fontSize: 14, lineHeight: 1.7, color: "#333" }}>{pr.summary}</p>
                    {pr.emphasis && <p style={{ fontSize: 12, marginTop: 4, color: "#888", fontStyle: "italic" }}>Focus: {pr.emphasis}</p>}
                  </div>
                ))}
              </Sec>}

              {/* Source Analysis */}
              {story.source_analysis?.length > 0 && <Sec t="Source Analysis">
                {story.source_analysis.map((sa, i) => (
                  <div key={i} className="pcard" style={{ background:"#fafafa",borderRadius:8,padding:"12px 16px",marginBottom:6,border:"1px solid #eee" }}>
                    <div style={{ display:"flex",justifyContent:"space-between",marginBottom:4 }}>
                      <span style={{ fontWeight:600,fontSize:13,color:"#111" }}>{sa.source_name}</span>
                      <TP t={sa.tone} />
                    </div>
                    {sa.framing_note && !sa.framing_note.includes("pending") && <p style={{ fontSize:12,color:"#555",marginBottom:4,lineHeight:1.5 }}>{sa.framing_note}</p>}
                    {sa.loaded_phrases?.length > 0 && <div style={{ display:"flex",gap:4,flexWrap:"wrap",marginBottom:6 }}>{sa.loaded_phrases.slice(0,5).map((ph,j)=><span key={j} style={{ fontSize:10,background:"#fef2f2",color:"#991b1b",padding:"2px 8px",borderRadius:4,border:"1px solid #fecaca" }}>"{ph}"</span>)}</div>}
                    <div style={{ marginTop:4 }}>
                      <div style={{ display:"flex",justifyContent:"space-between",fontSize:10,color:"#aaa" }}><span>Bias</span><span style={{ fontWeight:700,color:"#666" }}>{Math.round((sa.bias_score||0)*100)}%</span></div>
                      <div style={{ width:"100%",height:3,background:"#eee",borderRadius:2,marginTop:3 }}><div style={{ width:`${(sa.bias_score||0)*100}%`,height:"100%",background:(sa.bias_score||0)>0.5?"#b91c1c":(sa.bias_score||0)>0.25?"#a16207":"#15803d",borderRadius:2 }}/></div>
                    </div>
                  </div>
                ))}
              </Sec>}

              {/* Original Sources */}
              {story.original_articles?.length > 0 && <Sec t="Read Sources">
                {story.original_articles.map((a,i)=>(
                  <a key={i} href={a.url} target="_blank" rel="noopener noreferrer" className="slink" style={{ display:"flex",justifyContent:"space-between",alignItems:"center",padding:"10px 14px",background:"#fafafa",borderRadius:8,color:"#222",textDecoration:"none",fontSize:13,marginBottom:4,border:"1px solid #eee" }}>
                    <span><strong style={{ color:"#111" }}>{a.source}</strong> — {a.title.slice(0,55)}...</span>
                    <ExternalLink size={12} color="#bbb" />
                  </a>
                ))}
              </Sec>}
            </>
          )}

          {/* TAB: Explain Polarization */}
          {tab === "explain" && <ExplainPolarization story={story} />}

          {/* TAB: Deep Analysis */}
          {tab === "deep" && <DeepAnalysis story={story} />}

          {/* TAB: Timeline */}
          {tab === "timeline" && <NarrativeTimeline story={story} />}
        </div>
      </div>
    </div>
  );
}

function Sec({t,children}){return <div style={{marginBottom:22}}><h3 style={{fontSize:12,fontWeight:700,marginBottom:10,color:"#111",textTransform:"uppercase",letterSpacing:1}}>{t}</h3>{children}</div>}
function T({children,c,bg}){return <span style={{fontSize:10,padding:"3px 10px",borderRadius:6,background:bg,color:c,fontWeight:700}}>{children}</span>}
function TP({t}){const c=t==="positive"?"#15803d":t==="negative"?"#b91c1c":"#888";return <span style={{fontSize:10,padding:"2px 8px",borderRadius:6,background:"#fafafa",color:c,fontWeight:600,border:"1px solid #eee"}}>{t}</span>}
function G({l,v}){const c=v>50?"#b91c1c":v>25?"#a16207":"#15803d";return(<div style={{flex:1,background:"#fff",borderRadius:8,padding:"8px 12px",border:"1px solid #eee"}}><div style={{fontSize:9,color:"#aaa",marginBottom:4}}>{l}</div><div style={{width:"100%",height:3,background:"#eee",borderRadius:2}}><div style={{width:`${v}%`,height:"100%",background:c,borderRadius:2}}/></div><div style={{fontSize:12,fontWeight:700,color:c,marginTop:3}}>{v}%</div></div>)}
