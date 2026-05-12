"""Script builder for P2WSH and other script operations"""
from typing import List

class ScriptBuilder:
    """Build Bitcoin-style scripts"""
    
    OPCODES = {
        'OP_0': 0x00,
        'OP_CHECKMULTISIG': 0xae,
    }
    
    def __init__(self):
        self.script = bytearray()
    
    def append_number(self, num: int) -> 'ScriptBuilder':
        """Append a number to script"""
        if num == 0:
            self.script.append(0x00)
        elif 1 <= num <= 16:
            self.script.append(0x50 + num)
        else:
            self.script.append(num.to_bytes(1, 'little'))
        return self
    
    def append_data(self, data: bytes) -> 'ScriptBuilder':
        """Append data with length prefix"""
        self.script.append(len(data))
        self.script.extend(data)
        return self
    
    def append_opcode(self, opcode: str) -> 'ScriptBuilder':
        """Append an opcode"""
        self.script.append(self.OPCODES.get(opcode, 0))
        return self
    
    def build(self) -> bytes:
        """Return the built script"""
        return bytes(self.script)
