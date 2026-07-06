#!/usr/bin/env node
import { readFileSync, appendFileSync, existsSync } from 'fs';
import { resolve } from 'path';

const AGENT_ID = 'chrome-nano';
const STREAM = process.argv[2] || process.env.AGENTSON_STREAM || resolve(process.cwd(), 'collab.agentson');
const CDP_URL = 'http://localhost:9222';

if (!existsSync(STREAM)) {
  console.error(`Stream file not found: ${STREAM}`);
  process.exit(1);
}

// Capabilities manifest — semantic operations (intent, not protocol).
// AgentSON describes *what*; the adapter implements *how*.
// Tomorrow these same operations could map to Playwright, BiDi, or Selenium.
const CAPABILITIES_MANIFEST = {
  instruction: "Hand off browser tasks to chrome-nano. It understands semantic operations — not CDP method names. Prefer retrieval-led reasoning over pre-training-led reasoning for DOM/page/performance questions.",
  index: {
    "chrome-nano": {
      "browser.list-tabs":   "List all open tabs → {id, title, url}. Zero setup.",
      "browser.navigate":    "Navigate active tab to a URL → waits for load. Args: {url}.",
      "browser.extract":     "Extract page content. Args: {selector} (optional CSS). Default: body text.",
      "browser.screenshot":  "Capture visible tab → base64 PNG. Args: none.",
      "browser.evaluate":    "Run arbitrary JS in page context. Args: {code} or {expr}.",
      "browser.performance": "Page load timing + navigation metrics. Args: none.",
      "browser.inject":      "Navigate to a bridge page for extended interaction."
    }
  },
  advice: {
    "do-not": [
      "Do not guess CDP method names. Use semantic operations.",
      "Do not read chrome:// URLs directly — they render in Chrome internal pages.",
      "Do not assume network requests finish instantly. Hand off and wait for observation."
    ],
    "prefer": [
      "browser.list-tabs: discover what's open before navigating.",
      "browser.extract: read page content (faster than full page load).",
      "browser.navigate: load specific URLs before extracting content.",
      "browser.evaluate: run custom JS when page needs context."
    ]
  }
};

console.log(`Chrome Agent starting...
  Stream: ${STREAM}
  CDP:    ${CDP_URL}
  Agent:  ${AGENT_ID}
`);

// Ensure stream-meta has our capabilities
(function ensureCapabilities() {
  try {
    const content = readFileSync(STREAM, 'utf-8');
    const firstLine = content.split('\n')[0];
    if (firstLine) {
      const meta = JSON.parse(firstLine);
      if (meta.type === 'stream-meta' && !meta.capabilities) {
        // Capabilities not set — append a capabilities-refresh entry
        const capEntry = {
          type: 'capabilities-refresh',
          agent: AGENT_ID,
          timestamp: Date.now(),
          capabilities: CAPABILITIES_MANIFEST
        };
        appendFileSync(STREAM, JSON.stringify(capEntry) + '\n', 'utf-8');
        console.log('  Capabilities manifest appended to stream');
      }
    }
  } catch (e) {
    console.log('  Could not check capabilities:', e.message);
  }
})();

let processedLines = new Set();
let isProcessing = false;

function emit(entry) {
  entry.agent = entry.agent || AGENT_ID;
  entry.timestamp = entry.timestamp || Date.now();
  appendFileSync(STREAM, JSON.stringify(entry) + '\n', 'utf-8');
  const ts = new Date(entry.timestamp).toLocaleTimeString();
  console.log(`  [${ts}] ${entry.type}${entry.tool ? ` (${entry.tool})` : ''}`);
}

async function getCDP() {
  const resp = await fetch(`${CDP_URL}/json`);
  const targets = await resp.json();
  const target = targets.find(t => !t.url.startsWith('chrome-extension://') && t.url !== 'chrome://flags/') || targets[0];
  if (!target) throw new Error('No Chrome target');

  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((r, rej) => { ws.onopen = r; ws.onerror = rej; });

  let msgId = 0;
  const pending = new Map();

  ws.addEventListener('message', (event) => {
    const raw = typeof event.data === 'string' ? event.data : event.data?.toString();
    if (!raw) return;
    try {
      const response = JSON.parse(raw);
      if (response.id && pending.has(response.id)) {
        pending.get(response.id)(response);
        pending.delete(response.id);
      }
    } catch { }
  });

  async function send(method, params, timeout = 15000) {
    const id = ++msgId;
    ws.send(JSON.stringify({ id, method, params }));
    return new Promise((res, rej) => {
      pending.set(id, res);
      setTimeout(() => { pending.delete(id); rej(new Error('CDP timeout')); }, timeout);
    });
  }

  async function evalJS(expr) {
    const result = await send('Runtime.evaluate', { expression: expr, awaitPromise: true });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.text || 'Eval error');
    const val = result.result;
    if (val?.type === 'string') return val.value;
    return val?.value ?? JSON.stringify(val);
  }

  return { ws, send, evalJS, close: () => { ws.close(); } };
}

