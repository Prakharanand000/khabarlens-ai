/**
 * NewsCard.jsx — NYT-style large article cards.
 * Hero card: full-width image on top, large serif headline.
 * Regular cards: image left, content right, generous spacing.
 */
import { useState } from "react";
import { AlertTriangle, Eye, Volume2, ShieldAlert, Shield, ExternalLink, ArrowUpRight } from "lucide-react";
import axios from "axios";

const CI = {
  "Financial Crime": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&h=500&fit=crop",
  "Terrorism": "https://images.unsplash.com/photo-1580493113011-ad79f792a7c2?w=800&h=500&fit=crop",
  "Regulatory & Compliance": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=800&h=500&fit=crop",
  "Sanctions": "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=800&h=500&fit=crop",
  "Human Rights": "https://images.unsplash.com/photo-1591901206069-ed60c4429a2e?w=800&h=500&fit=crop",
  "Crime, Law & Justice": "https://images.unsplash.com/photo-1589994965851-a8f479c573a9?w=800&h=500&fit=crop",
  "Economy & Markets": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&h=500&fit=crop",
  "Geopolitics": "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=800&h=500&fit=crop",
  "AI & Tech Ethics": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&h=500&fit=crop",
  "Environment": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&h=500&fit=crop",
  "Health": "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=800&h=500&fit=crop",
  "General News": "https://images.unsplash.com/photo-1504711434969-e33886168d9c?w=800&h=500&fit=crop",
};

export default function NewsCard({ story, onOpen, apiBase, isHero }) {
  const [ie, setIe] = useState(false);
  const [al, setAl] = useState(false);
  const [ap, setAp] = useState(false);

  const p = story.polarization;
  const pc = p.score > 65 ? "#b91c1c" : p.score > 45 ? "#a16207" : p.score > 25 ? "#666" : "#15803d";
  const img = (!ie && story.image_url) ? story.image_url : (CI[story.category] || CI["General News"]);
  const link = story.original_articles?.[0]?.url || "#";

  const speak = async (lang) => {
    if (ap || al) return; setAl(true);
    try {
      const t = `${story.headline}. ${story.neutral_summary}`.slice(0, 500);
      const r = await axios.get(`${apiBase}/api/tts?text=${encodeURIComponent(t)}&lang=${lang}`, { responseType: "blob", timeout: 25000 });
      const a = new Audio(URL.createObjectURL(r.data));
      setAp(true); setAl(false); a.play(); a.onended = () => setAp(false);
    } catch { setAl(false); }
  };

  // HERO CARD — full width, image on top
  if (isHero) {
    return (
      <div className="ncard" style={{ animation: "fadeUp 0.4s ease" }}>
        <a href={link} target="_blank" rel="noopener noreferrer" style={{ display: "block", position: "relative", overflow: "hidden", borderRadius: 4 }}>
          <img src={img} alt="" onError={() => setIe(true)}
            style={{ width: "100%", height: 360, objectFit: "cover", display: "block", transition: "transform 0.4s" }}
            onMouseEnter={e => e.target.style.transform = "scale(1.02)"}
            onMouseLeave={e => e.target.style.transform = "scale(1)"}
          />
          <div style={{ position: "absolute", top: 12, left: 12, display: "flex", gap: 6 }}>
            {story.is_adverse && <Badge bg="rgba(185,28,28,0.9)"><ShieldAlert size={9} /> ADVERSE</Badge>}
            <Badge bg="rgba(0,0,0,0.7)">{story.category}</Badge>
          </div>
        </a>

        <div style={{ padding: "16px 0" }}>
          <div style={{ fontSize: 11, color: "#999", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6, fontWeight: 600 }}>
            {story.sources?.[0]} · {story.source_count} sources
          </div>
          <a href={link} target="_blank" rel="noopener noreferrer" className="ncard-headline" style={{ textDecoration: "none" }}>
            <h2 className="serif" style={{ fontSize: 32, fontWeight: 700, lineHeight: 1.2, color: "#111", marginBottom: 12 }}>
              {story.headline}
            </h2>
          </a>
          <p style={{ fontSize: 15, lineHeight: 1.8, color: "#444", marginBottom: 14, maxWidth: 600 }}>
            {story.neutral_summary}
          </p>

          {story.is_adverse && story.adverse_reason && (
            <div style={{ background: "#fef2f2", borderLeft: "3px solid #b91c1c", padding: "8px 14px", marginBottom: 14, fontSize: 12, color: "#991b1b", borderRadius: "0 4px 4px 0" }}>
              <strong>Adverse:</strong> {story.adverse_reason}
            </div>
          )}

          <PolBar p={p} pc={pc} />
          <Actions story={story} speak={speak} al={al} ap={ap} onOpen={onOpen} />
        </div>
      </div>
    );
  }

  // REGULAR CARD — image left, content right, large
  return (
    <div className="ncard" style={{ display: "flex", gap: 20, padding: "20px 0", animation: "fadeUp 0.4s ease" }}>
      <a href={link} target="_blank" rel="noopener noreferrer" style={{
        width: 280, height: 200, flexShrink: 0, overflow: "hidden", borderRadius: 4, position: "relative", display: "block",
      }}>
        <img src={img} alt="" onError={() => setIe(true)}
          style={{ width: "100%", height: "100%", objectFit: "cover", transition: "transform 0.3s" }}
          onMouseEnter={e => e.target.style.transform = "scale(1.03)"}
          onMouseLeave={e => e.target.style.transform = "scale(1)"}
        />
        {story.is_adverse && (
          <div style={{ position: "absolute", top: 8, left: 8 }}>
            <Badge bg="rgba(185,28,28,0.9)"><ShieldAlert size={9} /> ADVERSE</Badge>
          </div>
        )}
      </a>

      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <div style={{ fontSize: 10, color: "#999", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4, fontWeight: 600 }}>
          {story.category} · {story.sources?.[0]} · {story.source_count} sources
        </div>
        <a href={link} target="_blank" rel="noopener noreferrer" className="ncard-headline" style={{ textDecoration: "none" }}>
          <h3 className="serif" style={{ fontSize: 22, fontWeight: 700, lineHeight: 1.25, color: "#111", marginBottom: 8 }}>
            {story.headline}
          </h3>
        </a>
        <p style={{ fontSize: 14, lineHeight: 1.75, color: "#555", marginBottom: 10, flex: 1 }}>
          {story.neutral_summary}
        </p>

        {story.is_adverse && story.adverse_reason && (
          <div style={{ background: "#fef2f2", borderLeft: "2px solid #b91c1c", padding: "5px 10px", marginBottom: 10, fontSize: 11, color: "#991b1b", borderRadius: "0 4px 4px 0" }}>
            <strong>Adverse:</strong> {story.adverse_reason}
          </div>
        )}

        <PolBar p={p} pc={pc} />
        <Actions story={story} speak={speak} al={al} ap={ap} onOpen={onOpen} />
      </div>
    </div>
  );
}

