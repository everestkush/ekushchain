/**
 * EverestKush JavaScript SDK
 * Complete blockchain interaction library
 * Version: 1.0.0
 */

class EverestKushSDK {
    constructor(config = {}) {
        this.apiUrl = config.apiUrl || 'http://103.74.15.88:5000';
        this.wsUrl = config.wsUrl || 'ws://103.74.15.88:5000';
        this.apiKey = config.apiKey || null;
    }

    // ========== WALLET MANAGEMENT ==========
    
    /**
     * Generate new wallet (client-side only)
     */
    static generateWallet() {
        // Generate secure random private key
        const privateKey = this.generatePrivateKey();
        const publicKey = this.privateToPublic(privateKey);
        const address = this.publicToAddress(publicKey);
        
        return {
            address: address,
            publicKey: publicKey,
            privateKey: privateKey,  // NEVER send to server
            createdAt: Date.now()
        };
    }
    
    static generatePrivateKey() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return Array.from(array).map(b => b.toString(16).padStart(2, '0')).join('');
    }
    
    static privateToPublic(privateKey) {
        // Simplified - in production use proper crypto library
        const hash = this.sha256(privateKey);
        return '0x' + hash;
    }
    
    static publicToAddress(publicKey) {
        const hash = this.sha256(publicKey);
        return 'ekush' + hash.slice(0, 40);
    }
    
    static sha256(message) {
        const msgBuffer = new TextEncoder().encode(message);
        const hashBuffer = crypto.subtle.digest('SHA-256', msgBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }
    
    // ========== TRANSACTIONS ==========
    
    /**
     * Create and sign transaction
     */
    createTransaction(to, amount, from, privateKey) {
        const tx = {
            to: to,
            amount: amount,
            from: from,
            timestamp: Date.now(),
            nonce: Math.random().toString(36)
        };
        
        // Sign transaction
        const txHash = this.hashTransaction(tx);
        const signature = this.signTransaction(txHash, privateKey);
        
        return {
            ...tx,
            signature: signature,
            publicKey: this.privateToPublic(privateKey)
        };
    }
    
    hashTransaction(tx) {
        return this.constructor.sha256(JSON.stringify(tx));
    }
    
    signTransaction(hash, privateKey) {
        // In production: use proper ECDSA signing
        return this.constructor.sha256(hash + privateKey);
    }
    
    /**
     * Send transaction to network
     */
    async sendTransaction(tx) {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.apiKey) {
            headers['X-API-Key'] = this.apiKey;
        }
        
        const response = await fetch(`${this.apiUrl}/transaction/broadcast`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(tx)
        });
        
        return await response.json();
    }
    
    // ========== BLOCKCHAIN QUERIES ==========
    
    /**
     * Get address balance
     */
    async getBalance(address) {
        const response = await fetch(`${this.apiUrl}/balance/${address}`);
        return await response.json();
    }
    
    /**
     * Get blockchain stats
     */
    async getStats() {
        const response = await fetch(`${this.apiUrl}/api/stats`);
        return await response.json();
    }
    
    /**
     * Search blockchain
     */
    async search(query) {
        const response = await fetch(`${this.apiUrl}/search?q=${encodeURIComponent(query)}`);
        return await response.json();
    }
    
    /**
     * Get health status
     */
    async health() {
        const response = await fetch(`${this.apiUrl}/health`);
        return await response.json();
    }
    
    // ========== WEBSOCKET REAL-TIME ==========
    
    /**
     * Subscribe to real-time balance updates
     */
    subscribeBalance(address, callback) {
        // Load Socket.IO dynamically
        return new Promise((resolve, reject) => {
            if (typeof io === 'undefined') {
                const script = document.createElement('script');
                script.src = 'https://cdn.socket.io/4.5.0/socket.io.min.js';
                script.onload = () => {
                    const socket = this._connectWebSocket(address, callback);
                    resolve(socket);
                };
                script.onerror = reject;
                document.head.appendChild(script);
            } else {
                const socket = this._connectWebSocket(address, callback);
                resolve(socket);
            }
        });
    }
    
    _connectWebSocket(address, callback) {
        const socket = io(this.wsUrl);
        
        socket.on('connect', () => {
            socket.emit('subscribe_balance', { address: address });
        });
        
        socket.on('balance_update', callback);
        
        return socket;
    }
    
    // ========== MINING (for validators) ==========
    
    /**
     * Get mining work (requires API key)
     */
    async getMiningWork() {
        const headers = { 'Content-Type': 'application/json' };
        if (this.apiKey) {
            headers['X-API-Key'] = this.apiKey;
        }
        
        const response = await fetch(`${this.apiUrl}/rpc/getwork`, {
            method: 'POST',
            headers: headers
        });
        
        return await response.json();
    }
    
    /**
     * Submit mined block (requires API key)
     */
    async submitBlock(block) {
        const headers = { 'Content-Type': 'application/json' };
        if (this.apiKey) {
            headers['X-API-Key'] = this.apiKey;
        }
        
        const response = await fetch(`${this.apiUrl}/rpc/submitblock`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(block)
        });
        
        return await response.json();
    }
}

// Export for different environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EverestKushSDK;
}

if (typeof window !== 'undefined') {
    window.EverestKush = EverestKushSDK;
}
