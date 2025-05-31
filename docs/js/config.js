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

// Debug logging
console.log(`Environment: ${Config.isLocal ? 'development' : 'production'}`);
console.log(`Backend URL: ${Config.backendUrl}`);
console.log(`Chat endpoint: ${Config.endpoints.chat}`);

// Test backend connectivity
fetch(Config.endpoints.health)
    .then(response => response.json())
    .then(data => console.log('Backend health check:', data))
    .catch(error => console.error('Backend connection failed:', error));

window.Config = Config;

