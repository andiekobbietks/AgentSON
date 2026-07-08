const WebSocket = require('ws');
const fs = require('fs');

async function main() {
    const resp = await fetch('http://localhost:9222/json');
    const tabs = await resp.json();
    
    // Find a ChatGPT tab to use as base
    const chatgptTab = tabs.find(t => t.url.includes('chatgpt.com'));
    if (!chatgptTab) {
        console.log('No ChatGPT tab found');
        return;
    }
    
    console.log('Using tab:', chatgptTab.title);
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
    
    // Navigate to ChatGPT history
    console.log('Navigating to ChatGPT history...');
    await send('Page.enable');
    await send('Page.navigate', { url: 'https://chatgpt.com/' });
    await new Promise(r => setTimeout(r, 5000));
    
    // Extract all conversation links from sidebar
    console.log('Extracting conversation links...');
    
    const links = await send('Runtime.evaluate', {
        expression: `
            (() => {
                // Find all conversation links in sidebar
                const links = Array.from(document.querySelectorAll('a[href*="/c/"]'));
                return JSON.stringify(links.map(a => ({
                    title: a.innerText?.trim() || 'Untitled',
                    url: a.href,
                    id: a.href.match(/\\/c\\/([a-f0-9-]+)/)?.[1] || 'unknown'
                })).filter(l => l.id !== 'unknown'));
            })()
        `
    });
    
    const conversations = JSON.parse(links.result?.result?.value || '[]');
    console.log('Found', conversations.length, 'conversations');
    
    // Export each conversation
    const allExports = [];
    
    for (const conv of conversations.slice(0, 10)) { // Limit to 10 for testing
        console.log('\nExporting:', conv.title);
        
        try {
            // Navigate to conversation
            await send('Page.navigate', { url: conv.url });
            await new Promise(r => setTimeout(r, 3000));
            
            // Extract messages
            const messages = await send('Runtime.evaluate', {
                expression: `
                    (() => {
                        const msgs = [];
                        document.querySelectorAll('[data-message-author-role]').forEach((el, i) => {
                            const role = el.getAttribute('data-message-author-role');
                            const content = el.innerText;
                            if (content && content.trim().length > 0) {
                                msgs.push({ role, content: content.trim() });
                            }
                        });
                        return JSON.stringify(msgs);
                    })()
                `
            });
            
            const msgs = JSON.parse(messages.result?.result?.value || '[]');
            
            allExports.push({
                source: 'chatgpt',
                title: conv.title,
                sessionId: conv.id,
                url: conv.url,
                extractedAt: new Date().toISOString(),
                messages: msgs
            });
            
            console.log('  Messages:', msgs.length);
        } catch (e) {
            console.log('  Error:', e.message);
        }
    }
    
    // Save all exports
    const outputPath = 'C:\\Users\\LLM-Test\\Documents\\agentsong\\examples\\chatgpt_full_export.json';
    fs.writeFileSync(outputPath, JSON.stringify(allExports, null, 2));
    
    console.log('\n=== Summary ===');
    console.log('Total conversations exported:', allExports.length);
    console.log('Total messages:', allExports.reduce((sum, e) => sum + e.messages.length, 0));
    console.log('Saved to:', outputPath);
    
    ws.close();
}

main().catch(console.error);
