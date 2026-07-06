const fs = require('fs');
const { appendFileSync, existsSync, readFileSync } = require('fs');
const { resolve, basename } = require('path');

// AgentSON Export CLI
// Usage: 
//   node agentson_export.cjs convert <input.json> [output.agentson]
//   node agentson_export.cjs fetch <session-id> [output.agentson]
//
// Modes:
//   convert - Convert existing JSON export to .agentson format
//   fetch   - Fetch from ChatGPT via extension (requires Chrome with extension)

const mode = process.argv[2];
const input = process.argv[3];
const output = process.argv[4];

if (!mode || !input) {
    console.error('AgentSON Export CLI');
    console.error('');
    console.error('Usage:');
    console.error('  node agentson_export.cjs convert <input.json> [output.agentson]');
    console.error('  node agentson_export.cjs fetch <session-id> [output.agentson]');
    console.error('');
    console.error('Modes:');
    console.error('  convert   Convert existing JSON export to .agentson format');
    console.error('  fetch     Fetch conversation from ChatGPT via extension');
    process.exit(1);
}

// Emit function
function emit(out, entry) {
    entry.timestamp = entry.timestamp || Date.now();
    appendFileSync(out, JSON.stringify(entry) + '\n', 'utf-8');
    const ts = new Date(entry.timestamp).toLocaleTimeString();
    console.log(`  [${ts}] ${entry.type}`);
}

// Convert mode
async function convert() {
    const inputFile = input;
    const outputFile = output || inputFile.replace(/\.json$/, '.agentson');
    
    let inputData;
    try {
        inputData = JSON.parse(readFileSync(inputFile, 'utf-8'));
    } catch (e) {
        console.error(`Error reading input file: ${e.message}`);
        process.exit(1);
    }
    
    // Handle array of sessions or single session
    const sessions = Array.isArray(inputData) ? inputData : [inputData];
    
    console.log('=== AgentSON Export Converter ===');
    console.log(`Input: ${inputFile}`);
    console.log(`Output: ${outputFile}`);
    console.log(`Sessions: ${sessions.length}`);
    console.log('');
    
    // Initialize output
    if (existsSync(outputFile)) {
        fs.unlinkSync(outputFile);
    }
    
    for (const session of sessions) {
        // Extract session ID
        let sessionId = session.sessionId || session.chatGroupId;
        if (!sessionId && session.url) {
            const match = session.url.match(/\/c\/([a-f0-9-]+)/);
            if (match) sessionId = match[1];
        }
        if (!sessionId) sessionId = basename(inputFile, '.json');
        
        // Stream meta
        emit(outputFile, {
            type: 'stream-meta',
            stream_id: `chatgpt-export-${sessionId}`,
            agents: [
                { id: 'chatgpt', capabilities: ['conversation'] },
                { id: 'user', capabilities: ['query'] }
            ],
            mode: 'jsonl',
            source: {
                platform: 'chatgpt',
                sessionId: sessionId,
                title: session.title || 'ChatGPT Export',
                url: session.url || `https://chatgpt.com/c/${sessionId}`
            }
        });
        
        // Convert messages
        if (session.messages && Array.isArray(session.messages)) {
            console.log(`Converting session: ${session.title || sessionId} (${session.messages.length} messages)`);
            
            session.messages.forEach((msg, i) => {
                // Extract text content
                let text = '';
                if (msg.contents && Array.isArray(msg.contents)) {
                    text = msg.contents
                        .filter(c => c.type === 'text')
                        .map(c => c.content)
                        .join('\n\n');
                } else if (msg.content) {
                    text = msg.content;
                }
                
                if (!text || text.trim().length === 0) return;
                
                if (msg.role === 'user') {
                    emit(outputFile, {
                        type: 'user-query',
                        agent: 'user',
                        text: text.trim(),
                        source: 'chatgpt',
                        chatgptMessageId: msg.id || i,
                        timestamp: msg.created_at ? new Date(msg.created_at).getTime() : Date.now()
                    });
                } else if (msg.role === 'assistant') {
                    emit(outputFile, {
                        type: 'answer',
                        agent: 'chatgpt',
                        text: text.trim(),
                        model: msg.modelId || 'unknown',
                        source: 'chatgpt',
                        chatgptMessageId: msg.id || i,
                        timestamp: msg.created_at ? new Date(msg.created_at).getTime() : Date.now()
                    });
                }
            });
            
            // Completion marker
            emit(outputFile, {
                type: 'side-effect',
                agent: 'chatgpt-adapter',
                action: 'chat-export-complete',
                result: {
                    sessionId: sessionId,
                    title: session.title || 'ChatGPT Export',
                    messageCount: session.messages.length,
                    exportedAt: new Date().toISOString()
                }
            });
        }
    }
    
    console.log('\n=== Conversion Complete ===');
    console.log(`Output: ${outputFile}`);
}

