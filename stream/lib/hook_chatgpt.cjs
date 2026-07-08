const WebSocket = require('ws');

async function main() {
    const resp = await fetch('http://localhost:9222/json');
    const tabs = await resp.json();
    
    // Find the ChatGPT tab
    const chatgptTab = tabs.find(t => t.url.includes('chatgpt.com/c/'));
    if (!chatgptTab) {
        console.log('ChatGPT tab not found');
        console.log('Available tabs:');
        tabs.filter(t => t.type === 'page').forEach(t => console.log('  ' + t.title + ' | ' + t.url));
        return;
    }
    
    console.log('Found ChatGPT tab:', chatgptTab.title);
    console.log('URL:', chatgptTab.url);
    
    const ws = new WebSocket(chatgptTab.webSocketDebuggerUrl);
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
    
    // Wait for page to be ready
    await new Promise(r => setTimeout(r, 2000));
    
    // Get page info
    const title = await send('Runtime.evaluate', { expression: 'document.title' });
    console.log('\nPage title:', title.result?.result?.value);
    
    const url = await send('Runtime.evaluate', { expression: 'window.location.href' });
    console.log('URL:', url.result?.result?.value);
    
    // Extract chat messages using different selectors
    console.log('\n=== Extracting ChatGPT Conversation ===');
    
    const messages = await send('Runtime.evaluate', {
        expression: `
            (() => {
                // Try different selectors for ChatGPT messages
                const selectors = [
                    '[data-message-author-role]',
                    '.markdown.prose',
                    '.flex.flex-col',
                    '[class*="message"]',
                    '[class*="turn"]'
                ];
                
                for (const sel of selectors) {
                    const elems = document.querySelectorAll(sel);
                    if (elems.length > 2) {
                        return JSON.stringify({
                            selector: sel,
                            count: elems.length,
                            messages: Array.from(elems).map((el, i) => ({
                                index: i,
                                role: el.getAttribute('data-message-author-role') || 
                                      (el.closest('[data-message-author-role]')?.getAttribute('data-message-author-role')) || 'unknown',
                                content: el.innerText?.substring(0, 1000) || ''
                            })).filter(m => m.content.length > 10)
                        });
                    }
                }
                
                // Fallback: get all visible text
                return JSON.stringify({
                    selector: 'body-fallback',
                    count: 1,
                    messages: [{ 
                        index: 0, 
                        role: 'page', 
                        content: document.body?.innerText?.substring(0, 3000) || '' 
                    }]
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
            console.log(m.content.substring(0, 300));
        });
    }
    
    // Check for ChatGPT Exporter extension
    console.log('\n=== Checking for ChatGPT Exporter Extension ===');
    
    const extCheck = await send('Runtime.evaluate', {
        expression: `
            (() => {
                const checks = {
                    // Check for extension injected elements
                    hasExportButton: !!document.querySelector('button[data-testid*="export"]'),
                    exportButtons: Array.from(document.querySelectorAll('button')).filter(b => {
                        const text = b.innerText?.toLowerCase() || '';
                        return text.includes('export') || text.includes('download');
                    }).map(b => b.innerText),
                    
                    // Check for extension in page context
                    hasExporterObj: typeof window.chatgptExporter !== 'undefined',
                    hasExportFn: typeof window.exportChatGPT !== 'undefined',
                    
                    // Check for extension popup/modal
                    hasExportModal: !!document.querySelector('[class*="export"]'),
                    
                    // Check for any data attributes
                    dataAttrs: Array.from(document.querySelectorAll('[data-export], [data-action*="export"]')).length
                };
                return JSON.stringify(checks, null, 2);
            })()
        `
    });
    
    console.log('Extension checks:', extCheck.result?.result?.value);
    
    // Try to trigger export via extension API
    console.log('\n=== Attempting to Trigger Export ===');
    
    const triggerExport = await send('Runtime.evaluate', {
        expression: `
            (() => {
                // Try to find and click export button
                const exportBtns = Array.from(document.querySelectorAll('button')).filter(b => {
                    const text = b.innerText?.toLowerCase() || '';
                    return text.includes('export');
                });
                
                if (exportBtns.length > 0) {
                    exportBtns[0].click();
                    return 'Clicked export button: ' + exportBtns[0].innerText;
                }
                
                // Try to find share button (often near export)
                const shareBtns = Array.from(document.querySelectorAll('button')).filter(b => {
                    const text = b.innerText?.toLowerCase() || '';
                    return text.includes('share');
                });
                
                if (shareBtns.length > 0) {
                    return 'Found share button: ' + shareBtns[0].innerText + ' (export might be nearby)';
                }
                
                return 'No export/share buttons found';
            })()
        `
    });
    
    console.log('Export trigger result:', triggerExport.result?.result?.value);
    
    // Get all button text for debugging
    const allButtons = await send('Runtime.evaluate', {
        expression: `
            Array.from(document.querySelectorAll('button'))
                .map(b => b.innerText?.trim())
                .filter(t => t && t.length > 0 && t.length < 50)
                .join(', ')
        `
    });
    console.log('\nAll buttons on page:', allButtons.result?.result?.value);
    
    ws.close();
    console.log('\nDone');
}

main().catch(console.error);
