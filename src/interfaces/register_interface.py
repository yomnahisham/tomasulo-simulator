"""16-bit Register File (8 registers)"""

class RegisterFile:
    def __init__(self):
        self._registers = [0] * 8 # 8 registers, all initialized to 0


    def read(self, register: int) -> int:
        """
        Read value from register
        
        args:
            register: register number (0-7)
            
        returns:
            16-bit register value (R0 always returns 0)
        """
        if (register < 0 or register > 7):
            raise ValueError(f"Invalid register index: {register}")
        
        return self._registers[register]
    
    def write(self, register, value):
        """
        Write value to register
        
        args:
            register: register number (0-7)
            value: value to be stored
        """
        if (register < 0 or register > 7):
            raise ValueError(f"Invalid register index: {register}")
        
        if register != 0: # ignore write if register is 0 
            self._registers[register] = value & 0xFFFF # keep value in 16 bits

    def dump(self):
        """
        Return the full register file (for debugging purposes)
        """
        return self._registers
