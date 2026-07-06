#!/usr/bin/env node
import { readFileSync, writeFileSync, appendFileSync, watchFile, existsSync, mkdirSync } from 'fs';
import { resolve } from 'path';

const COMMANDS = {
  init: cmdInit,
  append: cmdAppend,
  watch: cmdWatch,
  'check-nano': cmdCheckNano,
  'prompt-nano': cmdPromptNano
};

async function main() {
  const cmd = process.argv[2];
  if (!cmd || !COMMANDS[cmd]) {
    console.log(`Usage: agentson-stream <command> [args]

Commands:
  init <stream-id>              Initialize a new .agentson stream
  append <json-entry>           Append a JSON entry to the stream
  watch <stream-file>           Watch stream for new entries (live tail)
  check-nano [ws-url]           Check if Gemini Nano is available in Chrome
  prompt-nano <text> [ws-url]   Send a prompt to Gemini Nano via Chrome CDP
`);
    process.exit(1);
  }
  await COMMANDS[cmd]();
}

function getStreamPath() {
  return process.env.AGENTSON_STREAM || resolve(process.cwd(), 'collab.agentson');
}

async function cmdInit() {
  const streamId = process.argv[3] || 'collab-' + Date.now();
  const streamPath = getStreamPath();

  const meta = {
    type: 'stream-meta',
    stream_id: streamId,
    timestamp: Date.now(),
    agents: [
      { id: 'opencode', name: 'opencode', capabilities: ['bash', 'filesystem', 'search', 'read', 'write', 'edit'] },
      { id: 'chrome-nano', name: 'Chrome Gemini Nano', capabilities: ['browser', 'prompt-api', 'dom-inspection', 'performance'] }
    ],
    mode: 'jsonl'
  };

  appendFileSync(streamPath, JSON.stringify(meta) + '\n', 'utf-8');
  console.log(`Stream initialized: ${streamPath}`);
  console.log(`Stream ID: ${streamId}`);
  console.log(`AGENTSON_STREAM=${streamPath}`);
}

async function cmdAppend() {
  const streamPath = getStreamPath();
  let jsonStr = process.argv[3];

  // Support reading from stdin or a file
  if (!jsonStr || jsonStr === '-') {
    const chunks = [];
    for await (const chunk of process.stdin) chunks.push(chunk);
    jsonStr = Buffer.concat(chunks).toString('utf-8').trim();
  } else if (jsonStr.endsWith('.json') && existsSync(jsonStr)) {
    jsonStr = readFileSync(jsonStr, 'utf-8').trim();
  }

  if (!jsonStr) { console.error('Error: missing JSON entry (pipe JSON via stdin or pass as argument)'); process.exit(1); }
  let entry;
  try { entry = JSON.parse(jsonStr); } catch (e) { console.error('Error: invalid JSON'); process.exit(1); }
  if (!entry.timestamp) entry.timestamp = Date.now();
  appendFileSync(streamPath, JSON.stringify(entry) + '\n', 'utf-8');
  console.log(`Entry appended: ${entry.type}${entry.agent ? ` (${entry.agent})` : ''}`);
}

async function cmdWatch() {
  const streamPath = process.argv[3] || getStreamPath();
  if (!existsSync(streamPath)) {
    console.error(`Stream file not found: ${streamPath}`);
    process.exit(1);
  }

  let lastSize = readFileSync(streamPath).length;
  console.log(`Watching: ${streamPath} (Ctrl+C to stop)`);
  console.log('─'.repeat(50));

  watchFile(streamPath, { interval: 500 }, (curr, prev) => {
    if (curr.size > prev.size) {
      const content = readFileSync(streamPath, 'utf-8');
      const newContent = content.slice(prev.size);
      for (const line of newContent.trim().split('\n')) {
        if (!line) continue;
        try {
          const entry = JSON.parse(line);
          printEntry(entry);
        } catch { /* skip malformed */ }
      }
    }
  });

  // Print existing entries
  const content = readFileSync(streamPath, 'utf-8');
  for (const line of content.trim().split('\n')) {
    if (line) {
      try { printEntry(JSON.parse(line)); } catch {}
    }
  }

  await new Promise(() => {}); // keep alive
}

function printEntry(entry) {
  const agent = entry.agent ? `[${entry.agent}]` : '     ';
  const ts = entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : '';
  switch (entry.type) {
    case 'stream-meta':
      console.log(`\n╔══ STREAM: ${entry.stream_id} ═══`);
      console.log(`║  Agents: ${entry.agents.map(a => a.id).join(', ')}`);
      console.log(`╚═══════════════════════════════`);
      break;
    case 'handoff':
      console.log(`\n── ${ts} ${agent} HANDOFF: ${entry.from} → ${entry.to} ──`);
      if (entry.context) console.log(`   Context: ${entry.context}`);
      break;
    case 'presence':
      console.log(`   ${ts} ${agent} ${entry.status.toUpperCase()} ${entry.message || ''}`);
      break;
    case 'user-query':
      console.log(`\n📝 ${ts} ${agent} ${entry.text || entry.query}`);
      break;
    case 'thought':
      console.log(`   💭 ${ts} ${agent} ${entry.text}`);
      break;
    case 'action':
      console.log(`   ⚡ ${ts} ${agent} ${entry.tool || 'action'} ${entry.status ? `[${entry.status}]` : ''}`);
      break;
    case 'observation':
      console.log(`   👁 ${ts} ${agent} ${entry.text}`);
      break;
    case 'answer':
      console.log(`\n✅ ${ts} ${agent} ${entry.text}`);
      break;
    default:
      console.log(`   ${ts} ${agent} ${entry.type}: ${JSON.stringify(entry).slice(0, 100)}`);
  }
}

