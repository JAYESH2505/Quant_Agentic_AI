import { useState } from "react";
import axios from "axios";
import SignalsPanel from "../components/SignalsPanel";
import FundamentalsPanel from "../components/FundamentalsPanel";
import SynthesisCard from "../components/SynthesisCard";
import PriceChart from "../components/PriceChart";

const API = "http://localhost:8000";

export default function Analyze() {
  const [ticker, setTicker]   = useState("");
  const [runId, setRunId]     = useState(null);
  const [report, setReport]   = useState(null);
  const [status, setStatus]   = useState(null);  // pending | running | completed | failed
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  async function handleAnalyze() {
    if (!ticker.trim()) return;
    setLoading(true);
    setError(null);
    setReport(null);
    setStatus("pending");

    try {
      const res = await axios.post(`${API}/analyze/${ticker.trim().toUpperCase()}`);
      const id  = res.data.id;
      setRunId(id);
      pollReport(id);
    } catch (e) {
      setError("Failed to start analysis. Is the backend running?");
      setLoading(false);
    }
  }

  function pollReport(id) {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${API}/report/${id}`);
        const data = res.data;
        setStatus(data.run.status);

        if (data.run.status === "completed") {
          setReport(data);
          setLoading(false);
          clearInterval(interval);
        } else if (data.run.status === "failed") {
          setError(`Analysis failed: ${data.run.error || "Unknown error"}`);
          setLoading(false);
          clearInterval(interval);
        }
      } catch {
        // keep polling
      }
    }, 2500);
  }

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      {/* Input */}
      <div style={{ display: "flex", gap: 12, marginBottom: 32 }}>
        <input
          value={ticker}
          onChange={e => setTicker(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleAnalyze()}
          placeholder="Enter ticker (e.g. AAPL)"
          style={{
            flex: 1, padding: "12px 16px", borderRadius: 8,
            background: "#1a1d27", border: "1px solid #2a2d3a",
            color: "#e0e0e0", fontSize: 16, outline: "none",
          }}
        />
        <button
          onClick={handleAnalyze}
          disabled={loading}
          style={{
            padding: "12px 28px", borderRadius: 8, border: "none",
            background: loading ? "#3a3d4a" : "#7c83fd", color: "#fff",
            fontWeight: 600, fontSize: 15, cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Analysing…" : "Analyse"}
        </button>
      </div>

      {/* Status badge */}
      {status && !report && (
        <div style={{ marginBottom: 24, color: "#aaa", fontSize: 14 }}>
          Status: <StatusBadge status={status} />
          {loading && <span style={{ marginLeft: 8 }}>Polling for results…</span>}
        </div>
      )}

      {/* Error */}
      {error && (
        <div style={{ background: "#2a1a1a", border: "1px solid #c0392b", borderRadius: 8, padding: 16, color: "#e74c3c", marginBottom: 24 }}>
          {error}
        </div>
      )}

      {/* Report */}
      {report && (
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <SynthesisCard report={report.report} ticker={ticker.toUpperCase()} />
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
            <SignalsPanel signals={report.technical_signals} />
            <FundamentalsPanel fundamental={report.fundamental} macro={report.macro} news={report.news} />
          </div>
          <PriceChart runId={runId} ticker={ticker.toUpperCase()} />
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = { pending: "#f39c12", running: "#3498db", completed: "#2ecc71", failed: "#e74c3c" };
  return (
    <span style={{ background: colors[status] + "22", color: colors[status], padding: "2px 10px", borderRadius: 12, fontSize: 13, fontWeight: 600 }}>
      {status}
    </span>
  );
}