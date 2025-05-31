document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing app...');
    
    // Initialize managers
    const conversationManager = new ConversationManager();
    const chatInterface = new ChatInterface(conversationManager);
    
    // Store loaded users for reference
    let loadedUsers = [];
    
    // Theme toggle functionality
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        // Load saved theme preference
        const savedTheme = localStorage.getItem('theme') || 'light-mode';
        document.body.className = savedTheme;
        themeToggle.textContent = savedTheme === 'dark-mode' ? '☀️' : '🌙';
        
        themeToggle.addEventListener('click', () => {
            const isDark = document.body.classList.contains('dark-mode');
            
            if (isDark) {
                document.body.className = 'light-mode';
                themeToggle.textContent = '🌙';
                localStorage.setItem('theme', 'light-mode');
            } else {
                document.body.className = 'dark-mode';
                themeToggle.textContent = '☀️';
                localStorage.setItem('theme', 'dark-mode');
            }
        });
    }
    
    // User selection handling with auto new chat
    const userSelect = document.getElementById('userSelect');
    if (userSelect) {
        userSelect.addEventListener('change', async function() {
            const selectedUserId = this.value;
            
            if (selectedUserId) {
                // Find the user object from loaded users
                const selectedUser = loadedUsers.find(user => user.id === selectedUserId);
                
                if (selectedUser) {
                    // End current conversation if active
                    if (conversationManager.conversationActive) {
                        await conversationManager.endConversation();
                    }
                    
                    // Set new user
                    conversationManager.setUser(selectedUser);
                    
                    // Clear chat and start new conversation
                    chatInterface.clearChat();
                    
                    // Start new conversation automatically
                    const started = await conversationManager.startNewConversation();
                    if (started) {
                        chatInterface.addMessage('system', `🆕 <em>Hi ${selectedUser.name}! Ready for a new conversation? What would you like to learn about?</em>`, true);
                    }
                }
            } else {
                // No user selected
                conversationManager.userId = null;
                conversationManager.currentUser = null;
                chatInterface.clearChat();
                chatInterface.addMessage('system', '👋 <em>Please select a user to start chatting!</em>', true);
            }
        });
    }
    
    // Conversation control buttons
    const newConversationBtn = document.getElementById('newConversationBtn');
    if (newConversationBtn) {
        newConversationBtn.addEventListener('click', async () => {
            if (!conversationManager.userId) {
                chatInterface.addMessage('system', '❌ <em>Please select a user first!</em>', true);
                return;
            }
            
            await conversationManager.startNewConversation();
            chatInterface.clearChat();
            chatInterface.addMessage('system', `🆕 <em>Ready for a new conversation, ${conversationManager.currentUser.name}! What would you like to learn about?</em>`, true);
        });
    }
    
    const endConversationBtn = document.getElementById('endConversationBtn');
    if (endConversationBtn) {
        endConversationBtn.addEventListener('click', async () => {
            const success = await conversationManager.endConversation();
            if (success) {
                chatInterface.addMessage('system', '🔚 <em>Conversation ended. Thanks for chatting!</em>', true);
            }
        });
    }
    
    const statusBtn = document.getElementById('statusBtn');
    if (statusBtn) {
        statusBtn.addEventListener('click', async () => {
            await conversationManager.checkStatus();
        });
    }
    
    // Chat functionality
    const sendButton = document.getElementById('sendButton');
    const userInput = document.getElementById('userInput');
    if (sendButton && userInput) {
        sendButton.addEventListener('click', () => {
            if (!conversationManager.userId) {
                chatInterface.addMessage('system', '❌ <em>Please select a user first!</em>', true);
                return;
            }
            chatInterface.sendMessage();
        });
        
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                if (!conversationManager.userId) {
                    chatInterface.addMessage('system', '❌ <em>Please select a user first!</em>', true);
                    return;
                }
                chatInterface.sendMessage();
            }
        });
    }
    
    // Load users and store reference
    if (typeof loadUsers === 'function') {
        loadUsers().then(users => {
            loadedUsers = users || [];
        });
    }
    
    // Welcome message
    chatInterface.addMessage('system', '👋 <em>Welcome! Select a user to start chatting!</em>', true);
});
