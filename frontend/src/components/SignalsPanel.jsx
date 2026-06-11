const signalColors = { buy: "#2ecc71", sell: "#e74c3c", neutral: "#f39c12" };

export default function SignalsPanel({ signals }) {
  if (!signals?.length) return null;
  return (
    <div style={{ background: "#1a1d27", borderRadius: 12, padding: 24, border: "1px solid #2a2d3a" }}>
      <h3 style={{ margin: "0 0 16px", color: "#e0e0e0" }}>Technical Signals</h3>
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {signals.map(s => (
          <div key={s.id}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <span style={{ fontSize: 14, color: "#ccc" }}>{s.indicator}</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: signalColors[s.signal] }}>
                {s.signal?.toUpperCase()}
              </span>
            </div>
            {/* Strength bar */}
            <div style={{ background: "#2a2d3a", borderRadius: 4, height: 6 }}>
              <div style={{
                width: `${s.strength}%`, height: "100%", borderRadius: 4,
                background: signalColors[s.signal],
                transition: "width 0.5s ease",
              }} />
            </div>
            <div style={{ fontSize: 11, color: "#666", marginTop: 3 }}>{s.interpretation}</div>
          </div>
        ))}
      </div>
    </div>
  );
}