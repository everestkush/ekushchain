"""
DNS Seeds - Auto Peer Discovery (Bitcoin Standard)
Allows new nodes to find peers without manual configuration
"""

import socket
import dns.resolver
import json
import os

# Hardcoded DNS seeds (like Bitcoin)
DNS_SEEDS = [
    "seed.everestkush.com",      # Primary seed
    "seed1.everestkush.com",     # Backup seed 1
    "seed2.everestkush.com",     # Backup seed 2
    "seed3.everestkush.com",     # Backup seed 3
]

# Fallback hardcoded nodes (in case DNS fails)
FALLBACK_NODES = [
    "http://192.168.23.5:5000",  # Machine A (Kathmandu)
    "http://192.168.23.4:5000",  # Machine B (Pokhara)
]

class DNSSeeds:
    def __init__(self):
        self.discovered_peers = []
    
    def query_dns_seed(self, seed_domain):
        """
        Query a DNS seed to get peer IP addresses
        Returns list of IP addresses
        """
        try:
            print(f"[P2P] Querying DNS seed: {seed_domain}")
            answers = dns.resolver.resolve(seed_domain, 'A')
            ips = [str(answer) for answer in answers]
            print(f"   Found {len(ips)} peers from {seed_domain}")
            return ips
        except Exception as e:
            print(f"   DNS seed {seed_domain} failed: {e}")
            return []
    
    def discover_peers(self):
        """
        Discover peers from all DNS seeds
        Returns list of peer URLs
        """
        all_ips = []
        
        # Query all DNS seeds
        for seed in DNS_SEEDS:
            ips = self.query_dns_seed(seed)
            all_ips.extend(ips)
        
        # Remove duplicates
        all_ips = list(set(all_ips))
        
        # Convert IPs to peer URLs
        peers = [f"http://{ip}:5000" for ip in all_ips]
        
        # Add fallback nodes if no peers found
        if not peers:
            print("[WARN] No DNS peers found, using fallback nodes")
            peers = FALLBACK_NODES
        
        self.discovered_peers = peers
        print(f"[OK] Discovered {len(peers)} total peers")
        return peers
    
    def get_peer_urls(self):
        """Return discovered peer URLs as list"""
        return self.discovered_peers if self.discovered_peers else FALLBACK_NODES
