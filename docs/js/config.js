// Centralized configuration management
const Config = {
    get backendUrl() {
        // Automatically detect environment
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            return 'http://localhost:10000';
        }
        
        // Production environment (GitHub Pages)
        return 'https://curly-disco-bzls.onrender.com';
    },
    
    get isLocal() {
        return window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    },
    
    get environment() {
        return this.isLocal ? 'development' : 'production';
    },
    
    // API endpoints
    get endpoints() {
        const base = this.backendUrl;
        return {
            chat: `${base}/chat`,
            endConversation: `${base}/api/end-conversation`,
            autoSave: `${base}/api/auto-save`,
            conversationStatus: `${base}/api/conversation-status`,
            health: `${base}/health`,
            testDb: `${base}/test-db`
        };
    }
};

// Log current configuration for debugging
console.log(`Environment: ${Config.environment}`);
console.log(`Backend URL: ${Config.backendUrl}`);

// Make Config available globally or export it
window.Config = Config;
