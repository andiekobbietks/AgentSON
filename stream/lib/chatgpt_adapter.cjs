const WebSocket = require('ws');
const fs = require('fs');
const { appendFileSync, existsSync } = require('fs');
const { resolve } = require('path');

// AgentSON ChatGPT Adapter
// Usage: node chatgpt_adapter.cjs <session-id-or-url> [output-stream]

const STREAM = process.argv[3] || resolve(process.cwd(), 'chatgpt_export.agentson');

function parseArgs() {
    const input = process.argv[2];
    if (!input) {
        console.error('Usage: node chatgpt_adapter.cjs <session-id-or-url> [output-stream]');
        console.error('  session-id-or-url: ChatGPT session ID or full URL');
        console.error('  output-stream: .agentson file to write (default: chatgpt_export.agentson)');
        process.exit(1);
    }
    
    // Extract session ID from URL or raw ID
    let sessionId = input;
    const urlMatch = input.match(/chatgpt\.com\/c\/([a-f0-9-]+)/);
    if (urlMatch) {
        sessionId = urlMatch[1];
    }
    
    return { sessionId, url: `https://chatgpt.com/c/${sessionId}` };
}

function emit(entry) {
    entry.agent = entry.agent || 'chatgpt-adapter';
    entry.timestamp = entry.timestamp || Date.now();
    appendFileSync(STREAM, JSON.stringify(entry) + '\n', 'utf-8');
    const ts = new Date(entry.timestamp).toLocaleTimeString();
    console.log(`  [${ts}] ${entry.type}`);
}

async function main() {
    const { sessionId, url } = parseArgs();
    
    console.log('=== AgentSON ChatGPT Adapter ===');
    console.log(`Session ID: ${sessionId}`);
    console.log(`URL: ${url}`);
    console.log(`Output: ${STREAM}`);
    console.log('');
    
    // Connect to Chrome CDP
    const resp = await fetch('http://localhost:9222/json');
    const tabs = await resp.json();
    
    // Find a page tab to use
    const tab = tabs.find(t => t.type === 'page' && !t.url.startsWith('chrome'));
    if (!tab) {
        console.error('No suitable Chrome tab found');
        process.exit(1);
    }
    
    console.log('Connecting to Chrome...');
    const ws = new WebSocket(tab.webSocketDebuggerUrl);
    await new Promise(r => ws.on('open', r));
    
    let msgId = 0;
    function send(method, params = {}) {
        return new Promise((res, rej) => {
            const id = ++msgId;
            const timeout = setTimeout(() => rej(new Error('CDP timeout')), 15000);
            ws.on('message', function handler(data) {
                const msg = JSON.parse(data.toString());
                if (msg.id === id) {
                    clearTimeout(timeout);
                    ws.off('message', handler);
                    res(msg);
                }
            });
            ws.send(JSON.stringify({ id, method, params }));
        });
    }
    
    // Navigate to the ChatGPT session
    console.log('Navigating to ChatGPT session...');
    await send('Page.enable');
    await send('Page.navigate', { url });
    await new Promise(r => setTimeout(r, 5000));
    
    // Verify we're on the right page
    const titleResult = await send('Runtime.evaluate', { expression: 'document.title' });
    const title = titleResult.result?.result?.value || 'Unknown';
    console.log(`Page title: ${title}`);
    
    // Extract conversation
    console.log('Extracting conversation...');
    
    const extractResult = await send('Runtime.evaluate', {
        expression: `
            (() => {
                const messages = [];
                const messageElements = document.querySelectorAll('[data-message-author-role]');
                
                messageElements.forEach((el, i) => {
                    const role = el.getAttribute('data-message-author-role');
                    const content = el.innerText;
                    if (content && content.trim().length > 0) {
                        messages.push({
                            index: i,
                            role: role || 'unknown',
                            content: content.trim()
                        });
                    }
                });
                
                return JSON.stringify({
                    title: document.title,
                    url: window.location.href,
                    messageCount: messages.length,
                    messages: messages
                });
            })()
        `
    });
    
    const data = JSON.parse(extractResult.result?.result?.value || '{}');
    
    if (data.messageCount === 0) {
        console.error('No messages found. Are you logged in to ChatGPT?');
        ws.close();
        process.exit(1);
    }
    
    console.log(`Found ${data.messageCount} messages`);
    
    // Initialize stream if needed
    if (!existsSync(STREAM)) {
        emit({
            type: 'stream-meta',
            stream_id: `chatgpt-export-${sessionId}`,
            timestamp: Date.now(),
            agents: [
                { id: 'chatgpt-adapter', capabilities: ['export'] },
                { id: 'user', capabilities: ['query'] }
            ],
            mode: 'jsonl',
            source: {
                platform: 'chatgpt',
                sessionId: sessionId,
                title: title,
                url: url
            }
        });
    }
    
    // Convert to AgentSON events
    console.log('Converting to AgentSON format...');
    
    for (const msg of data.messages) {
        if (msg.role === 'user') {
            emit({
                type: 'user-query',
                agent: 'user',
                text: msg.content,
                source: 'chatgpt',
                chatgptMessageId: msg.index
            });
        } else if (msg.role === 'assistant') {
            emit({
                type: 'answer',
                agent: 'chatgpt',
                text: msg.content,
                source: 'chatgpt',
                chatgptMessageId: msg.index
            });
        }
    }
    
    // Add completion marker
    emit({
        type: 'side-effect',
        agent: 'chatgpt-adapter',
        action: 'chat-export-complete',
        result: {
            sessionId: sessionId,
            title: title,
            messageCount: data.messageCount,
            exportedAt: new Date().toISOString()
        }
    });
    
    console.log(`\n=== Export Complete ===`);
    console.log(`Session: ${sessionId}`);
    console.log(`Messages: ${data.messageCount}`);
    console.log(`Output: ${STREAM}`);
    
    ws.close();
}

main().catch(e => {
    console.error('Error:', e.message);
    process.exit(1);
});
