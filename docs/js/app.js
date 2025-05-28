// Main application logic
document.addEventListener('DOMContentLoaded', function() {
    // Initialize managers
    const conversationManager = new ConversationManager();
    const chatInterface = new ChatInterface(conversationManager);
    
    // Get DOM elements
    const newConversationBtn = document.getElementById('newConversationBtn');
    const endConversationBtn = document.getElementById('endConversationBtn');
    const statusBtn = document.getElementById('statusBtn');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    
    // Event listeners for conversation controls
    newConversationBtn.addEventListener('click', async () => {
        await conversationManager.startNewConversation();
        chatInterface.clearChat();
        chatInterface.addMessage('system', '🆕 <em>Ready for a new conversation! What would you like to learn about?</em>', true);
    });
    
    endConversationBtn.addEventListener('click', async () => {
        const success = await conversationManager.endConversation();
        if (success) {
            chatInterface.addMessage('system', '🔚 <em>Conversation ended. Thanks for chatting!</em>', true);
        }
    });
    
    statusBtn.addEventListener('click', async () => {
        await conversationManager.checkStatus();
    });
    
    // Chat event listeners
    sendButton.addEventListener('click', () => {
        chatInterface.sendMessage();
    });
    
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            chatInterface.sendMessage();
        }
    });
    
    // Initialize conversation status
    conversationManager.checkStatus();
    
    // Welcome message
    chatInterface.addMessage('system', '👋 <em>Welcome! Click "New Conversation" to start chatting, or just type a message!</em>', true);
});
