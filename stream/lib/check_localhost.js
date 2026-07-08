const resp = await fetch('http://localhost:9222/json');
const targets = await resp.json();
const target = targets.find(t => t.url.startsWith('http://localhost')) || targets.find(t => t.url !== 'chrome://flags/' && !t.url.startsWith('chrome-extension://'));

if (!target) { console.log('NO TARGET FOUND'); process.exit(1); }

console.log('Using target:', target.url);
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => ws.onopen = r);

function cdp(method, params, timeout = 10000) {
  return new Promise((res, rej) => {
    const id = Math.floor(Math.random() * 100000);
    const handler = (event) => {
      const raw = typeof event.data === 'string' ? event.data : event.data?.toString();
      if (!raw) return;
      try { const response = JSON.parse(raw); if (response.id === id) { ws.removeEventListener('message', handler); res(response); } } catch {}
    };
    ws.addEventListener('message', handler);
    ws.send(JSON.stringify({ id, method, params }));
    setTimeout(() => { ws.removeEventListener('message', handler); rej(new Error('timeout')); }, timeout);
  });
}

await cdp('Page.enable', {});
await cdp('Page.navigate', { url: 'http://localhost/' });
await new Promise(r => setTimeout(r, 3000));

// Check AI APIs one by one
const checks = [
  'typeof LanguageModel',
  'typeof window.LanguageModel',
  'typeof self.LanguageModel',
  'typeof globalThis.LanguageModel',
  '"LanguageModel" in window',
  '"LanguageModel" in self',
  '"ai" in navigator',
  '"ai" in chrome',
  'Object.keys(window).filter(function(p) { return p.match(/[Aa][Ii]/) || p.match(/[Pp]rompt/) || p.match(/[Mm]odel/) || p.match(/[Nn]ano/); })'
];

for (const expr of checks) {
  const result = await cdp('Runtime.evaluate', {
    expression: expr,
    awaitPromise: false
  });
  console.log(expr + ' => ' + JSON.stringify(result.result?.result?.value));
}

// Also try creating a session directly (to trigger model download)
const createResult = await cdp('Runtime.evaluate', {
  expression: `(async function() {
    try {
      // Reset the page context
      const r = {};
      r.apiExists = typeof LanguageModel !== 'undefined';
      r.selfExists = typeof self !== 'undefined' && 'LanguageModel' in self;
      r.windowExists = typeof window !== 'undefined' && 'LanguageModel' in window;
      // Try to check for chrome.languageModel (extension API)
      r.chromeLM = typeof chrome !== 'undefined' && typeof chrome.languageModel !== 'undefined';
      // Check all top-level vars
      r.allKeys = Object.getOwnPropertyNames(window).slice(0, 5);
      return JSON.stringify(r);
    } catch(e) { return JSON.stringify({error: e.message}); }
  })()`,
  awaitPromise: true
});
console.log('Create result:', createResult.result?.result?.value);

ws.close();
