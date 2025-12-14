// Get DOM elements
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const messagesContainer = document.getElementById('messagesContainer');
const typingIndicator = document.getElementById('typingIndicator');

// 🔥 STREAMING Send message function (ChatGPT-style typing)
async function sendMessage() {
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    messageInput.value = '';
    
    // Disable send button and show typing indicator
    sendBtn.disabled = true;
    typingIndicator.classList.add('active');
    
    // Create bot message container for streaming
    const botMessageDiv = document.createElement('div');
    botMessageDiv.className = 'message bot-message';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content streaming-text';
    
    botMessageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(botMessageDiv);
    
    // Scroll to show the new message
    messagesContainer.scrollTo({
        top: messagesContainer.scrollHeight,
        behavior: 'smooth'
    });
    
    try {
        // 🔥 STREAMING REQUEST
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        });
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        // Hide typing indicator once streaming starts
        typingIndicator.classList.remove('active');
        
        // Read the stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        
        while (true) {
            const { value, done } = await reader.read();
            
            if (done) break;
            
            // Decode the chunk
            const chunk = decoder.decode(value);
            
            // Split by newlines (SSE format)
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.text) {
                            // Append text word-by-word (streaming effect)
                            fullText += data.text;
                            
                            // Format and display
                            contentDiv.innerHTML = formatMessage(fullText);
                            
                            // Auto-scroll as text appears
                            messagesContainer.scrollTo({
                                top: messagesContainer.scrollHeight,
                                behavior: 'smooth'
                            });
                        }
                        
                        if (data.done) {
                            // Streaming complete - remove cursor
                            contentDiv.classList.remove('streaming-text');
                            
                            // Add Jarvis styling if in Jarvis mode
                            if (data.jarvis_mode) {
                                botMessageDiv.classList.add('jarvis-mode');
                            }
                            
                            // Log model used (optional)
                            console.log('✅ Model used:', data.model_used);
                            
                            break;
                        }
                        
                        if (data.error) {
                            contentDiv.innerHTML = '⚠️ ' + data.error;
                            contentDiv.classList.remove('streaming-text');
                            contentDiv.classList.add('error-message');
                            break;
                        }
                    } catch (e) {
                        // Skip invalid JSON
                        continue;
                    }
                }
            }
        }
        
    } catch (error) {
        typingIndicator.classList.remove('active');
        contentDiv.innerHTML = '❌ Error: Unable to connect to the server. Please try again.';
        contentDiv.classList.remove('streaming-text');
        contentDiv.classList.add('error-message');
        console.error('Error:', error);
    }
    
    // Re-enable send button
    sendBtn.disabled = false;
    messageInput.focus();
}

// Add message to chat (for user messages)
function addMessage(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Handle markdown-style formatting
    const formattedText = formatMessage(text);
    contentDiv.innerHTML = formattedText;
    
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom smoothly
    messagesContainer.scrollTo({
        top: messagesContainer.scrollHeight,
        behavior: 'smooth'
    });
}

// Basic formatting for messages
function formatMessage(text) {
    // Convert **bold** to <strong>
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert newlines to <br>
    text = text.replace(/\n/g, '<br>');
    
    return text;
}

// Send prompt from suggested buttons
function sendPrompt(promptText) {
    messageInput.value = promptText;
    sendMessage();
}

// Handle Enter key press
messageInput.addEventListener('keypress', function(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

// Focus input on page load
window.addEventListener('load', function() {
    messageInput.focus();
});
