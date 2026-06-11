import { useState } from "react";
import Analyze from "./pages/Analyze";
import History from "./pages/History";
import "./App.css";

export default function App() {
  const [page, setPage] = useState("analyze");

  return (
    <div style={{ minHeight: "100vh", background: "#0f1117", color: "#e0e0e0", fontFamily: "Inter, sans-serif" }}>
      {/* Navbar */}
      <nav style={{ background: "#1a1d27", padding: "16px 32px", display: "flex", alignItems: "center", gap: "32px", borderBottom: "1px solid #2a2d3a" }}>
        <span style={{ fontWeight: 700, fontSize: 18, color: "#7c83fd" }}>⚡ QuantAgent</span>
        <button onClick={() => setPage("analyze")} style={navBtn(page === "analyze")}>Analyse</button>
        <button onClick={() => setPage("history")} style={navBtn(page === "history")}>History</button>
      </nav>

      <div style={{ padding: "32px" }}>
        {page === "analyze" ? <Analyze /> : <History setPage={setPage} />}
      </div>
    </div>
  );
}

function navBtn(active) {
  return {
    background: "none", border: "none", cursor: "pointer",
    color: active ? "#7c83fd" : "#888", fontWeight: active ? 600 : 400,
    fontSize: 15, borderBottom: active ? "2px solid #7c83fd" : "2px solid transparent",
    paddingBottom: 4,
  };
}