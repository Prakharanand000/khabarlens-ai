import { useState, useEffect, useRef } from "react";
import axios from "axios";
import NewsCard from "./components/NewsCard";
import PerspectiveModal from "./components/PerspectiveModal";
import Sidebar from "./components/Sidebar";
import OpinionColumn from "./components/OpinionColumn";
import ArticleAnalyzer from "./components/ArticleAnalyzer";
import MostPolarized from "./components/MostPolarized";
import AiChat from "./components/AiChat";
import { RefreshCw, Search, Volume2, VolumeX, X, Globe, TrendingUp, ChevronLeft, ChevronRight } from "lucide-react";

const API = "https://khabarlens-backend.onrender.com";
const CATS = ["All","Financial Crime","Money Laundering","Fraud & Scams","Insider Trading","Terrorism","Sanctions","Regulatory & Compliance","FINRA & SEC","Human Rights","War Crimes","Crime, Law & Justice","Cybercrime","Drug Trafficking","Corruption","Economy & Markets","Geopolitics","AI & Tech Ethics","Environment","Health","General News"];
const COUNTRIES = [
  { code: "US", flag: "🇺🇸" }, { code: "UK", flag: "🇬🇧" },
  { code: "IN", flag: "🇮🇳" }, { code: "FR", flag: "🇫🇷" },
  { code: "DE", flag: "🇩🇪" }, { code: "JP", flag: "🇯🇵" },
  { code: "WORLD", flag: "🌍" },
];
const QUICK = ["Iran conflict","Trump tariffs","AI regulation","sanctions Russia","SEC enforcement","climate policy","human rights","cybersecurity","stock market","immigration","cryptocurrency","NATO"];
const TAGS = [
  { label: "Adverse Only", isAdverse: true },
  { label: "High Polarization", isPol: true },
  { label: "Financial", search: "financial crime fraud" },
  { label: "Crime", search: "crime law justice" },
  { label: "Sanctions", search: "sanctions" },
  { label: "Human Rights", search: "human rights" },
  { label: "Terrorism", search: "terrorism" },
  { label: "Regulation", search: "SEC FINRA regulation" },
  { label: "Geopolitics", search: "geopolitics war conflict" },
  { label: "AI Ethics", search: "artificial intelligence ethics" },
  { label: "Economy", search: "economy markets" },
  { label: "Cybercrime", search: "cybercrime hacking" },
];
const PER_PAGE = 12;

function localFilter(stories, query) {
  if (!query?.trim()) return stories;
  const words = query.toLowerCase().split(/\s+/).filter(w => w.length > 1);
  return stories.filter(s => {
    const text = [s.headline, s.neutral_summary, s.category, ...(s.topic_tags||[]), ...(s.sources||[]), s.adverse_reason||"", ...(s.original_articles||[]).map(a=>a.title)].join(" ").toLowerCase();
    return words.every(w => text.includes(w));
  });
}

