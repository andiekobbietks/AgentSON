const resp = await fetch('http://localhost:9222/json');
const targets = await resp.json();
const target = targets.find(t => !t.url.startsWith('chrome-extension://'));
const ws = new WebSocket(target.webSocketDebuggerUrl);

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

// Navigate to chrome://flags
await cdp('Page.navigate', { url: 'chrome://flags/' });
await new Promise(r => setTimeout(r, 3000));

// Get the page content and search for our flags
const result = await cdp('Runtime.evaluate', {
  expression: `
    JSON.stringify((() => {
      const text = document.body.innerText || '';
      return text.split('\\n').filter(l => 
        l.includes('prompt') || l.includes('optimization') || l.includes('gemini') || l.includes('nano') || 
        l.includes('on-device') || l.includes('LanguageModel') || l.includes('Prompt API') || l.includes('Enable on-device')
      ).slice(0, 40);
    })());
  `,
  awaitPromise: true
});
console.log('=== Flag-related page content ===');
try { console.log(JSON.parse(result.result?.result?.value || '[]').join('\n')); } catch(e) { console.log('Raw:', result.result?.result?.value); }

// Also get the full HTML title
const titleResult = await cdp('Runtime.evaluate', { expression: 'document.title', awaitPromise: false });
console.log('\n=== Page title: ' + titleResult.result?.result?.value);

// Get the full page search box text
const searchResult = await cdp('Runtime.evaluate', {
  expression: `
    JSON.stringify((() => {
      // Get all experiment names visible on the page
      const names = Array.from(document.querySelectorAll('.experiment-name')).map(el => el.textContent.trim()).filter(Boolean);
      // Also check for flags-app shadow DOM
      return names.slice(0, 50);
    })());
  `,
  awaitPromise: true
});
console.log('\n=== Experiment names ===');
try { console.log(JSON.parse(searchResult.result?.result?.value || '[]').join('\n')); } catch(e) { console.log('Raw:', searchResult.result?.result?.value); }

ws.close();