async function getCDPConnection() {
  const wsUrl = process.argv[4] || 'ws://localhost:9222/devtools/browser/000da1a4-d391-4c68-80a6-ce099b1868d7';

  // Get a page target
  const resp = await fetch('http://localhost:9222/json');
  const targets = await resp.json();
  let target = targets.find(t => t.url && !t.url.startsWith('chrome-extension://') && t.url !== 'about:blank');
  if (!target) target = targets.find(t => t.id);
  if (!target) throw new Error('No Chrome tab target found');

  const pageWsUrl = target.webSocketDebuggerUrl;
  return { pageWsUrl, target };
}

async function cmdCheckNano() {
  try {
    const WS_URL = process.argv[3] || 'ws://localhost:9222/devtools/browser/000da1a4-d391-4c68-80a6-ce099b1868d7';

    // Get page target
    const resp = await fetch('http://localhost:9222/json');
    const targets = await resp.json();
    const target = targets.find(t => t.url === 'about:blank' || (t.url && !t.url.startsWith('chrome-extension://')));
    if (!target) { console.error('No suitable target found'); process.exit(1); }

    const ws = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      ws.onopen = resolve;
      ws.onerror = reject;
    });

    // Navigate to a blank page first to set context
    await cdpSend(ws, 'Page.enable', {});
    await cdpSend(ws, 'Page.navigate', { url: 'about:blank' });
    await new Promise(r => setTimeout(r, 1000));

    // Check LanguageModel availability
    const result = await cdpEval(ws, `(async () => {
      try {
        if (typeof LanguageModel === 'undefined') {
          return JSON.stringify({ available: false, reason: 'LanguageModel API not found' });
        }
        const availability = await LanguageModel.availability();
        const params = await LanguageModel.params().catch(() => ({}));
        return JSON.stringify({ available: true, availability, params });
      } catch (e) {
        return JSON.stringify({ available: false, error: e.message });
      }
    })()`);

    const parsed = JSON.parse(result);
    console.log(JSON.stringify(parsed, null, 2));
    ws.close();
  } catch (e) {
    console.error(`Error: ${e.message}`);
    process.exit(1);
  }
}

async function cmdPromptNano() {
  const promptText = process.argv[3];
  if (!promptText) { console.error('Error: missing prompt text'); process.exit(1); }

  try {
    const WS_URL = process.argv[4] || 'ws://localhost:9222/devtools/browser/000da1a4-d391-4c68-80a6-ce099b1868d7';

    const resp = await fetch('http://localhost:9222/json');
    const targets = await resp.json();
    const target = targets.find(t => t.url === 'about:blank' || (t.url && !t.url.startsWith('chrome-extension://')));
    if (!target) { console.error('No suitable target found'); process.exit(1); }

    const ws = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      ws.onopen = resolve;
      ws.onerror = reject;
    });

    await cdpSend(ws, 'Page.enable', {});
    await cdpSend(ws, 'Page.navigate', { url: 'about:blank' });
    await new Promise(r => setTimeout(r, 1000));

    const result = await cdpEval(ws, `(async () => {
      try {
        if (typeof LanguageModel === 'undefined') {
          return JSON.stringify({ success: false, error: 'LanguageModel API not available. Ensure chrome://flags/#prompt-api-for-gemini-nano is Enabled and model is downloaded.' });
        }
        const availability = await LanguageModel.availability();
        if (availability === 'unavailable') {
          return JSON.stringify({ success: false, error: 'Gemini Nano is unavailable on this device' });
        }
        if (availability === 'after-download') {
          // Trigger download
          const session = await LanguageModel.create();
          await session.prompt('hello');
          return JSON.stringify({ success: false, status: 'downloading', message: 'Model is downloading, try again in a moment' });
        }
        const session = await LanguageModel.create();
        const response = await session.prompt(${JSON.stringify(promptText)});
        session.destroy();
        return JSON.stringify({ success: true, response });
      } catch (e) {
        return JSON.stringify({ success: false, error: e.message, stack: e.stack });
      }
    })()`);

    const parsed = JSON.parse(result);
    console.log(JSON.stringify(parsed, null, 2));
    ws.close();
  } catch (e) {
    console.error(`Error: ${e.message}`);
    process.exit(1);
  }
}

function cdpSend(ws, method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = Math.floor(Math.random() * 100000);
    const msg = JSON.stringify({ id, method, params });

    const handler = (event) => {
      const raw = typeof event.data === 'string' ? event.data : event.data?.toString();
      if (!raw) return;
      try {
        const response = JSON.parse(raw);
        if (response.id === id) {
          ws.removeEventListener('message', handler);
          resolve(response);
        }
      } catch { /* ignore partial messages */ }
    };

    ws.addEventListener('message', handler);
    ws.send(msg);
    setTimeout(() => { ws.removeEventListener('message', handler); reject(new Error('CDP timeout')); }, 30000);
  });
}

async function cdpEval(ws, expression) {
  const result = await cdpSend(ws, 'Runtime.evaluate', {
    expression,
    awaitPromise: true,
    returnByValue: false
  });
  if (result.result?.exceptionDetails) {
    throw new Error(result.result.exceptionDetails.text || 'CDP evaluation error');
  }
  // Handle the result which is a stringified JSON
  const objResult = result.result?.result;
  if (objResult?.type === 'string') {
    return objResult.value;
  }
  return objResult?.value ?? JSON.stringify(objResult);
}

main().catch(e => { console.error(`Fatal: ${e.message}`); process.exit(1); });
