// DOM elements
const connectButton = document.getElementById('connectButton');
const serverUrlInput = document.getElementById('serverUrl');
const connectionStatus = document.getElementById('connectionStatus');
const messageInput = document.getElementById('messageInput');
const sendTextButton = document.getElementById('sendTextButton');
const recordButton = document.getElementById('recordButton');
const stopButton = document.getElementById('stopButton');
// Session conversation
const conversationDiv = document.getElementById('conversation');
const logContainer = document.getElementById('logContainer');
let visualizerCanvas = document.getElementById('audioVisualizer');

// Update OTA connection status style
export function otaStatusStyle(flan) {
    if (flan) {
        document.getElementById('otaStatus').textContent = 'OTA Connected';
        document.getElementById('otaStatus').style.color = 'green';
    } else {
        document.getElementById('otaStatus').textContent = 'OTA Disconnected';
        document.getElementById('otaStatus').style.color = 'red';
    }
}

// Get log container
export function getLogContainer(flan) {
    return logContainer;
}

// Update Opus library status display
export function updateScriptStatus(message, type) {
    const statusElement = document.getElementById('scriptStatus');
    if (statusElement) {
        statusElement.textContent = message;
        statusElement.className = `script-status ${type}`;
        statusElement.style.display = 'block';
        statusElement.style.width = 'auto';
    }
}

// Add message to conversation
export function addMessage(text, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'server'}`;
    messageDiv.textContent = text;
    conversationDiv.appendChild(messageDiv);
    conversationDiv.scrollTop = conversationDiv.scrollHeight;
}

