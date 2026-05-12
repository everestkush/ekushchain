/**
 * EverestKush SDK - Browser Version
 * For direct inclusion in HTML
 */
window.EverestKush = (function() {
    class EverestKushWallet {
        constructor(apiUrl = 'http://103.74.15.88:5000') {
            this.apiUrl = apiUrl;
            this.wsUrl = apiUrl.replace('http', 'ws');
        }
        
        static async generateWallet() {
            // Generate using Web Crypto API
            const keyPair = await window.crypto.subtle.generateKey(
                {
                    name: "ECDSA",
                    namedCurve: "P-256",
                },
                true,
                ["sign", "verify"]
            );
            
            const privateKey = await window.crypto.subtle.exportKey("pkcs8", keyPair.privateKey);
            const publicKey = await window.crypto.subtle.exportKey("spki", keyPair.publicKey);
            
            // Convert to hex
            const privateHex = Array.from(new Uint8Array(privateKey)).map(b => b.toString(16).padStart(2, '0')).join('');
            const publicHex = Array.from(new Uint8Array(publicKey)).map(b => b.toString(16).padStart(2, '0')).join('');
            const address = 'ekush' + publicHex.slice(0, 40);
            
            return { address, publicKey: publicHex, privateKey: privateHex };
        }
        
        async getBalance(address) {
            const response = await fetch(`${this.apiUrl}/balance/${address}`);
            return response.json();
        }
        
        async sendTransaction(to, amount, privateKey) {
            const tx = {
                to: to,
                amount: amount,
                timestamp: Date.now(),
                from: this.address
            };
            
            // Sign transaction (simplified - use proper crypto)
            const txHash = await this.hashTransaction(tx);
            const signature = await this.sign(txHash, privateKey);
            
            const signedTx = { ...tx, signature, publicKey: this.publicKey };
            
            const response = await fetch(`${this.apiUrl}/transaction/broadcast`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(signedTx)
            });
            
            return response.json();
        }
        
        async hashTransaction(tx) {
            const encoder = new TextEncoder();
            const data = encoder.encode(JSON.stringify(tx));
            const hash = await window.crypto.subtle.digest('SHA-256', data);
            return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, '0')).join('');
        }
        
        async sign(hash, privateKey) {
            // Import private key and sign
            // This is simplified - implement proper ECDSA
            return "0x" + hash.slice(0, 64);
        }
        
        subscribeBalance(address, callback) {
            const socket = io(this.wsUrl);
            socket.on('connect', () => {
                socket.emit('subscribe_balance', { address: address });
            });
            socket.on('balance_update', callback);
            return socket;
        }
    }
    
    return { Wallet: EverestKushWallet };
})();

// Example usage in console:
// const wallet = await EverestKush.Wallet.generateWallet();
// console.log(wallet.address);
