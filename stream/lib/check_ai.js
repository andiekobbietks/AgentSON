const resp = await fetch('http://localhost:9222/json');
const targets = await resp.json();
const target = targets.find(t => !t.url.startsWith('chrome-extension://'));
const ws = new WebSocket(target.webSocketDebuggerUrl);

await new Promise((r) => ws.onopen = r);

function cdp(method, params) {
  return new Promise((res, rej) => {
    const id = Math.floor(Math.random() * 100000);
    const handler = (event) => {
      const raw = typeof event.data === 'string' ? event.data : event.data?.toString();
      if (!raw) return;
      try {
        const response = JSON.parse(raw);
        if (response.id === id) { ws.removeEventListener('message', handler); res(response); }
      } catch {}
    };
    ws.addEventListener('message', handler);
    ws.send(JSON.stringify({ id, method, params }));
    setTimeout(() => { ws.removeEventListener('message', handler); rej(new Error('timeout')); }, 10000);
  });
}

await cdp('Page.enable', {});
await cdp('Page.navigate', { url: 'about:blank' });
await new Promise(r => setTimeout(r, 2000));

const checks = [
  'typeof LanguageModel',
  'typeof window.LanguageModel',
  'typeof globalThis.LanguageModel',
  'Object.keys(window).filter(k => k.includes("LanguageModel") || k.includes("AI") || k.includes("Model") || k.includes("Gemini") || k.includes("Prompt"))',
  'typeof navigator.ai',
  'typeof window.ai',
  '!!window.chrome',
  'typeof window.chrome.ai',
  '!!chrome',
  'typeof chrome.ai'
];

for (const check of checks) {
  const result = await cdp('Runtime.evaluate', { expression: check, awaitPromise: false });
  const val = result.result?.result?.value;
  console.log(check + ' => ' + JSON.stringify(val));
}

// Check all window properties that contain AI
const allProps = await cdp('Runtime.evaluate', { 
  expression: `Object.getOwnPropertyNames(window).filter(p => p.match(/ai|AI|Ai|model|Model|nano|Nano|gemini|Gemini|prompt|Prompt/))`,
  awaitPromise: false
});
console.log('AI-related window props:', JSON.stringify(allProps.result?.result?.value));

ws.close();
