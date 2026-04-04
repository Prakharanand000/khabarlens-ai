import { ChevronRight, ShieldAlert, Shield } from "lucide-react";

const GROUPS = {
  "Financial Crime": [
    "Financial Crime", "Money Laundering", "Fraud & Scams", "Insider Trading",
  ],
  "Security & Terror": [
    "Terrorism", "Cybercrime", "Drug Trafficking",
  ],
  "Regulation & Law": [
    "Sanctions", "Regulatory & Compliance", "FINRA & SEC", "Corruption",
  ],
  "Human Rights & Justice": [
    "Human Rights", "War Crimes", "Crime, Law & Justice",
  ],
  "Economy & Business": [
    "Economy & Markets",
  ],
  "World & Politics": [
    "Geopolitics", "General News",
  ],
  "Science & Tech": [
    "AI & Tech Ethics", "Environment", "Health",
  ],
};

export default function Sidebar({ cats, cc, active, onPick, advOnly, toggleAdv, advCt }) {
  return (
    <aside style={{
      width: 220, background: "#fafafa", borderRight: "1px solid #e5e5e5",
      position: "sticky", top: 0, height: "100vh", overflowY: "auto",
      display: "flex", flexDirection: "column", flexShrink: 0,
    }}>
      {/* Brand */}
      <div style={{ padding: "14px 16px 10px", borderBottom: "2px solid #111", background: "#111" }}>
        <div className="serif" style={{ fontSize: 18, fontWeight: 900, color: "#fff", letterSpacing: -0.5 }}>KhabarLens</div>
        <div style={{ fontSize: 8, color: "#888", marginTop: 2, letterSpacing: 1.5, textTransform: "uppercase" }}>AI News Intelligence</div>
      </div>

      {/* All Stories */}
      <div style={{ padding: "6px 0 0" }}>
        <CatBtn label="All Stories" active={active === "All"} onClick={() => onPick("All")} hasCount={true} />
      </div>

      {/* Grouped categories */}
      <div style={{ flex: 1, overflowY: "auto", paddingBottom: 8 }}>
        {Object.entries(GROUPS).map(([group, items]) => (
          <div key={group} style={{ padding: "8px 0 2px" }}>
            <div style={{
              padding: "0 16px", fontSize: 8, fontWeight: 800, color: "#aaa",
              textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 4,
            }}>{group}</div>
            {items.map(c => {
              const n = cc[c] || 0;
              const isActive = active === c;
              return (
                <CatBtn
                  key={c}
                  label={c}
                  count={n}
                  active={isActive}
                  onClick={() => onPick(c)}
                  hasCount={n > 0}
                />
              );
            })}
          </div>
        ))}
      </div>

      {/* Adverse filter */}
      <div style={{ padding: "8px 12px", borderTop: "1px solid #e5e5e5" }}>
        <button onClick={toggleAdv} className="abtn" style={{
          width: "100%", padding: "9px 12px", borderRadius: 6,
          border: `1.5px solid ${advOnly ? "#b91c1c" : "#e5e5e5"}`,
          background: advOnly ? "#fef2f2" : "#fff",
          color: advOnly ? "#b91c1c" : "#555",
          fontSize: 11, fontWeight: 700, display: "flex", alignItems: "center", gap: 6,
        }}>
          {advOnly ? <ShieldAlert size={13} /> : <Shield size={13} />}
          {advOnly ? "Showing Adverse Only" : "Filter Adverse News"}
          <span style={{ marginLeft: "auto", fontWeight: 900, color: advCt > 0 ? "#b91c1c" : "#ccc" }}>{advCt}</span>
        </button>
      </div>
    </aside>
  );
}

function CatBtn({ label, count, active, onClick, hasCount }) {
  return (
    <button onClick={onClick} className="sitem" style={{
      display: "flex", justifyContent: "space-between", alignItems: "center",
      width: "100%", padding: "7px 16px", border: "none",
      background: active ? "#fff" : "transparent",
      color: active ? "#111" : hasCount ? "#444" : "#aaa",
      fontWeight: active ? 700 : hasCount ? 500 : 400,
      fontSize: 12, textAlign: "left", cursor: "pointer",
      borderLeft: active ? "3px solid #111" : "3px solid transparent",
      opacity: hasCount || label === "All Stories" ? 1 : 0.5,
    }}>
      <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
        {active && <ChevronRight size={9} />}
        {label}
      </span>
      {count > 0 && (
        <span style={{
          fontSize: 9, background: active ? "#111" : "#eee",
          color: active ? "#fff" : "#888",
          padding: "1px 7px", borderRadius: 6, fontWeight: 700,
          minWidth: 18, textAlign: "center",
        }}>{count}</span>
      )}
    </button>
  );
}
