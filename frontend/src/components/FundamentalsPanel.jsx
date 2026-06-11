export default function FundamentalsPanel({ fundamental, macro, news }) {
  return (
    <div style={{ background: "#1a1d27", borderRadius: 12, padding: 24, border: "1px solid #2a2d3a" }}>
      <h3 style={{ margin: "0 0 16px", color: "#e0e0e0" }}>Fundamentals & Macro</h3>

      {fundamental && (
        <Section title="Earnings">
          <Row label="P/E Ratio"         value={fundamental.pe_ratio?.toFixed(2)} />
          <Row label="EPS"               value={fundamental.eps?.toFixed(2)} />
          <Row label="Revenue Growth"    value={fundamental.revenue_growth ? `${fundamental.revenue_growth.toFixed(1)}%` : null} />
          <Row label="Earnings Surprise" value={fundamental.earnings_surprise ? `${fundamental.earnings_surprise.toFixed(1)}%` : null} />
          <Row label="News Sentiment"    value={fundamental.sentiment_score?.toFixed(3)} />
        </Section>
      )}

      {macro && (
        <Section title="Macro">
          <Row label="GDP Growth"    value={macro.gdp_growth ? `${macro.gdp_growth.toFixed(1)}%` : null} />
          <Row label="CPI Index"     value={macro.cpi?.toFixed(1)} />
          <Row label="Interest Rate" value={macro.interest_rate ? `${macro.interest_rate.toFixed(2)}%` : null} />
        </Section>
      )}

      {news?.length > 0 && (
        <Section title={`Recent News (${news.length})`}>
          {news.slice(0, 4).map(a => (
            <div key={a.id} style={{ marginBottom: 8 }}>
              <a href={a.url} target="_blank" rel="noreferrer"
                style={{ fontSize: 12, color: "#7c83fd", textDecoration: "none" }}>
                {a.title?.slice(0, 80)}…
              </a>
              <span style={{ fontSize: 11, color: "#666", marginLeft: 8 }}>
                {a.sentiment_score > 0 ? "▲" : a.sentiment_score < 0 ? "▼" : "–"}
              </span>
            </div>
          ))}
        </Section>
      )}
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ fontSize: 12, color: "#666", fontWeight: 600, marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>{title}</div>
      {children}
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
      <span style={{ color: "#888" }}>{label}</span>
      <span style={{ color: value ? "#e0e0e0" : "#444" }}>{value ?? "N/A"}</span>
    </div>
  );
}