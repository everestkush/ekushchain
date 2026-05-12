/**
 * EverestKush JavaScript SDK
 * Use this to interact with EverestKush blockchain
 */

class EverestKush {
    constructor(baseURL = 'https://103.74.15.88:8080/api') {
        this.baseURL = baseURL;
        this.apiKey = null;
    }

    setApiKey(key) {
        this.apiKey = key;
    }

    async request(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (this.apiKey) {
            headers['X-API-Key'] = this.apiKey;
        }

        const response = await fetch(`${this.baseURL}${endpoint}`, {
            ...options,
            headers
        });
        
        return response.json();
    }

    // Wallet methods
    async createWallet() {
        return this.request('/wallet/new');
    }

    async generateMnemonic(words = 12) {
        return this.request(`/wallet/bip39/generate?words=${words}`);
    }

    async getBalance(address) {
        return this.request(`/balance/${address}`);
    }

    async getUTXOs(address) {
        return this.request(`/utxos/${address}`);
    }

    // Transaction methods
    async sendTransaction(sender, recipient, amount, privateKey) {
        return this.request('/transaction', {
            method: 'POST',
            body: JSON.stringify({ sender, recipient, amount, private_key: privateKey })
        });
    }

    // Blockchain methods
    async getStats() {
        return this.request('/stats');
    }

    async getChain() {
        return this.request('/chain');
    }

    async getBlock(height) {
        return this.request(`/block/${height}`);
    }

    async search(query) {
        return this.request(`/search?q=${query}`);
    }

    // Validator methods
    async getValidators() {
        return this.request('/api/v1/validator/list');
    }

    async bondValidator(address, amount) {
        return this.request('/api/v1/validator/bond', {
            method: 'POST',
            body: JSON.stringify({ address, amount })
        });
    }

    // WebSocket connection
    connectWebSocket() {
        const wsUrl = this.baseURL.replace('http', 'ws').replace('/api', '');
        this.ws = new WebSocket(`${wsUrl}`);
        
        this.ws.onopen = () => {
            console.log('Connected to EverestKush');
        };
        
        return this.ws;
    }

    subscribeBalance(address, callback) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.connectWebSocket();
        }
        
        this.ws.onopen = () => {
            this.ws.send(JSON.stringify({
                type: 'subscribe_balance',
                address: address
            }));
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'balance_update') {
                callback(data);
            }
        };
    }
}

// Export for Node.js and browser
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EverestKush;
} else {
    window.EverestKush = EverestKush;
}
