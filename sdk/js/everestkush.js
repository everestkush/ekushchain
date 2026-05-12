/**
 * EverestKush JavaScript SDK
 * Client-side wallet and transaction signing
 * NEVER sends private keys to server
 */

class EverestKushWallet {
    constructor() {
        this.apiUrl = 'http://103.74.15.88:5000';
        this.wsUrl = 'ws://103.74.15.88:5001';
    }
    
    /**
     * Generate new wallet (client-side only)
     */
    static generateWallet() {
        // Use Web Crypto API for secure key generation
        const privateKey = crypto.randomBytes(32).toString('hex');
        const publicKey = this.privateToPublic(privateKey);
        const address = this.publicToAddress(publicKey);
        
        return {
            address: address,
            publicKey: publicKey,
            privateKey: privateKey  // NEVER send to server
        };
    }
    
    /**
     * Create and sign transaction (client-side)
     */
    signTransaction(tx, privateKey) {
        const txHash = this.hashTransaction(tx);
        const signature = this.sign(txHash, privateKey);
        
        return {
            ...tx,
            signature: signature,
            publicKey: this.privateToPublic(privateKey)
        };
    }
    
    /**
     * Broadcast signed transaction to network
     */
    async broadcastTransaction(signedTx) {
        const response = await fetch(`${this.apiUrl}/transaction/broadcast`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(signedTx)
        });
        return await response.json();
    }
    
    /**
     * Get balance (public API - no key needed)
     */
    async getBalance(address) {
        const response = await fetch(`${this.apiUrl}/balance/${address}`);
        return await response.json();
    }
    
    /**
     * WebSocket subscription for real-time updates
     */
    subscribeBalance(address, callback) {
        const socket = io(this.wsUrl);
        socket.on('connect', () => {
            socket.emit('subscribe_balance', { address: address });
        });
        socket.on('balance_update', callback);
        return socket;
    }
    
    // Crypto helpers (simplified - use proper crypto lib)
    static privateToPublic(privateKey) {
        // Implement secp256k1 key derivation
        return '0x' + require('crypto').createHash('sha256').update(privateKey).digest('hex');
    }
    
    static publicToAddress(publicKey) {
        return 'ekush' + publicKey.slice(0, 40);
    }
    
    static hashTransaction(tx) {
        const str = JSON.stringify(tx);
        return require('crypto').createHash('sha256').update(str).digest('hex');
    }
    
    static sign(hash, privateKey) {
        // Implement ECDSA signing
        return require('crypto').createHmac('sha256', privateKey).update(hash).digest('hex');
    }
}

// NPM package export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EverestKushWallet;
}
