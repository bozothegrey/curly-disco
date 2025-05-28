// Chat interface management
class ChatInterface {
    constructor(conversationManager) {
        this.conversationManager = conversationManager;
        this.chatbox = document.getElementById('chatbox');
        this.userInput = document.getElementById('userInput');
        this.sendButton = document.getElementById('sendButton');
        this.BACKEND_URL = "https://curly-disco-bzls.onrender.com/chat";
    }
    
    addMessage(sender, text, isSystem = false) {
        const messageDiv = document.createElement('div');
        const messageClass = isSystem ? 'system-message' : (sender === 'child' ? 'child-message' : 'ai-message');
        messageDiv.classList.add('message', messageClass);
        
        if (isSystem) {
            messageDiv.innerHTML = text;
        } else {
            messageDiv.innerHTML = `<b>${sender === 'child' ? 'You' : 'AI'}:</b> ${text}`;
        }
        
        this.chatbox.appendChild(messageDiv);
        this.chatbox.scrollTop = this.chatbox.scrollHeight;
    }
    
    showTypingIndicator() {
        const typingIndicator = document.createElement('div');
        typingIndicator.id = 'typing';
        typingIndicator.textContent = "AI is thinking...";
        this.chatbox.appendChild(typingIndicator);
        return typingIndicator;
    }
    
    removeTypingIndicator(indicator) {
        if (indicator && indicator.parentNode) {
            this.chatbox.removeChild(indicator);
        }
    }
    
    async sendMessage(forceStart = false) {
        const childMessage = this.userInput.value.trim();
        if (!childMessage) return;
    
        this.addMessage('child', childMessage);
        this.userInput.value = '';
        this.sendButton.disabled = true;
    
        const typingIndicator = this.showTypingIndicator();
    
        try {
            const response = await fetch(this.BACKEND_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.conversationManager.userId,
                    message: childMessage,
                    force_start: forceStart
                })
            });
            
            if (!response.ok) throw new Error(`API error: ${response.status}`);
            const data = await response.json();
            
            this.removeTypingIndicator(typingIndicator);
            this.addMessage('ai', data.response);
            
            // Handle conversation state changes
            if (data.conversation_started) {
                this.conversationManager.conversationActive = true;
                this.addMessage('system', '🆕 <em>New conversation started!</em>', true);
            }
            
            if (data.conversation_ended) {
                this.conversationManager.conversationActive = false;
                this.addMessage('system', '🔚 <em>Conversation ended. Click "New Conversation" to start again!</em>', true);
            }
            
        } catch (error) {
            this.removeTypingIndicator(typingIndicator);
            this.addMessage('ai', "Oops! Please try again later.");
            console.error("API error:", error);
        } finally {
            this.sendButton.disabled = false;
        }
    }
    
    clearChat() {
        this.chatbox.innerHTML = '';
    }
}
