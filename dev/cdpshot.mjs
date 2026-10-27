// Capture a CEF tab's own rendering (overlay windows that gamescope's screenshot misses in-game).
// Tunnel first: ssh -N -L 18080:127.0.0.1:8080 <user>@<device>
// Usage: node cdpshot.mjs "<tab title>" <out.png>
const [title, out] = process.argv.slice(2);
const fs = await import('node:fs');
const tabs = await (await fetch('http://localhost:18080/json')).json();
const tab = tabs.find(t => t.title === title);
if (!tab) { console.error('tab not found'); process.exit(1); }
const ws = new WebSocket(tab.webSocketDebuggerUrl.replace(/ws:\/\/[^/]+/, 'ws://localhost:18080'));
ws.onopen = () => ws.send(JSON.stringify({ id: 1, method: 'Page.captureScreenshot', params: { format: 'png' } }));
ws.onmessage = (m) => {
  const r = JSON.parse(m.data);
  if (r.id !== 1) return;
  if (r.error) console.error(r.error); else { fs.writeFileSync(out, Buffer.from(r.result.data, 'base64')); console.log(out); }
  ws.close();
};
