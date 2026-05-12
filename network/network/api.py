
@app.route('/api/sync/block/<int:height>', methods=['GET'])
def sync_block():
    """Get block by height for syncing"""
    conn = sqlite3.connect('ekush_chain.db')
    cursor = conn.execute('SELECT idx, hash, previous_hash, validator, timestamp FROM blocks WHERE idx = ?', (height,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'error': 'Block not found'}), 404
    
    return jsonify({
        'idx': row[0],
        'hash': row[1],
        'previous_hash': row[2],
        'validator': row[3],
        'timestamp': row[4]
    })