function PolBar({ p, pc }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
      <AlertTriangle size={11} color={pc} />
      <span style={{ fontSize: 11, fontWeight: 600, color: pc }}>Polarization {p.score}/100</span>
      <div style={{ flex: 1, maxWidth: 140, height: 3, background: "#eee", borderRadius: 2 }}>
        <div style={{ width: `${p.score}%`, height: "100%", background: pc, borderRadius: 2, transition: "width 0.5s" }} />
      </div>
      <span style={{ fontSize: 10, color: "#bbb", fontStyle: "italic", fontFamily: "Georgia,serif" }}>{p.level}</span>
    </div>
  );
}

function Actions({ story, speak, al, ap, onOpen }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
      <div style={{ display: "flex", gap: 6 }}>
        {(story.original_articles || []).slice(0, 2).map((a, i) => (
          <a key={i} href={a.url} target="_blank" rel="noopener noreferrer" className="slink" style={{
            fontSize: 10, color: "#666", padding: "3px 8px", borderRadius: 4, border: "1px solid #eee",
            display: "flex", alignItems: "center", gap: 3, textDecoration: "none",
          }}>{a.source} <ArrowUpRight size={8} /></a>
        ))}
      </div>
      <div style={{ display: "flex", gap: 3 }}>
        {[["en","EN"],["hi","HI"],["es","ES"],["fr","FR"]].map(([c, l]) => (
          <button key={c} onClick={() => speak(c)} disabled={al||ap} className="abtn" style={{
            background: "#fff", border: "1px solid #eee", color: "#999", padding: "3px 7px", borderRadius: 3,
            fontSize: 9, display: "flex", alignItems: "center", gap: 2, opacity: (al||ap) ? 0.3 : 1,
          }}><Volume2 size={8} /> {l}</button>
        ))}
        <button onClick={onOpen} className="abtn" style={{
          background: "#111", border: "none", color: "#fff", padding: "5px 12px", borderRadius: 4,
          fontSize: 10, fontWeight: 600, display: "flex", alignItems: "center", gap: 4,
        }}><Eye size={11} /> Perspectives</button>
      </div>
    </div>
  );
}

function Badge({ children, bg }) {
  return <span style={{ padding: "3px 8px", borderRadius: 4, fontSize: 10, fontWeight: 700, background: bg, color: "#fff", display: "flex", alignItems: "center", gap: 3 }}>{children}</span>;
}
