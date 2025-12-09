"""16-bit word-addressable memory"""

class Memory:
    def __init__(self):
        self._memory = {}

    def read(self, address):
        """
        Read 16-bit word from memory at given address
        
        args:
            address: memory address (16-bit word addressable)
            
        returns:
            16-bit value from memory
        """
        if address < 0:
            raise ValueError(f"Invalid memory address: {address}")
        
        return self._memory.get(address, 0) # if value at address doesnt exist, we reutrn 0
    
    def write(self, address, value):
        """
        Write 16-bit word to memory at given address
        
        args:
            address: memory address (16-bit word addressable)
            value: 16-bit value to write
        """
        if address < 0:
            raise ValueError(f"Invalid memory address: {address}")
        
        self._memory[address] = value & 0xFFFF # keep value in 16 bits 

    def dump(self):
        """
        Return the full memory (for debugging purposes)
        """
        return self._memory
    
    def read_memory(self, address):
        """
        Alias for read() to match ExecutionManager interface
        """
        return self.read(address)
    
    def write_memory(self, address, value):
        """
        Alias for write() to match ExecutionManager interface
        """
        self.write(address, value)

    

