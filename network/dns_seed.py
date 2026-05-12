import socket
import dns.resolver
import random

class DNSSeed:
    SEED_DOMAINS = [
        'seed.everestkush.io',
        'dnsseed.everestkush.io',
        'seed.ekush.network'
    ]
    
    @classmethod
    def get_seeds(cls):
        seeds = []
        for domain in cls.SEED_DOMAINS:
            try:
                answers = dns.resolver.resolve(domain, 'A')
                for rdata in answers:
                    seeds.append(f"{rdata.address}:8334")
                print(f"[DNS] Found {len(answers)} seeds from {domain}")
            except:
                print(f"[DNS] Failed to resolve {domain}")
        
        if not seeds:
            seeds = ['103.74.15.88:8334', '192.168.23.5:8334']
            print("[DNS] Using fallback seeds")
        
        random.shuffle(seeds)
        return seeds
