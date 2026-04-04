/**
 * ArticleAnalyzer.jsx — Paste URL or text → get credibility, bias, category scores.
 * Uses POST /api/analyze endpoint (fixed from GET which had URL length issues).
 */
import { useState } from "react";
import { Link2, FileText, Loader2, AlertTriangle } from "lucide-react";
import axios from "axios";

const API = "http://localhost:8000";

export default function ArticleAnalyzer() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [mode, setMode] = useState("url");

  const analyze = async () => {
    if (!input.trim() || loading) return;
    setLoading(true); setResult(null);
    try {
      const { data } = await axios.post(`${API}/api/analyze`, {
        content: input.trim(),
        mode: mode,
      }, { timeout: 25000 });

      if (data.error && !data.credibility_score) {
        setResult({ verdict: data.error || "Analysis failed.", credibility_score: null });
      } else {
        setResult(data);
      }
    } catch (err) {
      setResult({ verdict: "Connection failed. Is the backend running?", credibility_score: null });
    } finally { setLoading(false); }
  };

  return (
    <div>
      <h3 className="serif" style={{ fontSize: 20, fontWeight: 700, color: "#111", marginBottom: 4 }}>
        Article Analyzer
      </h3>
      <p style={{ fontSize: 12, color: "#888", marginBottom: 14, lineHeight: 1.5 }}>
        Check any article for credibility, bias, fake news risk & adverse classification
      </p>

      {/* Mode toggle */}
      <div style={{ display: "flex", gap: 4, marginBottom: 10 }}>
        <ModeBtn active={mode === "url"} onClick={() => setMode("url")} icon={<Link2 size={11} />} label="Paste URL" />
        <ModeBtn active={mode === "text"} onClick={() => setMode("text")} icon={<FileText size={11} />} label="Paste Text" />
      </div>

      {/* Input */}
      {mode === "url" ? (
        <input value={input} onChange={e => setInput(e.target.value)}
          placeholder="https://www.example.com/article..."
          onKeyDown={e => e.key === "Enter" && analyze()}
          style={{
            width: "100%", padding: "10px 12px", border: "1px solid #ddd", borderRadius: 6,
            fontSize: 13, outline: "none", marginBottom: 10, background: "#fafafa",
            transition: "border-color 0.2s",
          }}
          onFocus={e => e.target.style.borderColor = "#111"}
          onBlur={e => e.target.style.borderColor = "#ddd"}
        />
      ) : (
        <textarea value={input} onChange={e => setInput(e.target.value)}
          placeholder="Paste article text here..."
          rows={5}
          style={{
            width: "100%", padding: "10px 12px", border: "1px solid #ddd", borderRadius: 6,
            fontSize: 13, outline: "none", marginBottom: 10, resize: "vertical", background: "#fafafa",
            fontFamily: "inherit", lineHeight: 1.6, transition: "border-color 0.2s",
          }}
          onFocus={e => e.target.style.borderColor = "#111"}
          onBlur={e => e.target.style.borderColor = "#ddd"}
        />
      )}

      <button onClick={analyze} disabled={loading || !input.trim()} className="abtn" style={{
        width: "100%", padding: "10px", borderRadius: 6, background: "#111", color: "#fff",
        border: "none", fontSize: 12, fontWeight: 700, display: "flex", alignItems: "center",
        justifyContent: "center", gap: 6, opacity: loading || !input.trim() ? 0.4 : 1,
        letterSpacing: 0.3,
      }}>
        {loading ? <><Loader2 size={13} className="spin" /> Analyzing...</> : "Analyze Article"}
      </button>

      {/* Results */}
      {result && (
        <div style={{ marginTop: 14, animation: "fadeUp 0.3s ease" }}>
          {result.credibility_score != null ? (
            <>
              {/* Score cards */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 12 }}>
                <ScoreCard label="Credibility" value={result.credibility_score}
                  color={result.credibility_score > 70 ? "#15803d" : result.credibility_score > 40 ? "#a16207" : "#b91c1c"} />
                <ScoreCard label="Bias Level" value={result.bias_score || 0}
                  color={(result.bias_score || 0) > 50 ? "#b91c1c" : (result.bias_score || 0) > 25 ? "#a16207" : "#15803d"} />
              </div>

              {/* Tags */}
              <div style={{ display: "flex", gap: 5, flexWrap: "wrap", marginBottom: 12 }}>
                <Tag c={result.is_adverse ? "#b91c1c" : "#15803d"} bg={result.is_adverse ? "#fef2f2" : "#f0fdf4"}>
                  {result.is_adverse ? "⚠ ADVERSE" : "✓ NON-ADVERSE"}
                </Tag>
                <Tag c="#111" bg="#f5f5f5">{result.category || "General"}</Tag>
                <Tag
                  c={result.fake_news_risk === "High" ? "#b91c1c" : result.fake_news_risk === "Medium" ? "#a16207" : "#15803d"}
                  bg={result.fake_news_risk === "High" ? "#fef2f2" : result.fake_news_risk === "Medium" ? "#fffbeb" : "#f0fdf4"}
                >
                  Fake News: {result.fake_news_risk || "Low"}
                </Tag>
                {result.bias_direction && (
                  <Tag c="#555" bg="#f5f5f5">{result.bias_direction}</Tag>
                )}
              </div>

              {/* Summary */}
              {result.summary && (
                <p style={{ fontSize: 12, color: "#444", lineHeight: 1.6, marginBottom: 10 }}>{result.summary}</p>
              )}

              {/* Red flags */}
              {result.red_flags?.length > 0 && (
                <div style={{ background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 6, padding: "8px 12px", marginBottom: 10 }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: "#92400e", marginBottom: 4 }}>Red Flags</div>
                  {result.red_flags.map((f, i) => (
                    <div key={i} style={{ fontSize: 11, color: "#a16207", display: "flex", alignItems: "flex-start", gap: 5, marginBottom: 2 }}>
                      <AlertTriangle size={10} style={{ marginTop: 2, flexShrink: 0 }} /> {f}
                    </div>
                  ))}
                </div>
              )}

              {/* Adverse reason */}
              {result.is_adverse && result.adverse_reason && (
                <div style={{ background: "#fef2f2", borderLeft: "3px solid #b91c1c", padding: "6px 10px", borderRadius: "0 6px 6px 0", marginBottom: 10, fontSize: 11, color: "#991b1b" }}>
                  <strong>Adverse:</strong> {result.adverse_reason}
                </div>
              )}

              {/* Verdict */}
              {result.verdict && (
                <p className="serif" style={{
                  fontSize: 13, color: "#333", fontStyle: "italic", lineHeight: 1.5,
                  borderTop: "1px solid #eee", paddingTop: 10, marginTop: 4,
                }}>{result.verdict}</p>
              )}
            </>
          ) : (
            <p style={{ fontSize: 12, color: "#b91c1c", lineHeight: 1.5 }}>{result.verdict}</p>
          )}
        </div>
      )}
    </div>
  );
}

function ModeBtn({ active, onClick, icon, label }) {
  return (
    <button onClick={onClick} className="abtn" style={{
      padding: "5px 12px", borderRadius: 5, fontSize: 11, fontWeight: 600,
      background: active ? "#111" : "#fff", color: active ? "#fff" : "#888",
      border: "1px solid #ddd", display: "flex", alignItems: "center", gap: 5,
    }}>{icon} {label}</button>
  );
}

function ScoreCard({ label, value, color }) {
  return (
    <div style={{ background: "#fafafa", border: "1px solid #eee", borderRadius: 8, padding: "10px 12px", textAlign: "center" }}>
      <div style={{ fontSize: 9, color: "#bbb", textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 3 }}>{label}</div>
      <div className="serif" style={{ fontSize: 26, fontWeight: 700, color }}>{value}<span style={{ fontSize: 12, fontWeight: 400, color: "#bbb" }}>/100</span></div>
    </div>
  );
}

function Tag({ children, c, bg }) {
  return <span style={{ fontSize: 10, padding: "3px 9px", borderRadius: 5, background: bg, color: c, fontWeight: 700 }}>{children}</span>;
}
