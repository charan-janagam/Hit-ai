// ================= CONFIG =================
const API_BASE_URL = 'https://YOUR-BACKEND.onrender.com';
// =========================================

// Get DOM elements
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const messagesContainer = document.getElementById('messagesContainer');
const typingIndicator = document.getElementById('typingIndicator');

// 🔥 STREAMING Send message function (ChatGPT-style typing)
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // Add user message
    addMessage(message, 'user');
    messageInput.value = '';

    sendBtn.disabled = true;
    typingIndicator.classList.add('active');

    // Create bot message container
    const botMessageDiv = document.createElement('div');
    botMessageDiv.className = 'message bot-message';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content streaming-text';

    botMessageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(botMessageDiv);

    messagesContainer.scrollTo({
        top: messagesContainer.scrollHeight,
        behavior: 'smooth'
    });

    try {
        // ✅ FIXED: absolute backend URL
        const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        if (!response.ok) {
            throw new Error('Network error');
        }

        typingIndicator.classList.remove('active');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const payload = line.slice(6);
                    if (!payload) continue;

                    const data = JSON.parse(payload);

                    if (data.text) {
                        fullText += data.text;
                        contentDiv.innerHTML = formatMessage(fullText);
                        messagesContainer.scrollTo({
                            top: messagesContainer.scrollHeight,
                            behavior: 'smooth'
                        });
                    }

                    if (data.done) {
                        contentDiv.classList.remove('streaming-text');
                        if (data.jarvis_mode) {
                            botMessageDiv.classList.add('jarvis-mode');
                        }
                        console.log('Model:', data.model_used);
                    }

                    if (data.error) {
                        contentDiv.innerHTML = '⚠️ ' + data.error;
                        contentDiv.classList.add('error-message');
                        contentDiv.classList.remove('streaming-text');
                    }
                }
            }
        }

    } catch (err) {
        typingIndicator.classList.remove('active');
        contentDiv.innerHTML = '❌ Server connection failed';
        contentDiv.classList.add('error-message');
        contentDiv.classList.remove('streaming-text');
        console.error(err);
    }

    sendBtn.disabled = false;
    messageInput.focus();
}

// Add message
function addMessage(text, type) {
    const msg = document.createElement('div');
    msg.className = `message ${type}-message`;

    const content = document.createElement('div');
    content.className = 'message-content';
    content.innerHTML = formatMessage(text);

    msg.appendChild(content);
    messagesContainer.appendChild(msg);

    messagesContainer.scrollTo({
        top: messagesContainer.scrollHeight,
        behavior: 'smooth'
    });
}

// Format text
function formatMessage(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
}

// Quick prompts
function sendPrompt(promptText) {
    messageInput.value = promptText;
    sendMessage();
}

// Enter key handler
messageInput.addEventListener('keypress', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Auto focus
window.addEventListener('load', () => {
    messageInput.focus();
});
