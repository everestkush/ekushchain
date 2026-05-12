"""
Kademlia-based P2P Node Discovery
"""
import asyncio
import hashlib
from typing import List, Tuple
import random

class KademliaNode:
    """Kademlia DHT for peer discovery"""
    
    def __init__(self, node_id: str, host: str, port: int):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.k_buckets = [[] for _ in range(160)]  # 160-bit keyspace
        self.routing_table = {}
    
    def distance(self, id1: str, id2: str) -> int:
        """XOR distance between two node IDs"""
        return int(id1, 16) ^ int(id2, 16)
    
    def find_node(self, target_id: str) -> List[Tuple]:
        """Find closest nodes to target"""
        distances = [(node, self.distance(node[0], target_id)) 
                     for node in self.get_all_peers()]
        distances.sort(key=lambda x: x[1])
        return [node for node, _ in distances[:20]]
    
    def bootstrap(self, seed_nodes: List[Tuple[str, int]]):
        """Join the network via seed nodes"""
        for host, port in seed_nodes:
            self.ping(host, port)
    
    def ping(self, host: str, port: int) -> bool:
        """Ping a node to check if alive"""
        # Implement UDP ping
        return True
    
    def get_all_peers(self) -> List[Tuple[str, int, str]]:
        """Get all known peers"""
        peers = []
        for bucket in self.k_buckets:
            peers.extend(bucket)
        return peers

async def start_discovery():
    """Start P2P discovery service"""
    node_id = hashlib.sha256(secrets.token_bytes(32)).hexdigest()
    node = KademliaNode(node_id, '0.0.0.0', 8334)
    
    # Bootstrap from known peers
    seed_peers = [
        ('103.74.15.88', 8334),  # Your node
        # Add more seed peers here
    ]
    
    node.bootstrap(seed_peers)
    print(f"✅ P2P Discovery started. Node ID: {node_id[:16]}...")
    
    return node

if __name__ == "__main__":
    asyncio.run(start_discovery())
