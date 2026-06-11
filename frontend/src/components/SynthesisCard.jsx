const biasColors = { buy: "#2ecc71", sell: "#e74c3c", neutral: "#f39c12" };

export default function SynthesisCard({ report, ticker }) {
  if (!report) return null;
  return (
    <div style={{ background: "#1a1d27", borderRadius: 12, padding: 24, border: "1px solid #2a2d3a" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 16 }}>
        <h2 style={{ margin: 0, fontSize: 18, color: "#e0e0e0" }}>{ticker} — Research Note</h2>
        <BiasBadge label="Technical"    bias={report.technical_bias} />
        <BiasBadge label="Fundamental"  bias={report.fundamental_bias} />
        <BiasBadge label="Overall"      bias={report.overall_bias} size="lg" />
      </div>
      <p style={{ lineHeight: 1.8, color: "#ccc", whiteSpace: "pre-line", margin: 0 }}>
        {report.narrative}
      </p>
    </div>
  );
}

function BiasBadge({ label, bias, size }) {
  const color = biasColors[bias] || "#888";
  return (
    <span style={{
      background: color + "22", color, border: `1px solid ${color}44`,
      borderRadius: 8, padding: size === "lg" ? "4px 14px" : "2px 10px",
      fontSize: size === "lg" ? 14 : 12, fontWeight: 600,
    }}>
      {label}: {bias?.toUpperCase()}
    </span>
  );
}