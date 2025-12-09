class Instruction:
    def __init__(self, name, rA = None, rB = None, rC = None, immediate = None, label = None, instr_id = None):
        """
        Represents a single instruction.
        """
        self._name = name
        self._rA = rA
        self._rB = rB
        self._rC = rC
        self._immediate = immediate
        self._label = label
        self._issue_cycle = None
        self._instr_id = instr_id

    def get_name(self):
        return self._name

    def get_rA(self):
        return self._rA

    def get_rB(self):
        return self._rB

    def get_rC(self):
        return self._rC

    def get_immediate(self):
        return self._immediate

    def get_label(self):
        return self._label

    def get_issue_cycle(self):
        return self._issue_cycle
    
    def get_instr_id(self):
        return self._instr_id

    def set_issue_cycle(self, cycle):
        self._issue_cycle = cycle

    def set_instr_id(self, instr_id):
        self._instr_id = instr_id
    
    def __str__(self):
        """Return a readable string representation of the instruction."""
        parts = [self._name]
        
        # Add registers
        if self._rA is not None:
            parts.append(f"R{self._rA}")
        if self._rB is not None:
            parts.append(f"R{self._rB}")
        if self._rC is not None:
            parts.append(f"R{self._rC}")
        
        # Add immediate if present
        if self._immediate is not None:
            parts.append(f"#{self._immediate}")
        
        # Add label if present
        if self._label is not None:
            parts.append(self._label)
        
        return " ".join(parts)
    
    def __repr__(self):
        """Return a detailed representation for debugging."""
        return f"Instruction({self.__str__()})"