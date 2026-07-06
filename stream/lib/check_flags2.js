// Check chrome://flags page content to verify flag state
const resp = await fetch('http://localhost:9222/json');
const targets = await resp.json();

// Find the chrome://flags page
let flagsTarget = targets.find(t => t.url.startsWith('chrome://flags'));
if (!flagsTarget) flagsTarget = targets[0];

const ws = new WebSocket(flagsTarget.webSocketDebuggerUrl);
await new Promise((r) => ws.onopen = r);

function cdp(method, params, timeout = 10000) {
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
    setTimeout(() => { ws.removeEventListener('message', handler); rej(new Error('timeout')); }, timeout);
  });
}

await cdp('Page.enable', {});
await cdp('Page.navigate', { url: 'chrome://flags/' });
await new Promise(r => setTimeout(r, 3000));

// Use the search box to find our flags
const searchResult = await cdp('Runtime.evaluate', {
  expression: `
    JSON.stringify((() => {
      // Try to use the search box
      const searchInput = document.querySelector('flags-app')?.shadowRoot?.querySelector('input#search');
      const results = [];
      
      if (searchInput) {
        results.push('Found search input via shadow DOM');
        // Try searching for 'prompt'
        searchInput.value = 'prompt';
        searchInput.dispatchEvent(new Event('input'));
        // Wait for filter...
      } else {
        results.push('No shadow DOM search input found');
      }
      
      // Fallback: check innerText for flag mentions
      const text = document.body.innerText || '';
      const promptLines = text.split('\\n').filter(l => 
        l.toLowerCase().includes('prompt') || 
        l.toLowerCase().includes('gemini') || 
        l.toLowerCase().includes('nano') ||
        l.toLowerCase().includes('optimization guide') ||
        l.toLowerCase().includes('on device')
      ).slice(0, 30);
      results.push(...promptLines);
      
      return results;
    })());
  `,
  awaitPromise: true
});

try {
  const val = JSON.parse(searchResult.result?.result?.value || '[]');
  console.log('=== Flags page: prompt/Gemini content ===');
  val.forEach(l => console.log('  ' + l));
} catch(e) {
  console.log('Parse error:', e.message);
  console.log('Raw:', searchResult.result?.result?.value);
}

// Also check chrome://version for Chrome channel
await cdp('Page.navigate', { url: 'chrome://version/' });
await new Promise(r => setTimeout(r, 2000));

const verResult = await cdp('Runtime.evaluate', {
  expression: `JSON.stringify(document.body.innerText.split('\\n').filter(Boolean).slice(0, 40))`,
  awaitPromise: true
});
try {
  const lines = JSON.parse(verResult.result?.result?.value || '[]');
  console.log('\n=== chrome://version ===');
  lines.forEach(l => console.log('  ' + l));
} catch(e) {
  console.log('Version parse error:', e.message);
}

// Now check on an about:blank page for LanguageModel directly
await cdp('Page.navigate', { url: 'about:blank' });
await new Promise(r => setTimeout(r, 1000));

const lmResult = await cdp('Runtime.evaluate', {
  expression: `JSON.stringify({ 
    hasLanguageModel: typeof LanguageModel !== 'undefined',
    hasWindowLanguageModel: typeof window.LanguageModel !== 'undefined',
    hasChromeAI: typeof chrome !== 'undefined' && typeof chrome.ai !== 'undefined',
    hasNavigatorAI: typeof navigator !== 'undefined' && typeof navigator.ai !== 'undefined',
    userAgent: navigator.userAgent
  })`,
  awaitPromise: false
});
try {
  console.log('\n=== API availability ===');
  console.log(JSON.parse(lmResult.result?.result?.value || '{}'));
} catch(e) {
  console.log('LM parse error:', e.message);
}

ws.close();
