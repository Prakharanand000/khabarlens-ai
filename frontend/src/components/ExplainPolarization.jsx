/**
 * ExplainPolarization.jsx — "Why is this story polarized?" section.
 * Shows human-readable reasons, headline comparison, key differences.
 */
import { useState } from "react";
import { Loader2, Zap, AlertTriangle, ArrowUpRight } from "lucide-react";
import axios from "axios";

const API = "http://localhost:8000";

export default function ExplainPolarization({ story }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (loading) return; setLoading(true);
    try {
      const r = await axios.post(`${API}/api/explain-polarization`, {
        headline: story.headline,
        summary: story.neutral_summary,
        sources: story.sources || [],
        perspectives: story.perspectives || [],
        source_analysis: story.source_analysis || [],
      }, { timeout: 20000 });
      if (!r.data.error) setData(r.data);
    } catch {} finally { setLoading(false); }
  };

  if (!data && !loading) {
    return (
      <div style={{ textAlign: "center", padding: "16px 0" }}>
        <button onClick={run} className="abtn" style={{
          background: "#111", color: "#fff", border: "none", padding: "10px 24px",
          borderRadius: 8, fontSize: 13, fontWeight: 700, display: "inline-flex", alignItems: "center", gap: 8,
        }}><Zap size={14} /> Why is this story polarized?</button>
      </div>
    );
  }
  if (loading) return <div style={{ textAlign: "center", padding: 20 }}><Loader2 size={20} className="spin" color="#111" /><p style={{ color: "#888", marginTop: 8, fontSize: 12 }}>Analyzing narrative differences...</p></div>;

  return (
    <div style={{ animation: "fadeUp 0.3s ease" }}>
      {/* One-line summary */}
      {data.one_line_summary && (
        <div style={{ background: "#fafafa", borderLeft: "3px solid #111", borderRadius: "0 8px 8px 0", padding: "12px 16px", marginBottom: 16 }}>
          <p className="serif" style={{ fontSize: 15, fontWeight: 700, color: "#111", lineHeight: 1.5 }}>
            {data.one_line_summary}
          </p>
        </div>
      )}

      {/* Reasons — bullet points */}
      {data.reasons?.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <h4 style={{ fontSize: 11, fontWeight: 800, color: "#111", textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>
            Why This Story Is Polarized
          </h4>
          {data.reasons.map((r, i) => (
            <div key={i} style={{ display: "flex", gap: 10, marginBottom: 8, padding: "8px 12px", background: "#fafafa", borderRadius: 8 }}>
              <AlertTriangle size={14} color="#a16207" style={{ marginTop: 2, flexShrink: 0 }} />
              <p style={{ fontSize: 13, color: "#333", lineHeight: 1.6 }}>{r}</p>
            </div>
          ))}
        </div>
      )}

      {/* Side-by-Side Headlines */}
      {data.headline_framing && (
        <div style={{ marginBottom: 20 }}>
          <h4 style={{ fontSize: 11, fontWeight: 800, color: "#111", textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>
            How Different Outlets Frame This Story
          </h4>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
            <FrameCol label="LEFT-LEANING" color="#15803d" items={data.headline_framing.left_leaning || []} />
            <FrameCol label="NEUTRAL" color="#555" items={data.headline_framing.neutral || []} />
            <FrameCol label="RIGHT-LEANING" color="#b91c1c" items={data.headline_framing.right_leaning || []} />
          </div>
        </div>
      )}

      {/* Actual source headlines from the article */}
      {story.headlines_by_source?.length > 1 && (
        <div style={{ marginBottom: 20 }}>
          <h4 style={{ fontSize: 11, fontWeight: 800, color: "#111", textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>
            Actual Headlines from Sources
          </h4>
          {story.headlines_by_source.map((h, i) => (
            <a key={i} href={h.url} target="_blank" rel="noopener noreferrer" className="slink" style={{
              display: "flex", justifyContent: "space-between", alignItems: "center",
              padding: "10px 14px", background: "#fafafa", borderRadius: 8, marginBottom: 4,
              textDecoration: "none", border: "1px solid #eee",
            }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 10, color: "#888", marginBottom: 2 }}>
                  {h.source} · Credibility: {Math.round(h.credibility * 100)}%
                </div>
                <div style={{ fontSize: 13, color: "#111", fontWeight: 500, lineHeight: 1.4 }}>
                  {h.headline}
                </div>
              </div>
              <ArrowUpRight size={14} color="#bbb" style={{ flexShrink: 0, marginLeft: 8 }} />
            </a>
          ))}
        </div>
      )}

      {/* Key Differences table */}
      {data.key_differences?.length > 0 && (
        <div>
          <h4 style={{ fontSize: 11, fontWeight: 800, color: "#111", textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>
            Key Narrative Differences
          </h4>
          {data.key_differences.map((d, i) => (
            <div key={i} style={{ display: "flex", gap: 12, marginBottom: 8, padding: "10px 14px", background: "#fafafa", borderRadius: 8, border: "1px solid #eee" }}>
              <div style={{ minWidth: 100 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: "#111" }}>{d.aspect}</span>
              </div>
              <p style={{ fontSize: 12, color: "#555", lineHeight: 1.5 }}>{d.description}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function FrameCol({ label, color, items }) {
  return (
    <div style={{ borderTop: `3px solid ${color}`, paddingTop: 10 }}>
      <div style={{ fontSize: 9, fontWeight: 800, color, letterSpacing: 1.5, marginBottom: 8 }}>{label}</div>
      {items.length > 0 ? items.map((h, i) => (
        <p key={i} style={{ fontSize: 12, color: "#333", lineHeight: 1.5, marginBottom: 6, padding: "6px 8px", background: "#f5f5f5", borderRadius: 4 }}>
          "{h}"
        </p>
      )) : (
        <p style={{ fontSize: 11, color: "#bbb", fontStyle: "italic" }}>No framing detected</p>
      )}
    </div>
  );
}
