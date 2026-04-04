export default function StatsBar({ stories, allStories, avgPol, adverseCount }) {
  const pb = { "0-30": 0, "31-60": 0, "61-100": 0 };
  stories.forEach(s => { const v = s.polarization.score; if (v <= 30) pb["0-30"]++; else if (v <= 60) pb["31-60"]++; else pb["61-100"]++; });
  const cats = {}; allStories.forEach(s => { cats[s.category] = (cats[s.category] || 0) + 1; });
  const tc = Object.entries(cats).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const mc = tc.length ? tc[0][1] : 1;
  const sv = { high: 0, medium: 0, low: 0 }; stories.forEach(s => { sv[s.severity || "low"]++; });
  const pc = avgPol > 60 ? "#b91c1c" : avgPol > 30 ? "#a16207" : "#15803d";

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginBottom: 24 }}>
      <C title="Polarization Distribution">
        <div style={{ display: "flex", gap: 10, alignItems: "flex-end", height: 50 }}>
          <Bar l="Low" v={pb["0-30"]} m={stories.length||1} c="#15803d" />
          <Bar l="Med" v={pb["31-60"]} m={stories.length||1} c="#a16207" />
          <Bar l="High" v={pb["61-100"]} m={stories.length||1} c="#b91c1c" />
        </div>
        <div style={{ fontSize: 11, color: "#999", marginTop: 8 }}>Avg: <span style={{ color: pc, fontWeight: 700 }}>{avgPol}/100</span></div>
      </C>
      <C title="Adverse Classification">
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <Pie sl={[{ v: adverseCount, c: "#b91c1c" }, { v: stories.length - adverseCount, c: "#15803d" }]} sz={48} />
          <div>
            <div style={{ fontSize: 12, color: "#b91c1c", fontWeight: 700 }}>{adverseCount} Adverse</div>
            <div style={{ fontSize: 12, color: "#15803d", fontWeight: 700 }}>{stories.length - adverseCount} Safe</div>
          </div>
        </div>
      </C>
      <C title="Severity Breakdown">
        <div style={{ display: "flex", gap: 10, alignItems: "flex-end", height: 50 }}>
          <Bar l="High" v={sv.high} m={stories.length||1} c="#b91c1c" />
          <Bar l="Med" v={sv.medium} m={stories.length||1} c="#a16207" />
          <Bar l="Low" v={sv.low} m={stories.length||1} c="#15803d" />
        </div>
      </C>
      <C title="Top Categories">
        <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
          {tc.map(([cat, n]) => (
            <div key={cat} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ height: 6, borderRadius: 3, background: "#111", width: `${(n / mc) * 100}%`, minWidth: 4 }} />
              <span style={{ fontSize: 9, color: "#999", whiteSpace: "nowrap" }}>{cat.length > 16 ? cat.slice(0, 14) + ".." : cat} ({n})</span>
            </div>
          ))}
        </div>
      </C>
    </div>
  );
}

function C({ title, children }) {
  return (
    <div style={{ background: "#fafafa", border: "1px solid #e5e5e5", borderRadius: 10, padding: 14 }}>
      <div style={{ fontSize: 9, fontWeight: 700, color: "#bbb", marginBottom: 10, textTransform: "uppercase", letterSpacing: 1 }}>{title}</div>
      {children}
    </div>
  );
}

function Bar({ l, v, m, c }) {
  const h = m > 0 ? Math.max((v / m) * 40, 3) : 3;
  return (
    <div style={{ flex: 1, textAlign: "center" }}>
      <div style={{ height: h, background: c, borderRadius: 3, marginBottom: 4 }} />
      <div style={{ fontSize: 13, fontWeight: 700, color: c }}>{v}</div>
      <div style={{ fontSize: 9, color: "#bbb" }}>{l}</div>
    </div>
  );
}

function Pie({ sl, sz }) {
  const t = sl.reduce((s, x) => s + x.v, 0) || 1;
  let cum = 0;
  const p = sl.map(x => { const s = (cum / t) * 360; cum += x.v; return `${x.c} ${s}deg ${(cum / t) * 360}deg`; });
  return <div style={{ width: sz, height: sz, borderRadius: "50%", background: `conic-gradient(${p.join(", ")})`, border: "2px solid #e5e5e5" }} />;
}
