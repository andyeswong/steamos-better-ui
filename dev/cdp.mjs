// Evaluate JS in a Steam CEF tab via the remote debugger.
// Tunnel first: ssh -N -L 18080:127.0.0.1:8080 <user>@<device>
// Usage: node cdp.mjs "<tab title>" <file.js | -e "expr">
// Expects an SSH tunnel: localhost:18080 -> ally 127.0.0.1:8080
const [title, mode, arg] = process.argv.slice(2);
const fs = await import('node:fs');
const expr = mode === '-e' ? arg : fs.readFileSync(mode, 'utf8');

const tabs = await (await fetch('http://localhost:18080/json')).json();
const tab = tabs.find(t => t.title === title);
if (!tab) { console.error('tab not found:', tabs.map(t => t.title)); process.exit(1); }

const ws = new WebSocket(tab.webSocketDebuggerUrl.replace(/ws:\/\/[^/]+/, 'ws://localhost:18080'));
ws.onopen = () => ws.send(JSON.stringify({
  id: 1, method: 'Runtime.evaluate',
  params: { expression: expr, returnByValue: true, awaitPromise: true },
}));
ws.onmessage = (m) => {
  const r = JSON.parse(m.data);
  if (r.id !== 1) return;
  const res = r.result?.result;
  if (r.result?.exceptionDetails) console.error(JSON.stringify(r.result.exceptionDetails, null, 1));
  else console.log(typeof res?.value === 'string' ? res.value : JSON.stringify(res?.value, null, 1));
  ws.close();
};
