"""JSON-RPC 2.0 Server with Bitcoin Core method names"""
import json
import logging
from flask import Flask, request, jsonify

logger = logging.getLogger(__name__)

def create_rpc_server(get_height_func, get_balance_func, send_tx_func):
    """Create Bitcoin Core compatible JSON-RPC server"""
    app = Flask(__name__)
    
    @app.route('/json-rpc', methods=['POST'])
    def json_rpc():
        data = request.json
        
        if data.get('jsonrpc') != '2.0':
            return jsonify({'error': 'Invalid JSON-RPC version'}), 400
        
        method = data.get('method')
        params = data.get('params', [])
        req_id = data.get('id')
        
        handlers = {
            'getblockchaininfo': lambda: {
                'chain': 'main',
                'blocks': get_height_func(),
                'headers': get_height_func(),
                'bestblockhash': get_best_hash(),
                'difficulty': get_difficulty(),
                'mediantime': int(time.time()),
                'verificationprogress': 0.999,
                'chainwork': get_chain_work()
            },
            'getbalance': lambda: get_balance_func(),
            'sendrawtransaction': lambda: send_tx_func(params[0] if params else ''),
            'getnewaddress': lambda: generate_new_address(),
        }
        
        if method not in handlers:
            return jsonify({
                'jsonrpc': '2.0',
                'error': {'code': -32601, 'message': 'Method not found'},
                'id': req_id
            })
        
        try:
            result = handlers[method]()
            return jsonify({'jsonrpc': '2.0', 'result': result, 'id': req_id})
        except Exception as e:
            return jsonify({
                'jsonrpc': '2.0',
                'error': {'code': -32000, 'message': str(e)},
                'id': req_id
            })
    
    return app

# Helper functions (replace with your actual implementations)
def get_best_hash():
    return "0" * 64

def get_difficulty():
    return 1.0

def get_chain_work():
    return "0"

def generate_new_address():
    return "EKush" + "1" * 33
