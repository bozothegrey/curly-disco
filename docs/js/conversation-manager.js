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
        
        this.conversationActive = true;
        this.conversationId = Date.now().toString();
        
        this.updateStatusIndicator(`🟢 New conversation started for ${this.currentUser.name}!`, 'status-active');
        
        return true;
    }
    
    async endConversation() {
        if (!this.conversationActive || !this.userId) return false;
        
        try {
            const response = await fetch(Config.endpoints.endConversation, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    action: 'manual_end'
                })
            });
            
            if (response.ok) {
                this.conversationActive = false;
                this.conversationId = null;
                this.updateStatusIndicator('🔴 Conversation ended', 'status-inactive');
                return true;
            }
        } catch (error) {
            console.error('Failed to end conversation:', error);
        }
        return false;
    }
    
    async checkStatus() {
        if (!this.userId) {
            this.updateStatusIndicator('❌ No user selected', 'status-inactive');
            return null;
        }
        
        try {
            const response = await fetch(`${Config.endpoints.conversationStatus}/${this.userId}`);
            const data = await response.json();
            
            if (data.active) {
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
