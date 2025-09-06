class ChatBot {
    constructor() {
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.isTyping = false;
        
        this.init();
    }

    init() {
        this.messageInput.addEventListener('input', this.handleInputChange.bind(this));
        this.messageInput.addEventListener('keypress', this.handleKeyPress.bind(this));
        this.sendButton.addEventListener('click', this.sendMessage.bind(this));
        
        this.messageInput.focus();
    }

    handleInputChange(e) {
        const message = e.target.value.trim();
        this.sendButton.disabled = message.length === 0;
    }

    handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isTyping) return;

        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.sendButton.disabled = true;
        this.messageInput.focus();

        this.showTypingIndicator();
        
        try {
            const response = await this.sendToAPI(message);
            this.hideTypingIndicator();
            this.addMessage(response, 'bot');
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage('죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.', 'bot');
            console.error('API Error:', error);
        }
    }

    async sendToAPI(message) {
        try {
            console.log('Sending message:', message);
            console.log('Request URL:', 'http://localhost:5001/chatbot/chat');
            
            const response = await fetch('/chatbot/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Response data:', data);
            return data.reply || data.response || data.message || '응답을 받을 수 없습니다.';
        } catch (error) {
            console.error('Detailed error:', error);
            throw error;
        }
    }

    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const currentTime = new Date().toLocaleTimeString('ko-KR', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: true 
        });

        if (sender === 'bot') {
            messageDiv.innerHTML = `
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <div class="message-bubble">${this.escapeHtml(text)}</div>
                    <div class="message-time">${currentTime}</div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-content">
                    <div class="message-bubble">${this.escapeHtml(text)}</div>
                    <div class="message-time">${currentTime}</div>
                </div>
                <div class="message-avatar">👤</div>
            `;
        }

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        if (this.isTyping) return;
        
        this.isTyping = true;
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <div class="message-bubble typing-indicator">
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        this.isTyping = false;
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;")
            .replace(/\n/g, "<br>");
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }

    addWelcomeMessages() {
        const welcomeMessages = [
            "안녕하세요! PinGrow ChatBot입니다. 🤖",
            "경제, 금융 관련 질문이나 정책에 대해 궁금한 것이 있으시면 언제든 물어보세요!",
            "어떤 도움이 필요하신가요?"
        ];

        welcomeMessages.forEach((message, index) => {
            setTimeout(() => {
                this.addMessage(message, 'bot');
            }, index * 1000);
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const chatBot = new ChatBot();
    
    setTimeout(() => {
        if (document.querySelectorAll('.message').length <= 1) {
            chatBot.addWelcomeMessages();
        }
    }, 500);
});

window.addEventListener('beforeunload', function() {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        localStorage.setItem('draftMessage', messageInput.value);
    }
});

window.addEventListener('load', function() {
    const draftMessage = localStorage.getItem('draftMessage');
    if (draftMessage) {
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.value = draftMessage;
            messageInput.dispatchEvent(new Event('input'));
        }
        localStorage.removeItem('draftMessage');
    }
});