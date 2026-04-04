/**
 * OpinionColumn.jsx — NYT-style perspectives column with clickable headlines.
 */

export default function OpinionColumn({ stories }) {
  if (!stories || stories.length === 0) return null;

  const items = stories.slice(0, 6).map(s => ({
    headline: s.headline,
    url: s.original_articles?.[0]?.url || "#",
    perspectives: s.perspectives || [],
    pol: s.polarization.score,
    category: s.category,
  }));

  const byType = (keyword) => items.flatMap(item =>
    item.perspectives
      .filter(p => p.label.toLowerCase().includes(keyword))
      .map(p => ({ ...p, headline: item.headline, url: item.url, pol: item.pol }))
  );

  return (
    <div>
      <h3 className="serif" style={{ fontSize: 22, fontWeight: 700, color: "#111", marginBottom: 4 }}>
        Opinion & Perspectives
      </h3>
      <p style={{ fontSize: 12, color: "#888", marginBottom: 18, lineHeight: 1.5 }}>
        How different framings cover the same stories
      </p>

      <PGroup label="Progressive Framing" color="#15803d" items={byType("progressive").concat(byType("left"))} />
      <PGroup label="Conservative Framing" color="#b91c1c" items={byType("conservative").concat(byType("right"))} />
      <PGroup label="Centrist View" color="#1d4ed8" items={byType("centrist").concat(byType("neutral"))} />
    </div>
  );
}

function PGroup({ label, color, items }) {
  if (!items.length) return null;
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{
        fontSize: 11, fontWeight: 700, color, textTransform: "uppercase",
        letterSpacing: 1.2, marginBottom: 10, paddingBottom: 5,
        borderBottom: `2px solid ${color}`,
      }}>{label}</div>
      {items.slice(0, 4).map((item, i) => (
        <div key={i} style={{
          marginBottom: 14, paddingBottom: 14,
          borderBottom: i < Math.min(items.length, 4) - 1 ? "1px solid #f0f0f0" : "none",
        }}>
          {/* Clickable headline */}
          <a href={item.url} target="_blank" rel="noopener noreferrer" className="serif" style={{
            fontSize: 15, fontWeight: 700, color: "#111", lineHeight: 1.3,
            display: "block", marginBottom: 5, textDecoration: "none",
            transition: "color 0.15s",
          }}
            onMouseEnter={e => e.target.style.color = color}
            onMouseLeave={e => e.target.style.color = "#111"}
          >
            {item.headline.length > 60 ? item.headline.slice(0, 58) + "..." : item.headline}
          </a>
          <p style={{ fontSize: 13, color: "#555", lineHeight: 1.6 }}>
            {item.summary}
          </p>
          {item.emphasis && (
            <p className="serif" style={{ fontSize: 11, color: "#bbb", fontStyle: "italic", marginTop: 4 }}>
              Focus: {item.emphasis.length > 80 ? item.emphasis.slice(0, 78) + "..." : item.emphasis}
            </p>
          )}
          <div style={{ fontSize: 10, color: "#ccc", marginTop: 3 }}>
            Polarization: {item.pol}/100
          </div>
        </div>
      ))}
    </div>
  );
}