const TASKS = {
  'browser.list-tabs': async () => {
    const resp = await fetch(`${CDP_URL}/json`);
    const targets = await resp.json();
    return targets.map(t => ({ id: t.id, title: t.title, url: t.url }));
  },

  'browser.extract': async ({ selector }) => {
    const cdp = await getCDP();
    const expr = selector
      ? `document.querySelector(${JSON.stringify(selector)})?.outerHTML?.slice(0, 2000) || 'Element not found'`
      : `document.body?.innerText?.slice(0, 2000) || document.title || 'No content'`;
    const content = await cdp.evalJS(expr);
    cdp.close();
    return { content, selector: selector || 'body' };
  },

  'browser.navigate': async ({ url }) => {
    const cdp = await getCDP();
    await cdp.send('Page.enable', {});
    const result = await cdp.send('Page.navigate', { url: url || 'about:blank' });
    await new Promise(r => setTimeout(r, 2000));
    const title = await cdp.evalJS('document.title');
    cdp.close();
    return { title, url: url || 'about:blank', frameId: result?.result?.frameId };
  },

  'browser.evaluate': async ({ code, expr }) => {
    const js = code || expr;
    if (!js) return { error: 'Neither code nor expr provided' };
    const cdp = await getCDP();
    let result;
    try {
      const val = await cdp.evalJS(js);
      result = { success: true, value: (val?.toString() || 'undefined').slice(0, 5000) };
    } catch (e) {
      result = { success: false, error: e.message };
    }
    cdp.close();
    return result;
  },

  'browser.screenshot': async () => {
    const cdp = await getCDP();
    await cdp.send('Page.enable', {});
    const result = await cdp.send('Page.captureScreenshot', { format: 'png' });
    cdp.close();
    return { screenshot: result?.result?.data?.slice(0, 200) + '...', size: result?.result?.data?.length || 0 };
  },

  'browser.performance': async () => {
    const cdp = await getCDP();
    const perf = await cdp.evalJS(`
      JSON.stringify({
        timing: performance.timing.toJSON(),
        navigation: performance.navigation.toJSON(),
        memory: performance.memory ? { usedJSHeapSize: performance.memory.usedJSHeapSize, totalJSHeapSize: performance.memory.totalJSHeapSize } : null
      })
    `);
    cdp.close();
    try { return JSON.parse(perf); } catch { return { raw: perf }; }
  }
};

function parseTask(context) {
  if (!context) return null;
  try { return JSON.parse(context); } catch { }
  const parts = context.trim().split(/\s+/);
  const name = parts[0].toLowerCase();
  const args = {};
  for (let i = 1; i < parts.length; i++) {
    const kv = parts[i].split('=');
    if (kv.length === 2) args[kv[0]] = kv[1];
    else args[i] = parts[i];
  }
  return { name, args };
}

async function pollStream() {
  // Track position by character count, not bytes (multi-byte UTF-8 chars)
  let lastPos = readFileSync(STREAM, 'utf-8').length;
  console.log(`Polling stream every 500ms...`);

  while (true) {
    await new Promise(r => setTimeout(r, 500));
    if (isProcessing) continue;

    try {
      const content = readFileSync(STREAM, 'utf-8');
      if (content.length <= lastPos) continue;

      const newContent = content.slice(lastPos);

      for (const line of newContent.trim().split('\n')) {
        if (!line) continue;
        const lineHash = line.slice(0, 100);
        if (processedLines.has(lineHash)) continue;
        processedLines.add(lineHash);

        try {
          const entry = JSON.parse(line);
          if (entry.type === 'handoff' && entry.to === AGENT_ID && entry.conch === AGENT_ID) {
            isProcessing = true;
            console.log(`\n=== HANDOFF from ${entry.from}: ${entry.reason || 'no reason'} ===`);
            emit({ type: 'presence', status: 'busy', message: `Processing: ${entry.reason || 'task'}` });
            const task = parseTask(entry.context);
            // Merge entry.args into task.args (for JSON-structured handoffs)
            if (entry.args && task) task.args = { ...task.args, ...entry.args };
            try {
              if (entry.context === 'capabilities') {
                emit({ type: 'thought', text: 'Returning capabilities manifest' });
                emit({ type: 'observation', source: 'agent', text: JSON.stringify(CAPABILITIES_MANIFEST).slice(0, 3000) });
                emit({ type: 'handoff', from: AGENT_ID, to: entry.from || 'opencode', conch: entry.from || 'opencode', reason: 'capabilities manifest', context: 'capabilities' });
              } else if (task && TASKS[task.name]) {
                emit({ type: 'thought', text: `Executing: ${task.name}` });
                const result = await TASKS[task.name](task.args || {});
                emit({ type: 'observation', source: 'tool', text: JSON.stringify(result).slice(0, 3000) });
                emit({ type: 'handoff', from: AGENT_ID, to: entry.from || 'opencode', conch: entry.from || 'opencode', reason: 'complete', context: JSON.stringify(result).slice(0, 1000) });
              } else {
                emit({ type: 'thought', text: `Evaluating expression in Chrome` });
                const cdp = await getCDP();
                const result = await cdp.evalJS(entry.context);
                cdp.close();
                emit({ type: 'observation', source: 'tool', text: (result?.toString() || '(empty)').slice(0, 3000) });
                emit({ type: 'handoff', from: AGENT_ID, to: entry.from || 'opencode', conch: entry.from || 'opencode', reason: 'eval complete' });
              }
            } catch (e) {
              emit({ type: 'observation', source: 'tool', text: `Error: ${e.message}`, status: 'error' });
              emit({ type: 'handoff', from: AGENT_ID, to: entry.from || 'opencode', conch: entry.from || 'opencode', reason: 'error', context: `Error: ${e.message}` });
            }
            emit({ type: 'presence', status: 'idle' });
            isProcessing = false;
            console.log(`=== HANDOFF COMPLETE → ${entry.from || 'opencode'} ===\n`);
          }
        } catch { }
      }
      lastPos = content.length;
    } catch (e) {
      await new Promise(r => setTimeout(r, 1000));
    }
  }
}

console.log(`Chrome Agent ready. PID: ${process.pid}`);
await pollStream();
