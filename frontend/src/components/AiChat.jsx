import { useState, useRef, useEffect } from "react";
import { MessageCircle, X, Send, Newspaper } from "lucide-react";
import axios from "axios";

const API = "http://localhost:8000";
const SUGGESTIONS = ["Which story is most polarized?", "Any adverse news?", "Explain polarization index", "Compare sources", "What should I watch?"];

export default function AiChat() {
  const [open, setOpen] = useState(false);
  const [msgs, setMsgs] = useState([{ role: "ai", text: "Hello! I'm your KhabarLens AI analyst. Ask me about any story, bias patterns, or adverse classifications." }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  const send = async (text) => {
    const q = text || input.trim();
    if (!q || loading) return;
    setInput("");
    setMsgs(prev => [...prev, { role: "user", text: q }]);
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/api/chat?message=${encodeURIComponent(q)}`, { timeout: 15000 });
      setMsgs(prev => [...prev, { role: "ai", text: data.reply || "No response." }]);
    } catch { setMsgs(prev => [...prev, { role: "ai", text: "Connection issue." }]); }
    finally { setLoading(false); }
  };

  return (
    <>
      {!open && (
        <button onClick={() => setOpen(true)} className="abtn" style={{
          position: "fixed", bottom: 24, right: 24, zIndex: 999,
          width: 52, height: 52, borderRadius: "50%",
          background: "#111", border: "none", color: "#fff",
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: "0 4px 16px rgba(0,0,0,0.15)",
        }}><MessageCircle size={22} /></button>
      )}

      {open && (
        <div style={{
          position: "fixed", bottom: 24, right: 24, zIndex: 999,
          width: 380, height: 500, borderRadius: 14,
          background: "#fff", border: "1px solid #e5e5e5",
          display: "flex", flexDirection: "column",
          boxShadow: "0 12px 50px rgba(0,0,0,0.12)",
          animation: "fadeUp 0.2s ease", overflow: "hidden",
        }}>
          <div style={{ padding: "14px 18px", borderBottom: "2px solid #111", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ width: 28, height: 28, borderRadius: 7, background: "#111", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Newspaper size={14} color="#fff" />
              </div>
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#111" }}>KhabarLens AI</div>
                <div className="serif" style={{ fontSize: 10, color: "#888", fontStyle: "italic" }}>Ask about the news</div>
              </div>
            </div>
            <button onClick={() => setOpen(false)} style={{ background: "#f5f5f5", border: "1px solid #eee", borderRadius: 6, padding: 4 }}>
              <X size={14} color="#888" />
            </button>
          </div>

          <div style={{ flex: 1, overflowY: "auto", padding: "14px 16px", display: "flex", flexDirection: "column", gap: 10 }}>
            {msgs.map((m, i) => (
              <div key={i} style={{ alignSelf: m.role === "user" ? "flex-end" : "flex-start", maxWidth: "85%" }}>
                <div style={{
                  padding: "10px 14px", borderRadius: 10,
                  background: m.role === "user" ? "#111" : "#f5f5f5",
                  color: m.role === "user" ? "#fff" : "#222",
                  fontSize: 13, lineHeight: 1.6,
                  borderBottomRightRadius: m.role === "user" ? 3 : 10,
                  borderBottomLeftRadius: m.role === "ai" ? 3 : 10,
                }}>{m.text}</div>
              </div>
            ))}
            {loading && <div style={{ alignSelf: "flex-start" }}><div style={{ padding: "10px 14px", borderRadius: 10, background: "#f5f5f5", color: "#888", fontSize: 13 }}>Thinking...</div></div>}
            <div ref={endRef} />
          </div>

          {msgs.length <= 2 && (
            <div style={{ padding: "0 14px 8px", display: "flex", gap: 4, flexWrap: "wrap" }}>
              {SUGGESTIONS.slice(0, 3).map((s, i) => (
                <button key={i} onClick={() => send(s)} className="abtn" style={{
                  padding: "4px 10px", borderRadius: 5, fontSize: 10, background: "#fafafa", border: "1px solid #eee", color: "#555",
                }}>{s}</button>
              ))}
            </div>
          )}

          <div style={{ padding: "10px 14px", borderTop: "1px solid #e5e5e5", display: "flex", gap: 8 }}>
            <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send()}
              placeholder="Ask about the news..."
              style={{ flex: 1, background: "#fafafa", border: "1px solid #eee", borderRadius: 6, padding: "8px 12px", color: "#222", fontSize: 13, outline: "none" }}
              onFocus={e => e.target.style.borderColor = "#111"} onBlur={e => e.target.style.borderColor = "#eee"}
            />
            <button onClick={() => send()} disabled={loading || !input.trim()} style={{
              background: "#111", border: "none", borderRadius: 6, padding: "8px 14px", display: "flex", alignItems: "center",
              opacity: loading || !input.trim() ? 0.3 : 1,
            }}><Send size={14} color="#fff" /></button>
          </div>
        </div>
      )}
    </>
  );
}
