from flask import Flask
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from rocksdict import Rdict
import hashlib
import secrets
import time
import json
import os

app = Flask(__name__)
CORS(app)

ROCKSDB_PATH = "/home/kushal/everestkush/rocksdb_data"
VOTERS_DB = Rdict(f"{ROCKSDB_PATH}/voters")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/voter/register_with_wallet', methods=['POST'])
def register_with_wallet():
    data = request.json
    wallet = data.get('wallet_address')
    
    if not wallet:
        return jsonify({"error": "wallet_address required"}), 400
    
    # Check if already registered
    for key, value in VOTERS_DB.items():
        voter = json.loads(value.decode())
        if voter.get('wallet_address') == wallet:
            return jsonify({"error": "Wallet already registered"}), 400
    
    voter_id = hashlib.sha256(f"{wallet}{secrets.token_hex(32)}{time.time()}".encode()).hexdigest()
    priv_key = secrets.token_hex(64)
    pub_key = hashlib.sha256(priv_key.encode()).hexdigest()
    
    voter_data = {
        "voter_id": voter_id,
        "public_key": pub_key,
        "private_key": priv_key,
        "wallet_address": wallet,
        "has_voted": 0,
        "choice": None,
        "created_at": int(time.time())
    }
    
    VOTERS_DB[voter_id.encode()] = json.dumps(voter_data).encode()
    
    return jsonify({
        "success": True,
        "voter_id": voter_id,
        "public_key": pub_key,
        "private_key": priv_key,
        "wallet_address": wallet,
        "message": "Wallet registered successfully"
    })

@app.route('/voter/check_by_wallet', methods=['GET'])
def check_by_wallet():
    wallet = request.args.get('wallet')
    if not wallet:
        return jsonify({"error": "wallet required"}), 400
    
    for key, value in VOTERS_DB.items():
        voter = json.loads(value.decode())
        if voter.get('wallet_address') == wallet:
            return jsonify({
                "registered": True,
                "voter_id": voter['voter_id'],
                "has_voted": voter['has_voted'] == 1,
                "choice": voter.get('choice')
            })
    
    return jsonify({"registered": False})

@app.route('/vote/cast', methods=['POST'])
def cast_vote():
    data = request.json
    voter_id = data.get('voter_id')
    choice = data.get('choice')
    priv_key = data.get('private_key')
    
    key = voter_id.encode()
    if key not in VOTERS_DB:
        return jsonify({"error": "Invalid voter"}), 404
    
    voter = json.loads(VOTERS_DB[key].decode())
    
    if voter.get('private_key') != priv_key:
        return jsonify({"error": "Invalid private key"}), 401
    
    if voter.get('has_voted') == 1:
        return jsonify({"error": "Already voted"}), 400
    
    voter['has_voted'] = 1
    voter['choice'] = choice
    VOTERS_DB[key] = json.dumps(voter).encode()
    
    return jsonify({"success": True, "message": f"Voted for {choice}"})

@app.route('/vote/results', methods=['GET'])
def vote_results():
    votes = {}
    for key, value in VOTERS_DB.items():
        voter = json.loads(value.decode())
        if voter.get('has_voted') == 1:
            choice = voter.get('choice')
            votes[choice] = votes.get(choice, 0) + 1
    
    total = sum(votes.values())
    return jsonify({"votes": votes, "total": total})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8084, debug=False)
