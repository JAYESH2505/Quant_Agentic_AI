import { useEffect, useState } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

const API = "http://localhost:8000";

export default function PriceChart({ runId, ticker }) {
  const [data] = useState([]);  

  useEffect(() => {
    if (!runId) return;
    axios.get(`${API}/report/${runId}`).then(res => {
      // OHLCV is not in FullReportOut by default — use signals run as proxy
      // For now chart the close prices from the report's ohlcv if available
    });
  }, [runId]);

  if (!data.length) return (
    <div style={{ background: "#1a1d27", borderRadius: 12, padding: 24, border: "1px solid #2a2d3a", color: "#555", textAlign: "center" }}>
      Price chart coming soon — wire OHLCV endpoint to enable
    </div>
  );

  return (
    <div style={{ background: "#1a1d27", borderRadius: 12, padding: 24, border: "1px solid #2a2d3a" }}>
      <h3 style={{ margin: "0 0 16px", color: "#e0e0e0" }}>{ticker} Price</h3>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
          <XAxis dataKey="date" tick={{ fill: "#666", fontSize: 11 }} />
          <YAxis tick={{ fill: "#666", fontSize: 11 }} />
          <Tooltip contentStyle={{ background: "#1a1d27", border: "1px solid #2a2d3a" }} />
          <Line type="monotone" dataKey="close" stroke="#7c83fd" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}