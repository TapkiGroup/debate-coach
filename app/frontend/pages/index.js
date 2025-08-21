import { useState } from "react";
import Columns from "../components/Columns";
import Log from "../components/Log";

export default function Home() {
  const API = process.env.NEXT_PUBLIC_BACKEND_URL || "http://49.13.2.245:8001/api";
  const [sessionId, setSessionId] = useState(null);
  const [mode, setMode] = useState("debate_counter");
  const [userText, setUserText] = useState("");
  const [reply, setReply] = useState(null);
  const [columns, setColumns] = useState({ PRO: [], CON: [], SOURCES: [] });
  const [log, setLog] = useState([]);
  const [strength, setStrength] = useState(null); // итоговая оценка силы

  async function newSession() {
    const r = await fetch(`${API}/session?mode=${mode}`, { method: "POST" });
    const data = await r.json();
    setSessionId(data.session_id);
    setColumns({ PRO: [], CON: [], SOURCES: [] });
    setReply(null);
    setStrength(null);
    setLog(l => [...l, { action: "newSession", data }]);
  }

  async function switchModeTo(newMode) {
    if (!sessionId) return alert("Create session first!");
    const r = await fetch(`${API}/mode`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, mode: newMode })
    });
    if (!r.ok) {
      const msg = await r.text();
      alert("Mode switch failed: " + msg);
      return;
    }
    const data = await r.json();
    setMode(newMode);
    setLog(l => [...l, { action: "switchMode", data }]);
  }

  async function send(text) {
    if (!sessionId) return alert("Start session first!");
    const r = await fetch(`${API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, user_text: text })
    });
    const data = await r.json();
    setReply(data);
    // запоминаем последнюю оценку, если пришла
    if (data && data.score && typeof data.score.value === "number") {
      setStrength(data.score.value);
    }
    setLog(l => [...l, { action: "chat", text, data }]);
    await refreshColumns();
  }

  async function refreshColumns() {
    if (!sessionId) return;
    const r = await fetch(`${API}/columns?session_id=${sessionId}`);
    const data = await r.json();
    setColumns(data);
    setLog(l => [...l, { action: "columns", data }]);
  }

  return (
    <div style={{ padding: 20, fontFamily: "system-ui" }}>
      <h1>Debate Coach UI</h1>
      <p>Session: {sessionId || "none"} | Mode: {mode}</p>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button onClick={newSession}>New session</button>
        <button onClick={() => switchModeTo("debate_counter")} disabled={!sessionId}>
          Switch to Debate
        </button>
        <button onClick={() => switchModeTo("pitch_objections")} disabled={!sessionId}>
          Switch to Pitch
        </button>
      </div>

      <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        <input
          value={userText}
          onChange={e => setUserText(e.target.value)}
          placeholder="Your message (claim / pitch / command)"
          style={{ width: 520, padding: 8 }}
        />
        <button onClick={() => send(userText)}>Send</button>
        <button onClick={() => send("evaluate_argument")}>Evaluate argument</button>
        <button onClick={() => send("give_objections")}>Give objections</button>
        <button onClick={() => send("ruthless_impression")}>Ruthless impression</button>
        <button onClick={() => send("research")}>Research</button>
        <button onClick={refreshColumns}>Refresh columns</button>
      </div>

      <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
        <button onClick={() => send("My claim: banning cash will reduce crime.")}>
          Example (Debate Claim)
        </button>
        <button onClick={() => send("Pitch: We will deliver groceries by autonomous drones in dense urban areas to cut delivery times by 80%.")}>
          Example (Pitch)
        </button>
      </div>

      <h2 style={{ marginTop: 20 }}>Last reply</h2>
      <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(reply, null, 2) || "—"}</pre>

      {/* strength красным под PRO */}
      <Columns columns={columns} strength={strength} />

      <Log log={log} />
    </div>
  );
}
