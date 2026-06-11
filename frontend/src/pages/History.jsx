import { useEffect, useState } from "react";
import axios from "axios";

const API = "http://localhost:8000";
const statusColors = { pending: "#f39c12", running: "#3498db", completed: "#2ecc71", failed: "#e74c3c" };

export default function History({ setPage }) {
  const [runs, setRuns]       = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/history`).then(res => {
      setRuns(res.data.runs);
      setLoading(false);
    });
  }, []);

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <h2 style={{ color: "#e0e0e0", marginBottom: 24 }}>Analysis History</h2>
      {loading ? (
        <p style={{ color: "#666" }}>Loading…</p>
      ) : runs.length === 0 ? (
        <p style={{ color: "#666" }}>No analyses yet. Run one from the Analyse page.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #2a2d3a", color: "#666", fontSize: 13 }}>
              <th style={th}>Run ID</th>
              <th style={th}>Ticker</th>
              <th style={th}>Status</th>
              <th style={th}>Started</th>
              <th style={th}>Completed</th>
            </tr>
          </thead>
          <tbody>
            {runs.map(r => (
              <tr key={r.run_id} style={{ borderBottom: "1px solid #1e2130" }}>
                <td style={td}>{r.run_id}</td>
                <td style={{ ...td, fontWeight: 600, color: "#7c83fd" }}>{r.ticker}</td>
                <td style={td}>
                  <span style={{ color: statusColors[r.status], fontWeight: 600, fontSize: 13 }}>
                    {r.status}
                  </span>
                </td>
                <td style={td}>{new Date(r.started_at).toLocaleString()}</td>
                <td style={td}>{r.completed_at ? new Date(r.completed_at).toLocaleString() : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

const th = { textAlign: "left", padding: "8px 12px" };
const td = { padding: "10px 12px", color: "#ccc", fontSize: 14 };