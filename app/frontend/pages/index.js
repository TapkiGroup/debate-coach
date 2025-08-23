"use client";

import { useEffect, useMemo, useRef, useState } from "react";

export default function Home() {
  const API =
    typeof window !== "undefined"
      ? `${window.location.origin.replace(/\/$/, "")}/api`
      : process.env.NEXT_PUBLIC_BACKEND_URL || "/api";

  // --- State ---
  const [starting, setStarting] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [mode, setMode] = useState("debate_counter");

  const [columns, setColumns] = useState({
    PRO: [],
    CON: [],
    SOURCES: [],
  });

  // Score: show N/100. reason
  const [strength, setStrength] = useState(null);
  const [lastReason, setLastReason] = useState("");

  const [userText, setUserText] = useState("");
  const [chat, setChat] = useState([]);
  const [fallacies, setFallacies] = useState([]); // optional “wow” panel

  // --- Helpers ---
  const trimPayload = (p) => {
    const s = typeof p === "string" ? p : JSON.stringify(p);
    return s.replace(/\n{3,}/g, "\n\n").trim(); // collapse extra blank lines
  };

  async function newSession(initialMode = mode) {
    try {
      setStarting(true);
      const r = await fetch(`${API}/session?mode=${encodeURIComponent(initialMode)}`, { method: "POST" });
      if (r.ok) {
        const data = await r.json();
        if (data?.session_id) {
          setSessionId(data.session_id);
          setColumns({ PRO: [], CON: [], SOURCES: [] });
          setStrength(null);
          setLastReason("");
          setChat([]);
          setFallacies([]);
          return data.session_id;
        }
      }
      throw new Error("No working /session endpoint found");
    } catch (e) {
      console.error(e);
      alert(String(e));
      return null;
    } finally {
      setStarting(false);
    }
  }

  async function switchModeTo(newMode) {
    setMode(newMode);
    const newId = await newSession(newMode);
    if (newId) await refreshColumns(newId);
  }

  async function refreshColumns(forId) {
    const id = forId ?? sessionId;
    if (!id) return;
    try {
      const r = await fetch(`${API}/columns?session_id=${encodeURIComponent(id)}`);
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
        if (data?.score && typeof data.score.value === "number") {
          setStrength(data.score.value);
          const r0 = Array.isArray(data.score.reasons) && data.score.reasons.length ? String(data.score.reasons[0]) : "";
          setLastReason(r0);
        }
        if (Array.isArray(data.fallacies)) setFallacies(data.fallacies);
      } else {
        reply = `⚠️ Chat failed: ${await response.text()}`;
      }
      setChat((prev) => [...prev, { role: "assistant", text: reply }]);
      await refreshColumns();
    } catch (e) {
      setChat((prev) => [...prev, { role: "assistant", text: `⚠️ Chat error: ${String(e)}` }]);
      await refreshColumns();
    }
  }

  // Start session once
  useEffect(() => {
    newSession(mode);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --- Layout ---
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
        padding: "16px 16px 12px 16px",
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
        minWidth: 260,
      },
      titleRow: {
        display: "flex",
        alignItems: "baseline",
        justifyContent: "space-between",
      },
      title: { margin: 0, fontSize: 24, fontWeight: 700 },
      sessionInfo: { fontSize: 12, opacity: 0.7 },

      // MAIN STACK IN LEFT PANE:
      // [Columns area ~ 2/3] -> [Score thin band] -> [Chat bottom ~ 1/4]
      columnsArea: {
        flex: 3, // ~ 3/4 minus score band => ~2/3 overall
        minHeight: 0,
        display: "grid",
        gridTemplateColumns: "1fr 2fr 2fr",
        gap: 12,
      },
      scoreBand: {
        height: 60,
        display: "grid",
        gridTemplateColumns: "1fr 3fr 1fr",
        gap: 12,
      },
      chatArea: {
        flex: 1, // bottom quarter
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
        border: "1px solid rgba(0,0,0,0.1)",
        borderRadius: 8,
        background: "#FFFFFF",
        overflow: "hidden",
      },

      // Column styles
      col: {
        border: "1px solid rgba(0,0,0,0.1)",
        borderRadius: 8,
        background: "#FFFFFF",
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
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
      item: {
        paddingBottom: 8,
        marginBottom: 8,
        borderBottom: "1px dashed rgba(0,0,0,0.18)", // visible divider
      },
      small: { fontSize: 12, opacity: 0.7 },

      // Score cell
      scoreCell: {
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#FFF5E6",
        border: "1px solid rgba(0,0,0,0.06)",
        borderRadius: 8,
        fontWeight: 700,
        fontSize: 16,
        textAlign: "center",
        padding: "0 10px",
      },

      // Chat
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

      // Right cards
      rightCard: {
        background: "rgba(255,255,255,0.55)",
        border: "1px solid rgba(0,0,0,0.08)",
        borderRadius: 10,
        padding: 12,
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
    }),
    []
  );

  // auto-scroll chat
  const scrollRef = useRef(null);
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [chat]);

  useEffect(() => {
    console.log("API base =", API);
  }, [API]);

  return (
    <div style={styles.app}>
      {/* LEFT */}
      <div style={styles.leftPane}>
        {/* Title */}
        <div style={styles.titleRow}>
          <h1 style={styles.title}>DebateMate</h1>
          <div style={styles.sessionInfo}>
            Session: {sessionId ?? "—"} &nbsp;|&nbsp; Mode: {mode} {starting ? " (starting…)" : ""}
          </div>
        </div>

        {/* Columns area (~2/3) */}
        <div style={styles.columnsArea}>
          {/* SOURCES */}
          <div style={styles.col}>
            <div style={styles.colHeader}>SOURCES</div>
            <div style={styles.colScroll}>
              {columns.SOURCES?.length ? (
                columns.SOURCES.map((t, i) => (
                  <div key={`src-${i}`} style={styles.item}>
                    • {typeof t === "string" ? t : t.title || t.url || JSON.stringify(t)}
                  </div>
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
                columns.PRO.map((t) => (
                  <div key={t.id} style={styles.item}>
                    {trimPayload(t.payload)}
                  </div>
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
                columns.CON.map((t) => (
                  <div key={t.id} style={styles.item}>
                    {trimPayload(t.payload)}
                  </div>
                ))
              ) : (
                <span style={styles.small}>No con points yet</span>
              )}
            </div>
          </div>
        </div>

        {/* Score thin band */}
        <div style={styles.scoreBand}>
          <div />
          <div style={styles.scoreCell}>
            {typeof strength === "number" ? (
              `${strength}/100${lastReason ? `. ${lastReason}` : ""}`
            ) : (
              <span style={styles.small}>Score will appear here</span>
            )}
          </div>
          <div />
        </div>

        {/* Chat bottom (~1/4) */}
        <div style={styles.chatArea}>
          <div ref={scrollRef} style={styles.chatScroll}>
            {chat.length === 0 && <div style={styles.small}>Start typing to chat with the model…</div>}
            {chat.map((m, i) => (
              <div key={i} style={m.role === "user" ? styles.bubbleUser : styles.bubbleAssistant}>
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
                if (e.key === "Enter" && !starting && sessionId) send(userText);
              }}
              disabled={starting || !sessionId}
            />
            <button
              style={styles.sendBtn}
              onClick={() => send(userText)}
              disabled={starting || !sessionId}
              title={!sessionId ? "Session is starting…" : "Send"}
            >
              Send
            </button>
          </div>
        </div>
      </div>

      {/* RIGHT */}
      <div style={styles.rightPane}>
        <div style={styles.rightCard}>
          <h3 style={{ margin: "0 0 6px 0" }}>Welcome to DebateMate!</h3>
          <div style={styles.small}>
            DebateMate is an AI-powered platform for structured argumentation, pitch testing, critical feedback, and objections.
          </div>
        </div>

        <div style={styles.rightCard}>
          <h4 style={{ margin: "0 0 6px 0" }}>Debate Me</h4>
        <p style={{ margin: 0 }}>Stress-test a claim or argument</p>
          <div style={{ height: 8 }} />
          <button
            style={{
              ...styles.modeBtn,
              outline: mode === "debate_counter" ? "2px solid #333" : "none",
              opacity: starting ? 0.6 : 1,
            }}
            onClick={() => switchModeTo("debate_counter")}
            disabled={starting}
          >
            Switch to Debate
          </button>
        </div>

        <div style={styles.rightCard}>
          <h4 style={{ margin: "0 0 6px 0" }}>Pitch Me</h4>
          <p style={{ margin: 0 }}>Test your pitch to prepare for objections</p>
          <div style={{ height: 8 }} />
          <button
            style={{
              ...styles.modeBtn,
              outline: mode === "pitch_objections" ? "2px solid #333" : "none",
              opacity: starting ? 0.6 : 1,
            }}
            onClick={() => switchModeTo("pitch_objections")}
            disabled={starting}
          >
            Switch to Pitch
          </button>
        </div>

        {/* Optional: Fallacies panel */}
        <div style={styles.rightCard}>
          <h4 style={{ margin: "0 0 6px 0" }}>Detected Fallacies</h4>
          {fallacies?.length ? (
            <div style={{ whiteSpace: "pre-wrap", fontSize: 14, lineHeight: 1.35 }}>
              {fallacies.map((f, i) => (
                <div key={i} style={{ marginBottom: 6 }}>
                  {f.emoji ? `${f.emoji} ` : ""}
                  {f.label}
                  {f.why ? `: ${f.why}` : ""}
                </div>
              ))}
            </div>
          ) : (
            <span style={styles.small}>None detected yet</span>
          )}
        </div>
      </div>
    </div>
  );
}
