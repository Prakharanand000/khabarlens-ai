/**
 * NarrativeTimeline.jsx — "How this story evolved" section.
 * Shows phases of news cycle with sentiment/polarization indicators.
 */
import { useState } from "react";
import { Loader2, Clock, TrendingUp } from "lucide-react";
import axios from "axios";

const API = "http://localhost:8000";

const PHASE_COLORS = {
  "low": "#15803d", "rising": "#a16207", "high": "#b91c1c",
  "neutral": "#888", "mixed": "#a16207", "diverging": "#b91c1c",
};

export default function NarrativeTimeline({ story }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (loading) return; setLoading(true);
    try {
      const r = await axios.post(`${API}/api/narrative-timeline`, {
        headline: story.headline, summary: story.neutral_summary, category: story.category,
      }, { timeout: 20000 });
      if (!r.data.error) setData(r.data);
    } catch {} finally { setLoading(false); }
  };

  if (!data && !loading) {
    return (
      <div style={{ textAlign: "center", padding: "12px 0" }}>
        <button onClick={run} className="abtn" style={{
          background: "#fff", color: "#111", border: "1px solid #ddd", padding: "8px 20px",
          borderRadius: 6, fontSize: 12, fontWeight: 600, display: "inline-flex", alignItems: "center", gap: 6,
        }}><Clock size={13} /> Show Narrative Timeline</button>
      </div>
    );
  }
  if (loading) return <div style={{ textAlign: "center", padding: 16 }}><Loader2 size={18} className="spin" color="#111" /></div>;

  return (
    <div style={{ animation: "fadeUp 0.3s ease" }}>
      <h4 style={{ fontSize: 11, fontWeight: 800, color: "#111", textTransform: "uppercase", letterSpacing: 1, marginBottom: 14 }}>
        How This Story Evolved
      </h4>

      {/* Timeline */}
      <div style={{ position: "relative", paddingLeft: 24 }}>
        {/* Vertical line */}
        <div style={{ position: "absolute", left: 7, top: 4, bottom: 4, width: 2, background: "#e5e5e5" }} />

        {(data.timeline || []).map((phase, i) => {
          const polColor = PHASE_COLORS[phase.polarization] || "#888";
          const isLast = i === (data.timeline?.length || 0) - 1;
          return (
            <div key={i} style={{ position: "relative", marginBottom: 16, paddingLeft: 20 }}>
              {/* Dot */}
              <div style={{
                position: "absolute", left: -20, top: 4,
                width: 14, height: 14, borderRadius: "50%",
                background: isLast ? "#111" : "#fff",
                border: `2px solid ${isLast ? "#111" : polColor}`,
              }} />
              <div style={{
                background: isLast ? "#f5f5f5" : "#fafafa",
                borderRadius: 8, padding: "12px 16px",
                border: isLast ? "1px solid #ddd" : "1px solid #eee",
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: "#111" }}>{phase.phase}</span>
                  <div style={{ display: "flex", gap: 6 }}>
                    <span style={{ fontSize: 9, padding: "2px 8px", borderRadius: 4, background: "#f5f5f5", color: "#888", border: "1px solid #eee" }}>
                      Sentiment: {phase.sentiment}
                    </span>
                    <span style={{ fontSize: 9, padding: "2px 8px", borderRadius: 4, background: polColor + "15", color: polColor, border: `1px solid ${polColor}33`, fontWeight: 600 }}>
                      Pol: {phase.polarization}
                    </span>
                  </div>
                </div>
                <p style={{ fontSize: 13, color: "#444", lineHeight: 1.6 }}>{phase.description}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Prediction */}
      {data.prediction && (
        <div style={{ background: "#f0f9ff", border: "1px solid #bae6fd", borderRadius: 8, padding: "10px 14px", marginTop: 8 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
            <TrendingUp size={12} color="#0369a1" />
            <span style={{ fontSize: 10, fontWeight: 700, color: "#0369a1", textTransform: "uppercase", letterSpacing: 0.5 }}>Prediction</span>
          </div>
          <p style={{ fontSize: 12, color: "#0c4a6e", lineHeight: 1.5 }}>{data.prediction}</p>
        </div>
      )}

      {data.narrative_shift && (
        <p style={{ fontSize: 12, color: "#888", fontStyle: "italic", marginTop: 8 }}>
          Narrative shift: {data.narrative_shift}
        </p>
      )}
    </div>
  );
}
