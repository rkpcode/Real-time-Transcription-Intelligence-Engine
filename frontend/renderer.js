/**
 * Renderer Process
 * Handles WebSocket connection and UI updates
 */

const { ipcRenderer } = require('electron');

// WebSocket connection
let ws = null;
let reconnectInterval = null;

// DOM elements
const transcriptContainer = document.getElementById('transcript-container');
const responseContainer = document.getElementById('response-container');
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const latencyIndicator = document.getElementById('latency-value');

// Connect to WebSocket server
function connectWebSocket() {
    const wsUrl = 'ws://localhost:8765';

    try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('✓ Connected to backend');
            updateStatus('connected', 'Connected');

            // Clear reconnect interval if exists
            if (reconnectInterval) {
                clearInterval(reconnectInterval);
                reconnectInterval = null;
            }
        };

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                handleMessage(message);
            } catch (error) {
                console.error('Error parsing message:', error);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateStatus('error', 'Connection Error');
        };

        ws.onclose = () => {
            console.log('WebSocket closed');
            updateStatus('disconnected', 'Disconnected');

            // Attempt to reconnect
            if (!reconnectInterval) {
                reconnectInterval = setInterval(() => {
                    console.log('Attempting to reconnect...');
                    connectWebSocket();
                }, 3000);
            }
        };

    } catch (error) {
        console.error('Failed to connect:', error);
        updateStatus('error', 'Failed to Connect');
    }
}

// Handle incoming messages
function handleMessage(message) {
    const { type, data, timestamp } = message;

    switch (type) {
        case 'transcript':
            handleTranscript(data);
            break;

        case 'response':
            handleResponse(data);
            break;

        case 'status':
            handleStatus(data);
            break;

        default:
            console.warn('Unknown message type:', type);
    }
}

// Handle transcript updates
function handleTranscript(data) {
    const { text, is_final, confidence } = data;

    if (!text || !text.trim()) return;

    // Find or create interim transcript element
    let transcriptEl = document.getElementById('interim-transcript');

    if (is_final) {
        // Create new final transcript element
        if (transcriptEl) {
            transcriptEl.remove();
        }

        const finalEl = document.createElement('div');
        finalEl.className = 'transcript-item final';
        finalEl.innerHTML = `
      <div class="transcript-text">${escapeHtml(text)}</div>
      <div class="transcript-meta">
        <span class="confidence">Confidence: ${(confidence * 100).toFixed(0)}%</span>
        <span class="timestamp">${formatTime(new Date())}</span>
      </div>
    `;

        transcriptContainer.appendChild(finalEl);

        // Scroll to bottom
        transcriptContainer.scrollTop = transcriptContainer.scrollHeight;

        // Limit number of transcripts shown
        const maxTranscripts = 20;
        while (transcriptContainer.children.length > maxTranscripts) {
            transcriptContainer.removeChild(transcriptContainer.firstChild);
        }

    } else {
        // Update interim transcript
        if (!transcriptEl) {
            transcriptEl = document.createElement('div');
            transcriptEl.id = 'interim-transcript';
            transcriptEl.className = 'transcript-item interim';
            transcriptContainer.appendChild(transcriptEl);
        }

        transcriptEl.innerHTML = `
      <div class="transcript-text">${escapeHtml(text)}</div>
      <div class="transcript-meta">
        <span class="interim-label">Interim...</span>
      </div>
    `;

        // Scroll to bottom
        transcriptContainer.scrollTop = transcriptContainer.scrollHeight;
    }
}

// Handle LLM responses
function handleResponse(data) {
    const { text, context, latency_ms } = data;

    // Create response card
    const responseEl = document.createElement('div');
    responseEl.className = 'response-card';
    responseEl.innerHTML = `
    <div class="response-header">
      <span class="response-icon">🤖</span>
      <span class="response-time">${formatTime(new Date())}</span>
    </div>
    <div class="response-text">${escapeHtml(text)}</div>
    ${context ? `<div class="response-context">Context: ${escapeHtml(context)}</div>` : ''}
    <div class="response-footer">
      <span class="latency ${getLatencyClass(latency_ms)}">
        ⚡ ${latency_ms}ms
      </span>
    </div>
  `;

    // Add with animation
    responseEl.style.opacity = '0';
    responseContainer.appendChild(responseEl);

    setTimeout(() => {
        responseEl.style.opacity = '1';
    }, 10);

    // Scroll to bottom
    responseContainer.scrollTop = responseContainer.scrollHeight;

    // Update latency indicator
    updateLatency(latency_ms);

    // Limit number of responses shown
    const maxResponses = 10;
    while (responseContainer.children.length > maxResponses) {
        responseContainer.removeChild(responseContainer.firstChild);
    }
}

// Handle status updates
function handleStatus(data) {
    const { status, message } = data;
    updateStatus(status, message || status);
}

// Update status indicator
function updateStatus(status, text) {
    statusIndicator.className = `status-dot ${status}`;
    statusText.textContent = text;
}

// Update latency indicator
function updateLatency(latencyMs) {
    latencyIndicator.textContent = `${latencyMs}ms`;
    latencyIndicator.className = `latency-value ${getLatencyClass(latencyMs)}`;
}

// Get latency class for color coding
function getLatencyClass(latencyMs) {
    if (latencyMs < 1000) return 'good';
    if (latencyMs < 2000) return 'ok';
    return 'slow';
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatTime(date) {
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    });
}

// Window controls
document.getElementById('minimize-btn').addEventListener('click', () => {
    ipcRenderer.send('minimize-window');
});

document.getElementById('close-btn').addEventListener('click', () => {
    ipcRenderer.send('close-window');
});

// Settings button (placeholder)
document.getElementById('settings-btn').addEventListener('click', () => {
    alert('Settings panel coming soon!');
});

// Clear button
document.getElementById('clear-btn').addEventListener('click', () => {
    transcriptContainer.innerHTML = '';
    responseContainer.innerHTML = '';

    // Send clear context message to backend
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'clear_context' }));
    }
});

// Make window draggable
const header = document.getElementById('header');
let isDragging = false;
let dragOffset = { x: 0, y: 0 };

header.addEventListener('mousedown', (e) => {
    if (e.target.closest('.window-controls') || e.target.closest('.header-actions')) {
        return;
    }
    isDragging = true;
    dragOffset.x = e.clientX;
    dragOffset.y = e.clientY;
});

document.addEventListener('mousemove', (e) => {
    if (isDragging) {
        const deltaX = e.screenX - dragOffset.x;
        const deltaY = e.screenY - dragOffset.y;

        // This would need to be handled by main process
        // For now, we'll use a simpler approach
    }
});

document.addEventListener('mouseup', () => {
    isDragging = false;
});

// Initialize
connectWebSocket();

// Heartbeat to keep connection alive
setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
    }
}, 30000);  // Every 30 seconds
