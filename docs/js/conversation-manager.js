// Conversation management logic
class ConversationManager {
    constructor() {
        this.conversationActive = false;
        this.conversationId = null;
        this.userId = this.getUserId();
        this.setupEventListeners();
    }
    
    getUserId() {
        let userId = localStorage.getItem('userId');
        if (!userId) {
            userId = Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
            localStorage.setItem('userId', userId);
        }
        return userId;
    }
    
    setupEventListeners() {
        // Primary approach - pagehide is more reliable than beforeunload
        window.addEventListener('pagehide', (event) => {
            if (this.conversationActive) {
                this.saveConversationOnExit();
            }
        });
        
        // Fallback for older browsers
        window.addEventListener('beforeunload', (event) => {
            if (this.conversationActive) {
                this.saveConversationOnExit();
            }
        });
        
        // Handle visibility change (tab switching, minimizing)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.conversationActive) {
                this.autoSaveConversation();
            }
        });
    }
    
    saveConversationOnExit() {
        if (!this.conversationActive) return;
        
        const data = JSON.stringify({
            user_id: this.userId,
            action: 'force_end_conversation',
            timestamp: new Date().toISOString()
        });
        
        navigator.sendBeacon(Config.endpoints.endConversation, data);
    }
    
    autoSaveConversation() {
        if (this.conversationActive) {
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
    
    async endConversation() {
        if (!this.conversationActive) return;
        
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
        try {
            const response = await fetch(`${Config.endpoints.conversationStatus}/${this.userId}`);
            const data = await response.json();
            
            if (data.active) {
                this.conversationActive = true;
                this.updateStatusIndicator('🟢 Conversation is active', 'status-active');
            } else {
                this.conversationActive = false;
                this.updateStatusIndicator('🔴 No active conversation', 'status-inactive');
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
        indicator.textContent = message;
        indicator.className = `status-indicator ${className}`;
        indicator.style.display = 'block';
        
        // Hide after 3 seconds
        setTimeout(() => {
            indicator.style.display = 'none';
        }, 3000);
    }
}
