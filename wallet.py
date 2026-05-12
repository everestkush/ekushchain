#!/usr/bin/env python3
"""
EverestKush Wallet - Command Line Interface
"""
import sys
import sqlite3
import json
import argparse
from datetime import datetime

DB_PATH = "/home/kushal/everestkush/ekush_chain.db"

class EverestKushWallet:
    def __init__(self, address):
        self.address = address
    
    def get_balance(self):
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT SUM(amount), COUNT(*) FROM utxos 
                WHERE address = ? AND is_spent = 0
            """, (self.address,))
            balance, utxos = cur.fetchone()
            return (balance or 0) / 1000000, utxos or 0
    
    def get_transaction_history(self, limit=50):
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT tx_hash, sender, recipient, amount, fee, timestamp 
                FROM transactions 
                WHERE sender = ? OR recipient = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (self.address, self.address, limit))
            
            txs = []
            for tx in cur.fetchall():
                txs.append({
                    'txid': tx[0][:16] + '...',
                    'type': 'SENT' if tx[1] == self.address else 'RECEIVED',
                    'counterparty': tx[2] if tx[1] == self.address else tx[1],
                    'amount': tx[3] / 1000000,
                    'fee': tx[4] / 1000000,
                    'timestamp': datetime.fromtimestamp(tx[5]).strftime('%Y-%m-%d %H:%M:%S')
                })
            return txs
    
    def get_utxos(self):
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT outpoint, amount/1000000, block_height, created_at
                FROM utxos 
                WHERE address = ? AND is_spent = 0
                ORDER BY amount DESC
            """, (self.address,))
            return [{'outpoint': u[0], 'amount': u[1], 'block': u[2], 'created': u[3]} for u in cur.fetchall()]
    
    def display_info(self):
        balance, utxos = self.get_balance()
        print("\n" + "=" * 60)
        print(f"EverestKush  EVERESTKUSH WALLET")
        print("=" * 60)
        print(f"- Address: {self.address}")
        print(f"[FUNDS] Balance: {balance:,.2f} EKUSH")
        print(f"[UTXO] UTXOs: {utxos}")
        print("=" * 60)
        
        # Show transaction history
        print("\n[LOG] RECENT TRANSACTIONS:")
        print("-" * 60)
        txs = self.get_transaction_history(10)
        if txs:
            for tx in txs:
                direction = "->" if tx['type'] == 'SENT' else "<-"
                print(f"{tx['timestamp']} {direction} {tx['amount']:.2f} EKUSH {tx['type']} {tx['counterparty'][:20]}...")
        else:
            print("No transactions found")
        
        # Show UTXOs
        print("\n[UTXO] UTXOs (Unspent Outputs):")
        print("-" * 60)
        utxos = self.get_utxos()
        if utxos:
            for i, utxo in enumerate(utxos[:10], 1):
                print(f"{i}. {utxo['amount']:.2f} EKUSH - {utxo['outpoint'][:30]}...")
            if len(utxos) > 10:
                print(f"... and {len(utxos) - 10} more")
        else:
            print("No UTXOs found")

def main():
    parser = argparse.ArgumentParser(description='EverestKush Wallet')
    parser.add_argument('address', help='Wallet address')
    parser.add_argument('--history', type=int, help='Show transaction history (limit)', default=10)
    
    args = parser.parse_args()
    
    wallet = EverestKushWallet(args.address)
    wallet.display_info()

if __name__ == "__main__":
    main()
