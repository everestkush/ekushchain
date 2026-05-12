
# Start P2P Manager for blockchain sync
from network.p2p_manager import P2PManager
p2p_manager = P2PManager()
p2p_manager.start()
print("✅ P2P Manager started - syncing with peers")
