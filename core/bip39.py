"""
BIP39: Mnemonic Seed Phrases
Purpose: Convert complex private keys into simple 12/24 word phrases

Example:
    Input:  "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    Output: Master Seed -> All wallets
"""

from mnemonic import Mnemonic
import hashlib

class BIP39:
    """BIP39 Standard - Human-readable wallet backup"""
    
    @staticmethod
    def generate(strength=128, language='english'):
        """
        Generate a new mnemonic phrase
        
        strength: 128 = 12 words, 256 = 24 words
        language: english, spanish, french, chinese_simplified, japanese
        
        Example: "abandon abandon abandon..."
        """
        mnemo = Mnemonic(language)
        mnemonic = mnemo.generate(strength=strength)
        
        # Calculate word count (12, 15, 18, 21, or 24)
        word_count = len(mnemonic.split())
        
        return {
            "mnemonic": mnemonic,
            "word_count": word_count,
            "strength": strength,
            "language": language
        }
    
    @staticmethod
    def to_seed(mnemonic, passphrase=""):
        """
        Convert mnemonic to master seed
        This seed is the root of ALL wallets
        """
        mnemo = Mnemonic('english')
        seed = mnemo.to_seed(mnemonic, passphrase)
        return seed.hex()
    
    @staticmethod
    def validate(mnemonic):
        """Check if mnemonic is valid"""
        mnemo = Mnemonic('english')
        return mnemo.check(mnemonic)
    
    @staticmethod
    def get_word_list(language='english'):
        """Get all BIP39 words (2048 words)"""
        mnemo = Mnemonic(language)
        return mnemo.wordlist
