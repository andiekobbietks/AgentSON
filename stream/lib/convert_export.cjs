const fs = require('fs');
const { appendFileSync, existsSync, readFileSync } = require('fs');
const { resolve, basename } = require('path');

// AgentSON JSON-to-Stream Converter
// Converts exported ChatGPT JSON to .agentson JSONL format
// Usage: node convert_export.cjs <input.json> [output.agentson]

const inputFile = process.argv[2];
const outputFile = process.argv[3];

if (!inputFile) {
    console.error('Usage: node convert_export.cjs <input.json> [output.agentson]');
    console.error('  Converts exported ChatGPT JSON to .agentson JSONL stream');
    process.exit(1);
}

// Read input JSON
let input;
try {
    input = JSON.parse(readFileSync(inputFile, 'utf-8'));
} catch (e) {
    console.error(`Error reading input file: ${e.message}`);
    process.exit(1);
}

// Determine output file
const out = outputFile || inputFile.replace(/\.json$/, '.agentson');

// Emit function
function emit(entry) {
    entry.timestamp = entry.timestamp || Date.now();
    appendFileSync(out, JSON.stringify(entry) + '\n', 'utf-8');
    const ts = new Date(entry.timestamp).toLocaleTimeString();
    console.log(`  [${ts}] ${entry.type}`);
}

// Initialize output stream
if (existsSync(out)) {
    fs.unlinkSync(out);
}

console.log('=== AgentSON Export Converter ===');
console.log(`Input: ${inputFile}`);
console.log(`Output: ${out}`);
console.log('');

// Generate stream ID from chatGroupId or URL
let streamId = input.chatGroupId;
if (!streamId && input.url) {
    const match = input.url.match(/\/c\/([a-f0-9-]+)/);
    if (match) streamId = match[1];
}
if (!streamId) streamId = basename(inputFile, '.json');

// Stream meta
emit({
    type: 'stream-meta',
    stream_id: `chatgpt-export-${streamId}`,
    timestamp: Date.now(),
    agents: [
        { id: 'chatgpt', capabilities: ['conversation'] },
        { id: 'user', capabilities: ['query'] }
    ],
    mode: 'jsonl',
    source: {
        platform: 'chatgpt',
        sessionId: streamId,
        title: input.title || 'ChatGPT Export',
        url: input.url || `https://chatgpt.com/c/${streamId}`
    }
});

// Convert messages
if (input.messages && Array.isArray(input.messages)) {
    console.log(`Converting ${input.messages.length} messages...`);
    
    input.messages.forEach((msg, i) => {
        // Extract text content from contents array
        let text = '';
        if (msg.contents && Array.isArray(msg.contents)) {
            text = msg.contents
                .filter(c => c.type === 'text')
                .map(c => c.content)
                .join('\n\n');
        } else if (msg.content) {
            // Fallback to content string
            text = msg.content;
        }
        
        if (!text || text.trim().length === 0) return;
        
        if (msg.role === 'user') {
            emit({
                type: 'user-query',
                agent: 'user',
                text: text.trim(),
                source: 'chatgpt',
                chatgptMessageId: msg.id || i,
                timestamp: msg.created_at ? new Date(msg.created_at).getTime() : Date.now()
            });
        } else if (msg.role === 'assistant') {
            emit({
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
}

// Completion marker
emit({
    type: 'side-effect',
    agent: 'chatgpt-adapter',
    action: 'chat-export-complete',
    result: {
        sessionId: streamId,
        title: input.title || 'ChatGPT Export',
        messageCount: input.messages?.length || 0,
        exportedAt: new Date().toISOString()
    }
});

console.log('\n=== Conversion Complete ===');
console.log(`Messages: ${input.messages?.length || 0}`);
console.log(`Output: ${out}`);
