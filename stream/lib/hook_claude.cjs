const WebSocket = require('ws');

async function main() {
    const resp = await fetch('http://localhost:9222/json');
    const tabs = await resp.json();
    
    // Find Claude tabs
    const claudeTabs = tabs.filter(t => t.url.includes('claude.ai/chat/'));
    console.log('Found', claudeTabs.length, 'Claude tabs');
    
    for (const tab of claudeTabs) {
        console.log('\n=== Extracting:', tab.title, '===');
        console.log('URL:', tab.url);
        
        try {
            await extractClaudeConversation(tab);
        } catch (e) {
            console.log('Error extracting:', e.message);
        }
    }
}

async function extractClaudeConversation(tab) {
    const ws = new WebSocket(tab.webSocketDebuggerUrl);
    await new Promise(r => ws.on('open', r));
    
    let msgId = 0;
    function send(method, params = {}) {
        return new Promise((res, rej) => {
            const id = ++msgId;
            const timeout = setTimeout(() => rej(new Error('Timeout')), 10000);
            const handler = (data) => {
                const msg = JSON.parse(data.toString());
                if (msg.id === id) {
                    clearTimeout(timeout);
                    ws.off('message', handler);
                    res(msg);
                }
            };
            ws.on('message', handler);
            ws.send(JSON.stringify({ id, method, params }));
        });
    }
    
    // Wait for page
    await new Promise(r => setTimeout(r, 2000));
    
    // Extract messages
    const messages = await send('Runtime.evaluate', {
        expression: `
            (() => {
                // Claude uses different selectors
                const selectors = [
                    '[data-testid*="message"]',
                    '.font-claude-message',
                    '[class*="message-content"]',
                    '.whitespace-pre-wrap',
                    '[class*="prose"]'
                ];
                
                for (const sel of selectors) {
                    const elems = document.querySelectorAll(sel);
                    if (elems.length > 2) {
                        return JSON.stringify({
                            selector: sel,
                            count: elems.length,
                            messages: Array.from(elems).map((el, i) => ({
                                index: i,
                                content: el.innerText?.substring(0, 1000) || ''
                            })).filter(m => m.content.length > 10)
                        });
                    }
                }
                
                // Fallback
                return JSON.stringify({
                    selector: 'body-fallback',
                    count: 1,
                    messages: [{ 
                        index: 0, 
                        content: document.body?.innerText?.substring(0, 3000) || '' 
                    }]
                });
            })()
        `
    });
    
    const result = JSON.parse(messages.result?.result?.value || '{}');
    console.log('Selector:', result.selector);
    console.log('Messages:', result.count);
    
    if (result.messages) {
        result.messages.slice(0, 5).forEach(m => {
            console.log(`\n--- Message ${m.index} ---`);
            console.log(m.content.substring(0, 200));
        });
    }
    
    ws.close();
}

main().catch(console.error);
