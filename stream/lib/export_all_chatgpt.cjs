const WebSocket = require('ws');
const fs = require('fs');

async function main() {
    const resp = await fetch('http://localhost:9222/json');
    const tabs = await resp.json();
    
    // Find all ChatGPT tabs
    const chatgptTabs = tabs.filter(t => t.url.includes('chatgpt.com/c/'));
    console.log('Found', chatgptTabs.length, 'ChatGPT tabs');
    
    const allExports = [];
    
    for (const tab of chatgptTabs) {
        console.log('\n=== Exporting:', tab.title, '===');
        console.log('URL:', tab.url);
        
        try {
            const conversation = await exportConversation(tab);
            if (conversation) {
                allExports.push(conversation);
                console.log('Messages:', conversation.messages.length);
            }
        } catch (e) {
            console.log('Error:', e.message);
        }
    }
    
    // Save all exports
    const outputPath = 'C:\\Users\\LLM-Test\\Documents\\agentsong\\examples\\chatgpt_all_sessions.json';
    fs.writeFileSync(outputPath, JSON.stringify(allExports, null, 2));
    console.log('\n=== Summary ===');
    console.log('Total sessions exported:', allExports.length);
    console.log('Saved to:', outputPath);
}

async function exportConversation(tab) {
    const ws = new WebSocket(tab.webSocketDebuggerUrl);
    await new Promise(r => ws.on('open', r));
    
    let msgId = 0;
    function send(method, params = {}) {
        return new Promise((res, rej) => {
            const id = ++msgId;
            const timeout = setTimeout(() => rej(new Error('Timeout')), 10000);
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
    
    // Extract conversation
    const result = await send('Runtime.evaluate', {
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
                    messages: messages
                });
            })()
        `
    });
    
    const data = JSON.parse(result.result?.result?.value || '{}');
    
    ws.close();
    
    return {
        source: 'chatgpt',
        title: data.title,
        url: data.url,
        sessionId: tab.url.match(/chatgpt\.com\/c\/([a-f0-9-]+)/)?.[1] || 'unknown',
        extractedAt: new Date().toISOString(),
        messages: data.messages
    };
}

main().catch(console.error);
