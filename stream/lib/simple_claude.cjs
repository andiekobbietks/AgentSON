const WebSocket = require('ws');

async function main() {
    const resp = await fetch('http://localhost:9222/json');
    const tabs = await resp.json();
    
    const claudeTab = tabs.find(t => t.url.includes('claude.ai/chat/'));
    if (!claudeTab) {
        console.log('No Claude tab found');
        return;
    }
    
    console.log('Connecting to:', claudeTab.title);
    const ws = new WebSocket(claudeTab.webSocketDebuggerUrl);
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
    
    // Get page content
    const content = await send('Runtime.evaluate', {
        expression: 'document.body.innerText.substring(0, 5000)'
    });
    
    console.log('Page content:');
    console.log(content.result?.result?.value);
    
    ws.close();
}

main().catch(console.error);