// Fetch mode
async function fetch() {
    const sessionId = input;
    const outputFile = output || `chatgpt_${sessionId}.agentson`;
    
    console.log('=== AgentSON ChatGPT Fetcher ===');
    console.log(`Session ID: ${sessionId}`);
    console.log(`Output: ${outputFile}`);
    console.log('');
    
    // Connect to Chrome CDP
    const resp = await fetch('http://localhost:9222/json');
    const tabs = await resp.json();
    
    // Find a ChatGPT tab or any page tab
    let tab = tabs.find(t => t.url.includes('chatgpt.com/c/'));
    if (!tab) {
        tab = tabs.find(t => t.type === 'page' && !t.url.startsWith('chrome'));
    }
    
    if (!tab) {
        console.error('No suitable Chrome tab found');
        process.exit(1);
    }
    
    console.log('Connecting to Chrome...');
    const WebSocket = require('ws');
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
    
    // Navigate to session
    const url = `https://chatgpt.com/c/${sessionId}`;
    console.log('Navigating to ChatGPT session...');
    await send('Page.enable');
    await send('Page.navigate', { url });
    await new Promise(r => setTimeout(r, 5000));
    
    // Verify we're on the right page
    const titleResult = await send('Runtime.evaluate', { expression: 'document.title' });
    const title = titleResult.result?.result?.value || 'Unknown';
    console.log(`Page title: ${title}`);
    
    // Initialize output
    if (existsSync(outputFile)) {
        fs.unlinkSync(outputFile);
    }
    
    // Stream meta
    emit(outputFile, {
        type: 'stream-meta',
        stream_id: `chatgpt-export-${sessionId}`,
        agents: [
            { id: 'chatgpt', capabilities: ['conversation'] },
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
    
    // Convert to AgentSON events
    console.log('Converting to AgentSON format...');
    
    for (const msg of data.messages) {
        if (msg.role === 'user') {
            emit(outputFile, {
                type: 'user-query',
                agent: 'user',
                text: msg.content,
                source: 'chatgpt',
                chatgptMessageId: msg.index
            });
        } else if (msg.role === 'assistant') {
            emit(outputFile, {
                type: 'answer',
                agent: 'chatgpt',
                text: msg.content,
                source: 'chatgpt',
                chatgptMessageId: msg.index
            });
        }
    }
    
    // Completion marker
    emit(outputFile, {
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
    
    console.log('\n=== Fetch Complete ===');
    console.log(`Session: ${sessionId}`);
    console.log(`Messages: ${data.messageCount}`);
    console.log(`Output: ${outputFile}`);
    
    ws.close();
}

// Run
if (mode === 'convert') {
    convert().catch(e => {
        console.error('Error:', e.message);
        process.exit(1);
    });
} else if (mode === 'fetch') {
    fetch().catch(e => {
        console.error('Error:', e.message);
        process.exit(1);
    });
} else {
    console.error(`Unknown mode: ${mode}`);
    process.exit(1);
}
