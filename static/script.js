// Get DOM elements
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const messagesContainer = document.getElementById('messagesContainer');
const typingIndicator = document.getElementById('typingIndicator');

// Send message function
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
    
    try {
        // Send request to backend
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        // Hide typing indicator
        typingIndicator.classList.remove('active');
        
        // Add bot response
        if (data.response) {
            addMessage(data.response, 'bot');
        } else if (data.error) {
            addMessage('Oops! Something went wrong: ' + data.error, 'bot');
        }
    } catch (error) {
        typingIndicator.classList.remove('active');
        addMessage('Error: Unable to connect to the server. Please check your API key and try again.', 'bot');
        console.error('Error:', error);
    }
    
    // Re-enable send button
    sendBtn.disabled = false;
    messageInput.focus();
}

// Add message to chat
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

// Auto-resize textarea would go here if we switch to textarea
// For now, keeping it as input for simplicity
