const WebSocket = require('ws');
const fs = require('fs');

async function main() {
    const resp = await fetch('http://localhost:9222/json');
    const tabs = await resp.json();
    
    // Find ChatGPT tab
    const chatgptTab = tabs.find(t => t.url.includes('chatgpt.com/c/'));
    if (!chatgptTab) {
        console.log('No ChatGPT tab found');
        return;
    }
    
    console.log('Connecting to:', chatgptTab.title);
    const ws = new WebSocket(chatgptTab.webSocketDebuggerUrl);
    await new Promise(r => ws.on('open', r));
    
    let msgId = 0;
    function send(method, params = {}) {
        return new Promise((res) => {
            const id = ++msgId;
            ws.on('message', function handler(data) {
                const msg = JSON.parse(data.toString());
                if (msg.id === id) {
                    ws.off('message', handler);
                    res(msg);
                }
            });
            ws.send(JSON.stringify({ id, method, params }));
        });
    }
    
    // Extract conversation using the extension's content script
    console.log('\nExtracting conversation...');
    
    const extractResult = await send('Runtime.evaluate', {
        expression: `
            (() => {
                // Try to find the extension's content script
                if (typeof window.saveai !== 'undefined') {
                    return JSON.stringify({ extension: 'saveai', available: true });
                }
                if (typeof window.content !== 'undefined') {
                    return JSON.stringify({ extension: 'content', available: true });
                }
                
                // Extract messages manually
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
                
                // Also try to get conversation title
                const title = document.title;
                const url = window.location.href;
                
                return JSON.stringify({
                    title: title,
                    url: url,
                    messageCount: messages.length,
                    messages: messages
                });
            })()
        `
    });
    
    const result = JSON.parse(extractResult.result?.result?.value || '{}');
    
    if (result.extension) {
        console.log('Extension found:', result.extension);
    } else {
        console.log('Title:', result.title);
        console.log('URL:', result.url);
        console.log('Messages found:', result.messageCount);
        
        // Save to file
        const output = {
            source: 'chatgpt',
            title: result.title,
            url: result.url,
            extractedAt: new Date().toISOString(),
            messages: result.messages
        };
        
        const outputPath = 'C:\\Users\\LLM-Test\\Documents\\agentsong\\examples\\chatgpt_export.json';
        fs.writeFileSync(outputPath, JSON.stringify(output, null, 2));
        console.log('\nSaved to:', outputPath);
        
        // Print first few messages
        if (result.messages) {
            console.log('\n=== First 3 messages ===');
            result.messages.slice(0, 3).forEach(m => {
                console.log(`\n[${m.role}]:`);
                console.log(m.content.substring(0, 200));
            });
        }
    }
    
    ws.close();
}

main().catch(console.error);
