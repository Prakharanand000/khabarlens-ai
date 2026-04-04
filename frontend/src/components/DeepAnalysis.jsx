/**
 * DeepAnalysis.jsx — The Perspective Slider + Omission Radar + Gen-Z Mode.
 * Shown inside PerspectiveModal when user clicks "Deep Analysis".
 */
import { useState } from "react";
import { Loader2, AlertTriangle, Zap, Eye, Radio, Target, MessageCircle } from "lucide-react";
import axios from "axios";

const API = "http://localhost:8000";

export default function DeepAnalysis({ story }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const run = async () => {
    if (loading) return;
    setLoading(true); setError(null);
    try {
      const resp = await axios.post(`${API}/api/deep-analysis`, {
        headline: story.headline,
        summary: story.neutral_summary,
        sources: story.sources || [],
        category: story.category || "",
      }, { timeout: 30000 });
      if (resp.data.error) { setError(resp.data.error); }
      else { setData(resp.data); }
    } catch (e) {
      setError("Failed to generate deep analysis. Check backend.");
    } finally { setLoading(false); }
  };

  if (!data && !loading && !error) {
    return (
      <div style={{ textAlign: "center", padding: "20px 0" }}>
        <button onClick={run} className="abtn" style={{
          background: "#111", color: "#fff", border: "none", padding: "12px 28px",
          borderRadius: 8, fontSize: 14, fontWeight: 700, display: "inline-flex",
          alignItems: "center", gap: 8, letterSpacing: 0.3,
        }}>
          <Zap size={16} /> Run Deep Analysis
        </button>
        <p style={{ fontSize: 12, color: "#888", marginTop: 8 }}>
          Perspective Slider · Omission Radar · Gen-Z Mode
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "30px 0" }}>
        <Loader2 size={24} className="spin" color="#111" />
        <p className="serif" style={{ color: "#666", marginTop: 12, fontSize: 14, fontStyle: "italic" }}>
          Generating deep analysis...
        </p>
      </div>
    );
  }

  if (error) {
    return <div style={{ background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 8, padding: 14, color: "#b91c1c", fontSize: 13 }}>{error}</div>;
  }

  const ps = data.perspective_slider;
  const or_ = data.omission_radar || [];
  const gz = data.gen_z_mode;
  const bm = data.bias_meter;

  return (
    <div style={{ animation: "fadeUp 0.3s ease" }}>
      {/* ═══ PERSPECTIVE SLIDER ═══ */}
      <div style={{ marginBottom: 28 }}>
        <SectionHead icon={<Eye size={14} />} title="The Perspective Slider" subtitle="Same story, three political lenses" />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
          {ps && ["left", "center", "right"].map((key) => {
            const p = ps[key];
            if (!p) return null;
            const colors = { left: "#15803d", center: "#444", right: "#b91c1c" };
            const labels = { left: "← LEFT", center: "CENTER", right: "RIGHT →" };
            return (
              <div key={key} style={{
                background: "#fafafa", borderRadius: 10, padding: "16px 14px",
                borderTop: `3px solid ${colors[key]}`,
              }}>
                <div style={{
                  fontSize: 10, fontWeight: 800, color: colors[key],
                  textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 6,
                }}>{labels[key]}</div>
                <div className="serif" style={{ fontSize: 14, fontWeight: 700, color: "#111", marginBottom: 8 }}>
                  {p.title}
                </div>
                <p style={{ fontSize: 13, lineHeight: 1.7, color: "#444", marginBottom: 8 }}>
                  {p.summary}
                </p>
                <p style={{ fontSize: 11, color: "#888", fontStyle: "italic", borderTop: "1px solid #eee", paddingTop: 8 }}>
                  Key angle: {p.key_angle}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* ═══ OMISSION RADAR ═══ */}
      {or_.length > 0 && (
        <div style={{ marginBottom: 28 }}>
          <SectionHead icon={<Radio size={14} />} title="The Omission Radar" subtitle="What this coverage might be missing" />
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {or_.map((item, i) => (
              <div key={i} style={{
                background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 10,
                padding: "14px 16px", display: "flex", gap: 12,
              }}>
                <div style={{
                  width: 28, height: 28, borderRadius: "50%", background: "#fef3c7",
                  display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
                }}>
                  <AlertTriangle size={14} color="#92400e" />
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: "#92400e", marginBottom: 3 }}>
                    Context Missing
                  </div>
                  <p style={{ fontSize: 13, color: "#78350f", lineHeight: 1.6, marginBottom: 4 }}>
                    {item.missing_context}
                  </p>
                  <p style={{ fontSize: 12, color: "#a16207", fontStyle: "italic" }}>
                    Why it matters: {item.why_it_matters}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ═══ GEN-Z MODE ═══ */}
      {gz && (
        <div style={{ marginBottom: 28 }}>
          <SectionHead icon={<MessageCircle size={14} />} title="Gen-Z Mode" subtitle="The social card version" />
          <div style={{ background: "#111", borderRadius: 14, padding: "20px 22px", color: "#fff" }}>
            {/* The Tea */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 10, fontWeight: 800, color: "#a78bfa", textTransform: "uppercase", letterSpacing: 2, marginBottom: 6 }}>
                ☕ THE TEA
              </div>
              <p style={{ fontSize: 16, fontWeight: 600, lineHeight: 1.5 }}>
                {gz.the_tea}
              </p>
            </div>

            {/* The Receipts */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 10, fontWeight: 800, color: "#60a5fa", textTransform: "uppercase", letterSpacing: 2, marginBottom: 6 }}>
                🧾 THE RECEIPTS
              </div>
              {(gz.the_receipts || []).map((r, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "flex-start", gap: 8, marginBottom: 6,
                  padding: "8px 12px", background: "rgba(255,255,255,0.06)", borderRadius: 8,
                }}>
                  <span style={{ color: "#60a5fa", fontWeight: 800, fontSize: 14 }}>{i + 1}</span>
                  <span style={{ fontSize: 13, lineHeight: 1.5, color: "#ddd" }}>{r}</span>
                </div>
              ))}
            </div>

            {/* Vibe Check */}
            <div style={{ display: "flex", gap: 16, marginBottom: 16 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 10, fontWeight: 800, color: "#f472b6", textTransform: "uppercase", letterSpacing: 2, marginBottom: 6 }}>
                  ✨ VIBE CHECK
                </div>
                <div style={{
                  display: "inline-block", padding: "6px 16px", borderRadius: 20,
                  background: gz.vibe_check === "big deal" ? "rgba(239,68,68,0.2)" :
                    gz.vibe_check === "overhyped" ? "rgba(234,179,8,0.2)" : "rgba(96,165,250,0.2)",
                  color: gz.vibe_check === "big deal" ? "#fca5a5" :
                    gz.vibe_check === "overhyped" ? "#fde68a" : "#93c5fd",
                  fontSize: 14, fontWeight: 800, textTransform: "uppercase",
                }}>
                  {gz.vibe_check}
                </div>
                <p style={{ fontSize: 11, color: "#999", marginTop: 6 }}>{gz.vibe_explanation}</p>
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 10, fontWeight: 800, color: "#34d399", textTransform: "uppercase", letterSpacing: 2, marginBottom: 6 }}>
                  🎯 MAIN CHARACTER
                </div>
                <div style={{ fontSize: 15, fontWeight: 700, color: "#fff" }}>{gz.main_character}</div>
                <p style={{ fontSize: 11, color: "#999", marginTop: 4 }}>{gz.main_character_role}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═══ BIAS METER ═══ */}
      {bm && (
        <div style={{ marginBottom: 16 }}>
          <SectionHead icon={<Target size={14} />} title="Bias Meter" subtitle="Overall coverage lean assessment" />
          <div style={{ background: "#fafafa", borderRadius: 10, padding: "14px 18px", border: "1px solid #eee" }}>
            {/* Visual meter */}
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: "#15803d" }}>LEFT</span>
              <div style={{ flex: 1, height: 8, background: "#eee", borderRadius: 4, position: "relative" }}>
                <div style={{
                  position: "absolute", top: -2, width: 12, height: 12, borderRadius: "50%",
                  background: "#111", border: "2px solid #fff", boxShadow: "0 1px 4px rgba(0,0,0,0.2)",
                  left: bm.overall_lean === "Left" ? "10%" :
                        bm.overall_lean === "Center-Left" ? "30%" :
                        bm.overall_lean === "Center" ? "50%" :
                        bm.overall_lean === "Center-Right" ? "70%" : "90%",
                  transform: "translateX(-50%)",
                  transition: "left 0.5s ease",
                }} />
                {/* Scale markers */}
                {[10, 30, 50, 70, 90].map(pos => (
                  <div key={pos} style={{
                    position: "absolute", top: 0, left: `${pos}%`, width: 1, height: 8,
                    background: "#ccc", transform: "translateX(-50%)",
                  }} />
                ))}
              </div>
              <span style={{ fontSize: 10, fontWeight: 700, color: "#b91c1c" }}>RIGHT</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: "#111" }}>{bm.overall_lean}</span>
              <span style={{ fontSize: 11, color: "#888" }}>Confidence: {bm.confidence}</span>
            </div>
            <p style={{ fontSize: 12, color: "#555", marginTop: 6, lineHeight: 1.5 }}>{bm.reasoning}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function SectionHead({ icon, title, subtitle }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 2 }}>
        {icon}
        <h3 style={{ fontSize: 14, fontWeight: 800, color: "#111", textTransform: "uppercase", letterSpacing: 0.8 }}>{title}</h3>
      </div>
      <p style={{ fontSize: 11, color: "#888", marginLeft: 22 }}>{subtitle}</p>
    </div>
  );
}
