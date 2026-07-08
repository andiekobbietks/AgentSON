// Check for Chrome task APIs (Summarizer, Translator, Language Detector)
const resp = await fetch('http://localhost:9222/json');
const targets = await resp.json();
const target = targets.find(t => t.url.startsWith('http://localhost')) || targets[0];

console.log('Using target:', target?.url);
if (!target) { console.log('No target'); process.exit(1); }

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

// Check all possible AI APIs
const apis = [
  // Prompt API (Gemini Nano)
  'typeof LanguageModel',
  'typeof window.LanguageModel',
  '"LanguageModel" in window',
  
  // Summarizer API
  'typeof Summarizer',
  'typeof window.Summarizer',
  '"Summarizer" in window',
  'typeof self.Summarizer',
  
  // Translator API
  'typeof Translator',
  'typeof window.Translator',
  '"Translator" in window',
  
  // Language Detector API
  'typeof LanguageDetector',
  'typeof window.LanguageDetector',
  '"LanguageDetector" in window',
  
  // Writer / Rewriter API
  'typeof Writer',
  'typeof Rewriter',
  
  // Generic AI detection
  '"aiOriginTrial" in document',
  '!!(document as any).aiOriginTrial',
  
  // Check for any chrome.* AI APIs
  'typeof chrome.languageModel',
  'typeof chrome.ai',
  'typeof chrome.prompt'
];

console.log('\n=== API Availability ===');
for (const expr of apis) {
  const result = await cdp('Runtime.evaluate', {
    expression: expr,
    awaitPromise: false
  });
  const val = result.result?.result?.value;
  const desc = result.result?.result?.description;
  console.log('  ' + expr.padEnd(45) + ' => ' + JSON.stringify(val) + (desc ? ' (' + desc + ')' : ''));
}

// Check navigator properties
const navResult = await cdp('Runtime.evaluate', {
  expression: `JSON.stringify({
    hasNavigatorAI: typeof navigator !== 'undefined' && 'ai' in navigator,
    navigatorAIKeys: typeof navigator.ai !== 'undefined' ? Object.keys(navigator.ai) : [],
    hasWindowAI: typeof window !== 'undefined' && 'ai' in window,
    hasChromeAI: typeof chrome !== 'undefined' && 'ai' in chrome,
    windowAISurface: typeof window !== 'undefined' && window.ai ? Object.keys(window.ai) : []
  })`,
  awaitPromise: false
});
console.log('\n=== Navigator/Window AI ===');
try { console.log(JSON.parse(navResult.result?.result?.value)); } catch(e) { console.log('Raw:', navResult.result?.result?.value); }

ws.close();
