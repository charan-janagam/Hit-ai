const API_BASE_URL = window.location.origin;

const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const messagesContainer = document.getElementById("messagesContainer");
const typingIndicator = document.getElementById("typingIndicator");

async function sendMessage() {
  const message = messageInput.value.trim();
  if (!message) return;

  addMessage(message, "user");
  messageInput.value = "";
  sendBtn.disabled = true;
  typingIndicator.classList.add("active");

  const botDiv = document.createElement("div");
  botDiv.className = "message bot-message";
  const contentDiv = document.createElement("div");
  contentDiv.className = "message-content streaming-text";
  botDiv.appendChild(contentDiv);
  messagesContainer.appendChild(botDiv);

  const res = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message })
  });

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let full = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    chunk.split("\n").forEach(line => {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        if (!data || data === "[DONE]") return;
        const json = JSON.parse(data);
        const delta = json.choices?.[0]?.delta?.content;
        if (delta) {
          full += delta;
          contentDiv.innerHTML = full;
        }
      }
    });
  }

  contentDiv.classList.remove("streaming-text");
  typingIndicator.classList.remove("active");
  sendBtn.disabled = false;
}

function addMessage(text, type) {
  const msg = document.createElement("div");
  msg.className = "message";
  msg.innerHTML = `<div class="message-content">${text}</div>`;
  messagesContainer.appendChild(msg);
}

function sendPrompt(text) {
  messageInput.value = text;
  sendMessage();
}

sendBtn.onclick = sendMessage;
messageInput.addEventListener("keypress", e => {
  if (e.key === "Enter") sendMessage();
});
