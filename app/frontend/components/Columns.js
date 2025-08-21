export default function Columns({ columns, strength }) {
  return (
    <div style={{ display: "flex", gap: 20, marginTop: 20 }}>
      {/* PRO */}
      <div style={{ flex: 1, border: "1px solid #ccc", padding: 10 }}>
        <h3>PRO</h3>
        <ul style={{ paddingLeft: 16 }}>
          {columns.PRO?.length
            ? columns.PRO.map((c, i) => (
                <li key={i}>
                  <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(c, null, 2)}</pre>
                </li>
              ))
            : <li>—</li>}
        </ul>
        <div style={{ marginTop: 8, color: "#d32f2f", fontWeight: 600 }}>
          {typeof strength === "number" ? `Strength score: ${strength}/100` : ""}
        </div>
      </div>

      {/* CON */}
      <div style={{ flex: 1, border: "1px solid #ccc", padding: 10 }}>
        <h3>CON</h3>
        <ul style={{ paddingLeft: 16 }}>
          {columns.CON?.length
            ? columns.CON.map((c, i) => (
                <li key={i}>
                  <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(c, null, 2)}</pre>
                </li>
              ))
            : <li>—</li>}
        </ul>
      </div>

      {/* SOURCES */}
      <div style={{ flex: 1, border: "1px solid #ccc", padding: 10 }}>
        <h3>SOURCES</h3>
        <ul style={{ paddingLeft: 16 }}>
          {columns.SOURCES?.length
            ? columns.SOURCES.map((c, i) => (
                <li key={i}>
                  <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(c, null, 2)}</pre>
                </li>
              ))
            : <li>—</li>}
        </ul>
      </div>
    </div>
  );
}