export default function App() {
  const [allStories, setAllStories] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [pageStories, setPageStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [q, setQ] = useState("");
  const [activeSearch, setActiveSearch] = useState("");
  const [searching, setSearching] = useState(false);
  const [cat, setCat] = useState("All");
  const [advOnly, setAdvOnly] = useState(false);
  const [polOnly, setPolOnly] = useState(false);
  const [briefing, setBriefing] = useState(false);
  const [country, setCountry] = useState("US");
  const [searchFocused, setSearchFocused] = useState(false);
  const [page, setPage] = useState(1);
  const [mostPol, setMostPol] = useState(null);
  const bRef = useRef(null);

  const load = async (ctry) => {
    const c = ctry || country;
    setLoading(true); setError(null); setQ(""); setActiveSearch(""); setPage(1);
    try {
      const { data } = await axios.get(`${API}/api/stories?limit=30&country=${c}`, { timeout: 300000 });
      setAllStories(data.all_stories || data.stories || []);
      if (data.most_polarized) setMostPol(data.most_polarized);
    } catch (e) { setError(e.code === "ECONNABORTED" ? "Taking longer..." : "Can't reach backend."); }
    finally { setLoading(false); }
  };

  const switchCountry = (c) => { setCountry(c); load(c); };

  const doSearch = async (e, query) => {
    if (e) e.preventDefault();
    const sq = (query || q).trim();
    if (!sq) return;
    setQ(sq); setActiveSearch(sq); setSearchFocused(false); setPage(1);
    const local = localFilter(allStories, sq);
    if (local.length >= 3) return;
    setSearching(true);
    try {
      const { data } = await axios.get(`${API}/api/search?q=${encodeURIComponent(sq)}&limit=15&country=${country}`, { timeout: 120000 });
      if (data.stories?.length > 0) {
        const existing = new Set(allStories.map(s => s.headline.toLowerCase()));
        const n = data.stories.filter(s => !existing.has(s.headline.toLowerCase()));
        if (n.length > 0) setAllStories(prev => [...prev, ...n]);
      }
    } catch {} finally { setSearching(false); }
  };

  const clearSearch = () => { setQ(""); setActiveSearch(""); setPage(1); };
  const handleTag = (tag) => {
    if (tag.isAdverse) { setAdvOnly(!advOnly); setPage(1); return; }
    if (tag.isPol) { setPolOnly(!polOnly); setPage(1); return; }
    if (tag.search) { doSearch(null, tag.search); return; }
  };

  const playBrief = async () => {
    if (briefing) { if (bRef.current) bRef.current.pause(); setBriefing(false); return; }
    try {
      const { data } = await axios.get(`${API}/api/briefing-text?limit=5`);
      const r = await axios.get(`${API}/api/tts?text=${encodeURIComponent(data.text?.slice(0,900))}&lang=en`, { responseType: "blob", timeout: 30000 });
      const a = new Audio(URL.createObjectURL(r.data));
      bRef.current = a; setBriefing(true); a.play(); a.onended = () => { setBriefing(false); bRef.current = null; };
    } catch { setBriefing(false); }
  };

  useEffect(() => {
    let r = allStories;
    if (cat !== "All") r = r.filter(s => s.category === cat);
    if (advOnly) r = r.filter(s => s.is_adverse);
    if (polOnly) r = r.filter(s => s.polarization.score > 40);
    if (activeSearch) r = localFilter(r, activeSearch);
    setFiltered(r); setPage(1);
  }, [allStories, cat, advOnly, polOnly, activeSearch]);

  useEffect(() => { setPageStories(filtered.slice((page-1)*PER_PAGE, page*PER_PAGE)); }, [filtered, page]);
  useEffect(() => { load(); }, []);
  useEffect(() => { document.body.style.overflow = selected ? "hidden" : ""; return () => { document.body.style.overflow = ""; }; }, [selected]);

  const cc = {}; allStories.forEach(s => { cc[s.category] = (cc[s.category]||0)+1; });
  const advCt = filtered.filter(s => s.is_adverse).length;
  const totalPages = Math.max(1, Math.ceil(filtered.length / PER_PAGE));
  const today = new Date().toLocaleDateString('en-US', { weekday:'long', month:'long', day:'numeric', year:'numeric' });

  // Find the most polarized story object for click handler
  const mostPolStory = allStories.find(s => s.headline === mostPol?.headline);

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar cats={CATS} cc={cc} active={cat} onPick={c=>{setCat(c);setPage(1)}} advOnly={advOnly} toggleAdv={()=>{setAdvOnly(!advOnly);setPage(1)}} advCt={advCt} />

      <main style={{ flex: 1, minWidth: 0 }}>
        <header style={{ background: "#111", padding: "14px 32px 16px", color: "#fff" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
            <span style={{ fontSize: 13, color: "#ccc", fontWeight: 600 }}>{today}</span>
            <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
              <Globe size={13} color="#888" style={{ marginRight: 4 }} />
              {COUNTRIES.map(c=>(
                <button key={c.code} onClick={()=>switchCountry(c.code)} className="abtn" style={{
                  padding:"4px 10px",borderRadius:5,fontSize:12,fontWeight:700,
                  background:country===c.code?"#fff":"transparent",
                  color:country===c.code?"#111":"#bbb",
                  border:country===c.code?"none":"1px solid #444",
                }}>{c.flag} {c.code}</button>
              ))}
            </div>
          </div>
          <div style={{ textAlign: "center", marginBottom: 14 }}>
            <h1 className="serif" style={{ fontSize: 48, fontWeight: 900, color: "#fff", letterSpacing: -1.5 }}>KhabarLens AI</h1>
            <p style={{ fontSize: 12, color: "#aaa", marginTop: 6, letterSpacing: 4, textTransform: "uppercase", fontWeight: 600 }}>Structured · Objective · Multi-Perspective News Intelligence</p>
          </div>
          <div style={{ maxWidth: 760, margin: "0 auto", position: "relative" }}>
            <div style={{ display: "flex", gap: 8 }}>
              <form onSubmit={doSearch} style={{ display: "flex", gap: 6, flex: 1 }}>
                <div className="sbox" style={{ flex:1,display:"flex",alignItems:"center",gap:8,border:"1.5px solid #555",borderRadius:8,padding:"10px 16px",background:"rgba(255,255,255,0.08)" }}>
                  <Search size={16} color="#999" />
                  <input value={q} onChange={e=>{setQ(e.target.value);setActiveSearch(e.target.value)}}
                    onFocus={()=>setSearchFocused(true)} onBlur={()=>setTimeout(()=>setSearchFocused(false),200)}
                    placeholder="Search articles — type to filter instantly..."
                    style={{ flex:1,background:"transparent",border:"none",outline:"none",color:"#fff",fontSize:15,fontWeight:500 }}
                  />
                  {(q||activeSearch)&&<X size={14} color="#888" style={{cursor:"pointer"}} onClick={clearSearch}/>}
                </div>
                <button type="submit" disabled={searching} style={{ background:"#fff",border:"none",color:"#111",padding:"10px 24px",borderRadius:8,fontSize:14,fontWeight:700 }}>{searching?"...":"Search"}</button>
              </form>
              <button onClick={()=>load()} disabled={loading} className="abtn" style={{ padding:"10px 14px",border:"1px solid #555",borderRadius:8,background:"transparent" }}><RefreshCw size={15} color="#ccc" className={loading?"spin":""}/></button>
              <button onClick={playBrief} className="abtn" style={{ padding:"10px 18px",border:"1px solid #555",borderRadius:8,background:briefing?"#fff":"transparent",color:briefing?"#111":"#ccc",fontSize:13,fontWeight:700,display:"flex",alignItems:"center",gap:6 }}>{briefing?<VolumeX size={14}/>:<Volume2 size={14}/>} {briefing?"Stop":"Briefing"}</button>
            </div>
            {searchFocused&&!q&&(
              <div style={{ position:"absolute",top:"100%",left:0,right:80,marginTop:6,background:"#1a1a1a",border:"1px solid #333",borderRadius:10,padding:"12px 16px",zIndex:50,animation:"fadeUp 0.15s ease" }}>
                <div style={{ fontSize:10,color:"#888",fontWeight:700,textTransform:"uppercase",letterSpacing:1,marginBottom:8 }}><TrendingUp size={10} style={{marginRight:4}}/> Trending</div>
                <div style={{ display:"flex",gap:6,flexWrap:"wrap" }}>{QUICK.map(s=><button key={s} onMouseDown={()=>doSearch(null,s)} className="abtn" style={{ padding:"5px 12px",borderRadius:6,fontSize:12,background:"rgba(255,255,255,0.06)",border:"1px solid #333",color:"#ddd" }}>{s}</button>)}</div>
              </div>
            )}
            {activeSearch&&!loading&&(
              <div style={{ marginTop:8,display:"flex",alignItems:"center",gap:8,justifyContent:"center" }}>
                <span style={{ fontSize:12,color:"#888" }}>Showing {filtered.length} result{filtered.length!==1?"s":""} for "<strong style={{color:"#fff"}}>{activeSearch}</strong>"{searching&&" — searching web..."}</span>
                <button onClick={clearSearch} style={{ fontSize:11,color:"#aaa",background:"rgba(255,255,255,0.1)",border:"none",padding:"2px 10px",borderRadius:4,cursor:"pointer" }}>Clear</button>
              </div>
            )}
          </div>
          <div style={{ maxWidth:760,margin:"12px auto 0",display:"flex",gap:5,flexWrap:"wrap",justifyContent:"center" }}>
            {TAGS.map(tag=>{
              const isA=(tag.isAdverse&&advOnly)||(tag.isPol&&polOnly);
              return <button key={tag.label} onClick={()=>handleTag(tag)} className="abtn" style={{ padding:"4px 12px",borderRadius:20,fontSize:11,fontWeight:600,background:isA?"#fff":"rgba(255,255,255,0.08)",color:isA?"#111":"#bbb",border:isA?"none":"1px solid #444" }}>{tag.label}</button>;
            })}
          </div>
        </header>

        <div style={{ display: "flex", maxWidth: 1280, margin: "0 auto" }}>
          <div style={{ flex: 2, padding: "24px 28px", borderRight: "1px solid #e5e5e5", minWidth: 0 }}>
            {/* 🔥 Most Polarized Banner */}
            {!loading && mostPol && !activeSearch && cat === "All" && (
              <MostPolarized story={mostPol} onClick={() => mostPolStory && setSelected(mostPolStory)} />
            )}

            {!loading && filtered.length > 0 && (
              <div style={{ display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:16 }}>
                <span style={{ fontSize:13,color:"#555" }}>Showing {(page-1)*PER_PAGE+1}–{Math.min(page*PER_PAGE,filtered.length)} of <strong>{filtered.length}</strong> stories</span>
                {totalPages>1&&<Pagination page={page} total={totalPages} onPage={p=>{setPage(p);window.scrollTo(0,0)}}/>}
              </div>
            )}
            {loading&&<div style={{textAlign:"center",padding:80}}><div className="loader"/><p className="serif" style={{color:"#555",marginTop:20,fontSize:18,fontStyle:"italic"}}>Analyzing 30+ articles from {COUNTRIES.find(c=>c.code===country)?.flag} {country}...</p><p style={{color:"#aaa",marginTop:6,fontSize:12}}>60–120 seconds</p></div>}
            {error&&<div style={{background:"#fef2f2",border:"1px solid #fca5a5",borderRadius:4,padding:14,color:"#b91c1c",fontSize:14,marginBottom:16}}>{error}</div>}
            {!loading&&pageStories.length>0&&(
              <>
                {page===1&&<NewsCard story={pageStories[0]} onOpen={()=>setSelected(pageStories[0])} apiBase={API} isHero/>}
                {page===1&&pageStories.length>1&&<hr className="nyt-rule-thick"/>}
                {(page===1?pageStories.slice(1):pageStories).map((s,i,arr)=>(
                  <div key={s.id}><NewsCard story={s} onOpen={()=>setSelected(s)} apiBase={API}/>{i<arr.length-1&&<hr className="nyt-rule"/>}</div>
                ))}
              </>
            )}
            {!loading&&filtered.length===0&&allStories.length>0&&(
              <div style={{textAlign:"center",padding:50}}>
                <p className="serif" style={{color:"#555",fontSize:18,fontStyle:"italic",marginBottom:12}}>No articles match "{activeSearch||cat}"</p>
                {activeSearch&&<button onClick={()=>doSearch(null,activeSearch)} className="abtn" style={{background:"#111",color:"#fff",border:"none",padding:"10px 24px",borderRadius:8,fontSize:13,fontWeight:700}}>Search web for "{activeSearch}"</button>}
              </div>
            )}
            {!loading&&totalPages>1&&(
              <div style={{display:"flex",justifyContent:"center",marginTop:24,paddingTop:20,borderTop:"2px solid #111"}}><Pagination page={page} total={totalPages} onPage={p=>{setPage(p);window.scrollTo(0,0)}}/></div>
            )}
          </div>
          <div style={{ width:380,padding:"24px 22px",flexShrink:0,overflowY:"auto" }}>
            <ArticleAnalyzer apiBase={API}/>
            <hr className="nyt-rule-thick" style={{marginTop:24}}/>
            <OpinionColumn stories={filtered}/>
          </div>
        </div>
      </main>
      {selected&&<PerspectiveModal story={selected} onClose={()=>setSelected(null)} apiBase={API}/>}
      <AiChat/>
    </div>
  );
}

function Pagination({page,total,onPage}){
  return <div style={{display:"flex",gap:3,alignItems:"center"}}>
    <PB disabled={page<=1} onClick={()=>onPage(page-1)}><ChevronLeft size={13}/></PB>
    {Array.from({length:total},(_,i)=>i+1).map(p=><button key={p} onClick={()=>onPage(p)} style={{width:30,height:30,borderRadius:4,border:"1px solid #ddd",background:page===p?"#111":"#fff",color:page===p?"#fff":"#555",fontSize:12,fontWeight:700,cursor:"pointer"}}>{p}</button>)}
    <PB disabled={page>=total} onClick={()=>onPage(page+1)}><ChevronRight size={13}/></PB>
  </div>;
}
function PB({children,disabled,onClick}){
  return <button onClick={onClick} disabled={disabled} className="abtn" style={{padding:"6px 10px",borderRadius:4,border:"1px solid #ddd",background:"#fff",color:disabled?"#ccc":"#333",fontSize:12,display:"flex",alignItems:"center",cursor:disabled?"default":"pointer",opacity:disabled?0.4:1}}>{children}</button>;
}
