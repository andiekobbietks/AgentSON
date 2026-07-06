const WebSocket = require('ws');

async function main() {
    const resp = await fetch('http://localhost:9222/json');
    const tabs = await resp.json();
    
    console.log('Available tabs:');
    tabs.forEach(t => console.log('  ' + t.title + ' | ' + t.url));
    
    // Find a page tab (not extension or chrome://)
    const tab = tabs.find(t => t.type === 'page' && !t.url.startsWith('chrome'));
    
    if (!tab) {
        console.log('No suitable tab found, using first page tab');
        const pageTab = tabs.find(t => t.type === 'page');
        if (!pageTab) {
            console.log('No page tabs available');
            return;
        }
        return connectAndExtract(pageTab);
    }
    
    return connectAndExtract(tab);
}

async function connectAndExtract(tab) {
    console.log('\nConnecting to:', tab.title, tab.url);
    const ws = new WebSocket(tab.webSocketDebuggerUrl);
    await new Promise(r => ws.on('open', r));
    
    let msgId = 0;
    function send(method, params = {}) {
        return new Promise((res) => {
            const id = ++msgId;
            const handler = (data) => {
                const msg = JSON.parse(data.toString());
                if (msg.id === id) {
                    ws.off('message', handler);
                    res(msg);
                }
            };
            ws.on('message', handler);
            ws.send(JSON.stringify({ id, method, params }));
        });
    }
    
    // If not on ChatGPT, navigate there
    if (!tab.url.includes('chatgpt.com')) {
        console.log('Navigating to ChatGPT...');
        await send('Page.enable');
        await send('Page.navigate', { url: 'https://chatgpt.com' });
        await new Promise(r => setTimeout(r, 6000));
    }
    
    // Get page info
    const title = await send('Runtime.evaluate', { expression: 'document.title' });
    console.log('Page title:', title.result?.result?.value);
    
    const url = await send('Runtime.evaluate', { expression: 'window.location.href' });
    console.log('URL:', url.result?.result?.value);
    
    // Extract all text content from chat messages
    console.log('\nExtracting chat messages...');
    const messages = await send('Runtime.evaluate', {
        expression: `
            (() => {
                // Try different selectors for ChatGPT messages
                const selectors = [
                    '[data-message-author-role]',
                    '.markdown',
                    '.prose',
                    '[class*="message"]',
                    '[class*="turn"]'
                ];
                
                for (const sel of selectors) {
                    const elems = document.querySelectorAll(sel);
                    if (elems.length > 0) {
                        return JSON.stringify({
                            selector: sel,
                            count: elems.length,
                            messages: Array.from(elems).map((el, i) => ({
                                index: i,
                                role: el.getAttribute('data-message-author-role') || 'unknown',
                                content: el.innerText?.substring(0, 500) || ''
                            }))
                        });
                    }
                }
                
                // Fallback: get all text
                return JSON.stringify({
                    selector: 'body',
                    count: 1,
                    messages: [{ index: 0, role: 'page', content: document.body?.innerText?.substring(0, 2000) || '' }]
                });
            })()
        `
    });
    
    const result = JSON.parse(messages.result?.result?.value || '{}');
    console.log('Selector used:', result.selector);
    console.log('Messages found:', result.count);
    
    if (result.messages) {
        result.messages.forEach(m => {
            console.log(`\n--- Message ${m.index} (${m.role}) ---`);
            console.log(m.content.substring(0, 200));
        });
    }
    
    // Check for export extension
    console.log('\nChecking for ChatGPT Exporter extension...');
    const extCheck = await send('Runtime.evaluate', {
        expression: `
            (() => {
                // Check for common extension markers
                const checks = {
                    hasExporter: typeof window.chatgptExporter !== 'undefined',
                    hasExportBtn: !!document.querySelector('[data-export]'),
                    exportBtns: Array.from(document.querySelectorAll('button')).filter(b => 
                        b.innerText?.toLowerCase().includes('export')
                    ).map(b => b.innerText)
                };
                return JSON.stringify(checks);
            })()
        `
    });
    
    const ext = JSON.parse(extCheck.result?.result?.value || '{}');
    console.log('Extension checks:', JSON.stringify(ext, null, 2));
    
    ws.close();
    console.log('\nDone');
}

main().catch(console.error);
