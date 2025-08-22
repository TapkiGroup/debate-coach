"use client";

import { useEffect, useMemo, useRef, useState } from "react";

export default function Home() {
  const API =
    typeof window !== "undefined"
      ? `${window.location.origin.replace(/\/$/, "")}/api`
      : (process.env.NEXT_PUBLIC_BACKEND_URL || "/api");

  useEffect(() => {
    console.log("API base =", API);
  }, []);

  useEffect(() => {
    newSession(mode);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // State
  const [starting, setStarting] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [mode, setMode] = useState("debate_counter");

  const [columns, setColumns] = useState({ PRO: [], CON: [], SOURCES: [] });
  const [strength, setStrength] = useState(null);

  const [userText, setUserText] = useState("");
  const [chat, setChat] = useState([]); 

  // --- API helpers ---

  async function tryPostJSON(paths, bodies, extraHeaders) {
    const headers = { "Content-Type": "application/json", ...(extraHeaders || {}) };
    const errors = [];
    for (const p of (Array.isArray(paths) ? paths : [paths])) {
      for (const body of (Array.isArray(bodies) ? bodies : [bodies])) {
        try {
          const res = await fetch(`${API}${p}`, { method: "POST", headers, body: JSON.stringify(body) });
          if (res.ok) return { ok: true, path: p, body, data: await res.json(), status: res.status };
          errors.push({ path: p, status: res.status, text: await res.text() });
        } catch (e) {
          errors.push({ path: p, err: String(e) });
        }
      }
    }
    return { ok: false, errors };
  }

  async function tryGetJSON(paths, query) {
    const qs = query ? (query.startsWith("?") ? query : `?${query}`) : "";
    const errors = [];
    for (const p of (Array.isArray(paths) ? paths : [paths])) {
      try {
        const res = await fetch(`${API}${p}${qs}`);
        if (res.ok) return { ok: true, path: p, data: await res.json(), status: res.status };
        errors.push({ path: p, status: res.status, text: await res.text() });
      } catch (e) {
        errors.push({ path: p, err: String(e) });
      }
    }
    return { ok: false, errors };
  }

  async function newSession(initialMode = mode) {
    try {
      setStarting(true);

      // Use the correct backend endpoint
      const r = await fetch(`${API}/session?mode=${encodeURIComponent(initialMode)}`, { method: "POST" });
      if (r.ok) {
        const data = await r.json();
        if (data?.session_id) {
          setSessionId(data.session_id);
          setColumns({ PRO: [], CON: [], SOURCES: [] });
          setStrength(null);
          setChat([]);
          return;
        }
      }

      throw new Error("No working /session endpoint found");
    } catch (e) {
      console.error(e);
      alert(String(e));
    } finally {
      setStarting(false);
    }
  }

  async function switchModeTo(newMode) {
    await newSession(newMode);
    setMode(newMode);
    await refreshColumns();
  }

  async function refreshColumns() {
    if (!sessionId) return;
    try {
      const r = await fetch(`${API}/columns?session_id=${encodeURIComponent(sessionId)}`);
      if (r.ok) {
        const data = await r.json();
        setColumns({
          PRO: Array.isArray(data.PRO) ? data.PRO : [],
          CON: Array.isArray(data.CON) ? data.CON : [],
          SOURCES: Array.isArray(data.SOURCES) ? data.SOURCES : [],
        });
      } else {
        setColumns({ PRO: [], CON: [], SOURCES: [] });
      }
    } catch {
      setColumns({ PRO: [], CON: [], SOURCES: [] });
    }
  }

  async function send(text) {
    if (!sessionId) return alert("Start a session first!");
    const trimmed = text.trim();
    if (!trimmed) return;

    setChat((c) => [...c, { role: "user", text: trimmed }]);
    setUserText("");

    try {
      const response = await fetch(`${API}/chat`, {
        method: "POST",
        body: JSON.stringify({ session_id: sessionId, user_text: trimmed }),
        headers: { "Content-Type": "application/json" },
      });
      let reply = "⚠️ No reply from model.";
      if (response.ok) {
        const data = await response.json();
        if (typeof data.chat_reply === "string" && data.chat_reply.trim()) {
          reply = data.chat_reply;
        }
        if (data?.score && typeof data.score.value === "number") setStrength(data.score.value);
      } else {
        reply = `⚠️ Chat failed: ${await response.text()}`;
      }
      setChat(prev => [...prev, { role: "assistant", text: reply }]);
      await refreshColumns();
    } catch (e) {
      setChat(prev => [...prev, { role: "assistant", text: `⚠️ Chat error: ${String(e)}` }]);
      await refreshColumns();
    }
  }

  useEffect(() => {
    newSession(mode);
  }, []);

  const styles = useMemo(
    () => ({
      app: {
        height: "100vh",
        display: "flex",
        fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif",
      },
      leftPane: {
        flex: 5,
        background: "#FFF9DB", // pale yellow
        display: "flex",
        flexDirection: "column",
        padding: "16px 16px 0 16px",
        gap: 12,
        minWidth: 0,
      },
      rightPane: {
        flex: 1,
        background: "#FFD8A8", // soft orange
        padding: 16,
        display: "flex",
        flexDirection: "column",
        gap: 16,
        minWidth: 240,
      },
      titleRow: {
        display: "flex",
        alignItems: "baseline",
        justifyContent: "space-between",
      },
      title: {
        margin: 0,
        fontSize: 24,
        fontWeight: 700,
      },
      sessionInfo: {
        fontSize: 12,
        opacity: 0.7,
      },
      threeColsRow: {
        display: "grid",
        gridTemplateColumns: "1fr 1fr 1fr",
        gap: 12,
        height: 240, // fixed height + scroll
      },
      col: {
        border: "1px solid rgba(0,0,0,0.1)",
        borderRadius: 8,
        background: "#FFFFFF",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      },
      colHeader: {
        padding: "8px 10px",
        fontWeight: 700,
        borderBottom: "1px solid rgba(0,0,0,0.06)",
        background: "#FFF5E6",
      },
      colScroll: {
        padding: 10,
        overflowY: "auto",
        whiteSpace: "pre-wrap",
        wordBreak: "break-word",
        fontSize: 14,
        lineHeight: 1.35,
      },
      scoreRow: {
        display: "grid",
        gridTemplateColumns: "1fr 1fr 1fr",
        gap: 12,
      },
      scoreCell: {
        height: 56,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "transparent",
        borderRadius: 8,
        fontWeight: 700,
        fontSize: 18,
      },
      chatWrap: {
        display: "flex",
        flexDirection: "column",
        gap: 8,
        height: 280, // fixed height
        border: "1px solid rgba(0,0,0,0.1)",
        borderRadius: 8,
        background: "#FFFFFF",
        overflow: "hidden",
      },
      chatScroll: {
        flex: 1,
        overflowY: "auto",
        padding: 12,
        display: "flex",
        flexDirection: "column",
        gap: 8,
      },
      bubbleUser: {
        alignSelf: "flex-end",
        maxWidth: "80%",
        background: "#E6F4FF",
        border: "1px solid rgba(0,0,0,0.06)",
        padding: "8px 10px",
        borderRadius: 10,
        whiteSpace: "pre-wrap",
      },
      bubbleAssistant: {
        alignSelf: "flex-start",
        maxWidth: "80%",
        background: "#F7F7F7",
        border: "1px solid rgba(0,0,0,0.06)",
        padding: "8px 10px",
        borderRadius: 10,
        whiteSpace: "pre-wrap",
      },
      inputRow: {
        display: "flex",
        gap: 8,
        padding: 8,
        borderTop: "1px solid rgba(0,0,0,0.06)",
      },
      input: {
        flex: 1,
        padding: "10px 12px",
        borderRadius: 8,
        border: "1px solid rgba(0,0,0,0.2)",
        outline: "none",
        fontSize: 14,
      },
      sendBtn: {
        padding: "10px 14px",
        borderRadius: 8,
        border: "1px solid rgba(0,0,0,0.2)",
        background: "#FFEC99",
        fontWeight: 700,
        cursor: "pointer",
      },
      modeBtn: {
        padding: "10px 12px",
        borderRadius: 8,
        border: "1px solid rgba(0,0,0,0.2)",
        background: "#FFE8CC",
        fontWeight: 700,
        cursor: "pointer",
        textAlign: "center",
      },
      rightCard: {
        background: "rgba(255,255,255,0.55)",
        border: "1px solid rgba(0,0,0,0.08)",
        borderRadius: 10,
        padding: 12,
      },
      small: { fontSize: 12, opacity: 0.7 },
    }),
    []
  );

  // auto-scroll chat
  const scrollRef = useRef(null);
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chat]);

  return (
    <div style={styles.app}>
      {/* LEFT (pale yellow) */}
      <div style={styles.leftPane}>
        {/* Title row */}
        <div style={styles.titleRow}>
          <h1 style={styles.title}>Debate Coach</h1>
          <div style={styles.sessionInfo}>
            Session: {sessionId ?? "—"} &nbsp;|&nbsp; Mode: {mode}
            {starting ? " (starting…)" : ""}
          </div>
        </div>

        {/* Three columns: SOURCES · PRO · CON */}
        <div style={styles.threeColsRow}>
          {/* SOURCES */}
          <div style={styles.col}>
            <div style={styles.colHeader}>SOURCES</div>
            <div style={styles.colScroll}>
              {columns.SOURCES?.length ? (
                columns.SOURCES.map((t, i) => (
                  <div key={`src-${i}`}>• {typeof t === "string" ? t : t.title || t.url || JSON.stringify(t)}</div>
                ))
              ) : (
                <span style={styles.small}>No sources yet</span>
              )}
            </div>
          </div>
          {/* PRO */}
          <div style={styles.col}>
            <div style={styles.colHeader}>PRO</div>
            <div style={styles.colScroll}>
              {columns.PRO?.length ? (
                columns.PRO.map((t, i) => (
                  <div key={`pro-${i}`}>• {typeof t === "string" ? t : t.payload?.text || t.payload?.claim || JSON.stringify(t)}</div>
                ))
              ) : (
                <span style={styles.small}>No pro points yet</span>
              )}
            </div>
          </div>
          {/* CON */}
          <div style={styles.col}>
            <div style={styles.colHeader}>CON</div>
            <div style={styles.colScroll}>
              {columns.CON?.length ? (
                columns.CON.map((t, i) => (
                  <div key={`con-${i}`}>• {typeof t === "string" ? t : t.payload?.text || t.payload?.claim || JSON.stringify(t)}</div>
                ))
              ) : (
                <span style={styles.small}>No con points yet</span>
              )}
            </div>
          </div>
        </div>
        {/* Score row under PRO (center cell) */}
        <div style={styles.scoreRow}>
          <div style={styles.scoreCell}></div>
          <div style={{ ...styles.scoreCell, background: "#FFF5E6", border: "1px solid rgba(0,0,0,0.06)" }}>
            {typeof strength === "number" ? `Score: ${strength}` : <span style={styles.small}>Score will appear here</span>}
          </div>
          <div style={styles.scoreCell}></div>
        </div>

        {/* Chat area (wide across) */}
        <div style={styles.chatWrap}>
          <div ref={scrollRef} style={styles.chatScroll}>
            {chat.length === 0 && <div style={styles.small}>Start typing to chat with the model…</div>}
            {chat.map((m, i) => (
              <div
                key={i}
                style={m.role === "user" ? styles.bubbleUser : styles.bubbleAssistant}
              >
                {m.text}
              </div>
            ))}
          </div>
          <div style={styles.inputRow}>
            <input
              style={styles.input}
              placeholder="Your message (claim / pitch / command)"
              value={userText}
              onChange={(e) => setUserText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") send(userText);
              }}
            />
            <button style={styles.sendBtn} onClick={() => send(userText)}>
              Send
            </button>
          </div>
        </div>
      </div>

      {/* RIGHT (soft orange) */}
      <div style={styles.rightPane}>
        <div style={styles.rightCard}>
          <h3 style={{ margin: "0 0 6px 0" }}>Welcome to Debate Coach</h3>
          <div className="small">
            This demo spins up a session automatically. Use the right panel to switch modes at any time.
          </div>
        </div>

        <div style={styles.rightCard}>
          <h4 style={{ margin: "0 0 6px 0" }}>Debate Mode</h4>
          <p style={{ margin: 0 }}>
            Stress-test a claim. The model generates counters, pros/cons and sources.
          </p>
          <div style={{ height: 8 }} />
          <button
            style={styles.modeBtn}
            onClick={() => switchModeTo("debate_counter")}
            disabled={!sessionId}
            title={!sessionId ? "Session is starting…" : "Switch to Debate"}
          >
            Switch to Debate
          </button>
        </div>

        <div style={styles.rightCard}>
          <h4 style={{ margin: "0 0 6px 0" }}>Pitch Mode</h4>
          <p style={{ margin: 0 }}>
            Test a pitch. The model produces tough objections and an overall score.
          </p>
          <div style={{ height: 8 }} />
          <button
            style={styles.modeBtn}
            onClick={() => switchModeTo("pitch_objections")}
            disabled={!sessionId}
            title={!sessionId ? "Session is starting…" : "Switch to Pitch"}
          >
            Switch to Pitch
          </button>
        </div>
      </div>
    </div>
  );
}
