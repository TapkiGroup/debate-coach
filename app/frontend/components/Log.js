export default function Log({ log }) {
  return (
    <div style={{ marginTop: 20 }}>
      <h2>Log</h2>
      <ul>
        {log.map((item, i) => (
          <li key={i}>
            <b>{item.action}</b>
            <pre>{JSON.stringify(item, null, 2)}</pre>
          </li>
        ))}
      </ul>
    </div>
  );
}
