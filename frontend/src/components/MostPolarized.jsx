/**
 * MostPolarized.jsx — "🔥 Most Polarized Story Today" banner.
 */
import { Flame, AlertTriangle } from "lucide-react";

export default function MostPolarized({ story, onClick }) {
  if (!story || !story.headline) return null;
  const pc = story.score > 65 ? "#b91c1c" : story.score > 45 ? "#a16207" : "#15803d";

  return (
    <div onClick={onClick} style={{
      background: "#111", borderRadius: 10, padding: "14px 20px", marginBottom: 20,
      display: "flex", alignItems: "center", gap: 14, cursor: "pointer",
      transition: "transform 0.15s, box-shadow 0.15s",
    }}
      onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = "0 6px 20px rgba(0,0,0,0.15)"; }}
      onMouseLeave={e => { e.currentTarget.style.transform = ""; e.currentTarget.style.boxShadow = ""; }}
    >
      <div style={{
        width: 44, height: 44, borderRadius: 10, background: pc,
        display: "flex", alignItems: "center", justifyContent: "center",
        flexShrink: 0,
      }}>
        <Flame size={20} color="#fff" />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 9, fontWeight: 800, color: "#f87171", textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 3 }}>
          🔥 Most Polarized Story Today
        </div>
        <div className="serif" style={{ fontSize: 15, fontWeight: 700, color: "#fff", lineHeight: 1.3, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {story.headline}
        </div>
      </div>
      <div style={{ textAlign: "center", flexShrink: 0 }}>
        <div style={{ fontSize: 22, fontWeight: 900, color: pc, fontFamily: "Georgia" }}>{story.score}</div>
        <div style={{ fontSize: 9, color: "#888" }}>/ 100</div>
      </div>
    </div>
  );
}
