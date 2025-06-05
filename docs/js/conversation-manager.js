class ConversationManager {
    constructor() {
        this.conversationActive = false;
        this.conversationId = null;
        this.userId = null; // Will be set when user is selected
        this.currentUser = null; // Store full user object
        this.setupEventListeners();
    }
    
    setUser(user) {
        this.userId = user.id; // Use the ID from JSON
        this.currentUser = user;
        console.log(`User set: ${user.name} (ID: ${user.id})`);
    }
    
    setupEventListeners() {
        // Page close handlers
        window.addEventListener('pagehide', (event) => {
            if (this.conversationActive) {
                this.saveConversationOnExit();
            }
        });
        
        window.addEventListener('beforeunload', (event) => {
            if (this.conversationActive) {
                this.saveConversationOnExit();
            }
        });
        
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.conversationActive) {
                this.autoSaveConversation();
            }
        });
    }
    
    saveConversationOnExit() {
        if (!this.conversationActive) return;
        
        // Create FormData instead of JSON for sendBeacon compatibility
        const formData = new FormData();
        formData.append('user_id', this.userId);
        formData.append('action', 'force_end_conversation');
        formData.append('timestamp', new Date().toISOString());
        
        navigator.sendBeacon(Config.endpoints.endConversation, formData);
    }
    
    autoSaveConversation() {
        if (this.conversationActive && this.userId) {
            fetch(Config.endpoints.autoSave, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    timestamp: new Date().toISOString()
                })
            }).catch(err => console.log('Auto-save failed:', err));
        }
    }
    
    async startNewConversation() {
        if (!this.userId) {
            this.updateStatusIndicator('❌ Please select a user first', 'status-inactive');
            return false;
        }
        
        try {
            // Verify with backend if conversation can start
            const status = await this.checkStatus();
            if (status && status.active) {
                this.conversationActive = true;
                this.updateStatusIndicator(`🟢 Continuing conversation for ${this.currentUser.name}`, 'status-active');
                return true;
            }
            
            // Start new conversation
            this.conversationActive = true;
            this.conversationId = Date.now().toString();
            
            // Send initial message to establish conversation
            const response = await fetch(Config.endpoints.chat, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    message: "Hello",
                    force_start: true
                })
            });
            
            if (!response.ok) throw new Error('Failed to start conversation');
            
            this.updateStatusIndicator(`🟢 New conversation started for ${this.currentUser.name}!`, 'status-active');
            return true;
            
        } catch (error) {
            console.error('Start conversation failed:', error);
            this.updateStatusIndicator('❌ Failed to start conversation', 'status-error');
            return false;
        }
    }
    
    async endConversation() {
        if (!this.conversationActive || !this.userId) {
            this.updateStatusIndicator('❌ No active conversation to end', 'status-inactive');
            return false;
        }
        
        try {
            const url = Config.endpoints.endConversation;
            console.log(`Ending conversation at: ${url}`);
            
            console.log('Sending end conversation request with:', {
                user_id: this.userId,
                action: 'manual_end'
            });
            
            const response = await fetch(url, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    action: 'manual_end'
                }),
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('End conversation response:', data);
            
            if (data && data.status === 'conversation_ended') {
                this.conversationActive = false;
                this.conversationId = null;
                this.updateStatusIndicator('🔴 Conversation ended successfully', 'status-inactive');
                return true;
            } else {
                throw new Error('Unexpected response format');
            }
        } catch (error) {
            console.error('Failed to end conversation:', error);
            this.updateStatusIndicator('❌ Failed to end conversation', 'status-error');
            return false;
        }
    }
    
    async checkStatus() {
        if (!this.userId) {
            this.updateStatusIndicator('❌ No user selected', 'status-inactive');
            return null;
        }
        
        try {
            const url = `${Config.endpoints.conversationStatus}/${this.userId}`;
            console.log(`Checking conversation status at: ${url}`);
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Status response:', data);
            
            if (data && data.hasOwnProperty('active')) {
                this.conversationActive = true;
                this.updateStatusIndicator(`🟢 ${this.currentUser.name} has an active conversation`, 'status-active');
            } else {
                this.conversationActive = false;
                this.updateStatusIndicator(`🔴 No active conversation for ${this.currentUser.name}`, 'status-inactive');
            }
            
            return data;
        } catch (error) {
            console.error('Status check failed:', error);
            this.updateStatusIndicator('❌ Status check failed', 'status-inactive');
            return null;
        }
    }
    
    updateStatusIndicator(message, className) {
        const indicator = document.getElementById('statusIndicator');
        if (indicator) {
            indicator.textContent = message;
            indicator.className = `status-indicator ${className}`;
            indicator.style.display = 'block';
            
            // Hide after 3 seconds
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 3000);
        }
    }
}
