"""reservation stations for storing instructions before execution."""
from ..interfaces.instruction import Instruction

class ReservationStation:
    """Base class for reservation stations"""
    def __init__(self):
        self.Op = None
        self.busy = False
        self.instruction = None
        self.state = None # 'EMPTY', 'ISSUED', 'EXECUTING', 'COMPLETED'
        self.dest = None
    
    def is_busy(self) -> bool:
        """
        Check if the RS is busy
        
        returns:
            True if busy, False otherwise
        """
        return self.busy
    
    def change_state(self, new_state: str) -> None:
        """ 
        Change the state of the RS
        args:
            new_state: new state string
        """
        self.state = new_state
    
    def is_issued(self) -> bool:
        """
        Check if the RS is in ISSUED state

        returns:
            True if in ISSUED state, False otherwise
        """
        return self.state == 'ISSUED' and self.busy
    
    def is_executing(self) -> bool:
        """
        Check if the RS is in EXECUTING state

        returns:
            True if in EXECUTING state, False otherwise
        """
        return self.state == 'EXECUTING' and self.busy
    
    def is_completed(self) -> bool:
        """
        Check if the RS is in COMPLETED state

        returns:
            True if in COMPLETED state, False otherwise
        """
        return self.state == 'COMPLETED' and self.busy
    
    
        
class LoadRS(ReservationStation):
    """Load Reservation Station"""
    def __init__(self):
        super().__init__()
        self.Vj = None
        self.Qj = None
        self.A = None
    
    def push(self, instruction: Instruction, A, dest, Vj=None, Qj=None) -> None:
        """
        Push a new instruction into the LoadRS
        
        args:
            instruction: instruction data structure
            A: base address
            Vj: value of base register (if ready)
            Qj: ROB index producing base register (if not ready)
        """
        if self.busy:
            raise Exception("LoadRS is already busy")
        if Vj is not None and Qj is not None:
            raise Exception("Both Vj and Qj cannot be valid")
        if Vj is None and Qj is None:
            raise Exception("Either Vj or Qj must be valid")
        self.instruction = instruction
        self.Op = 'LOAD'
        self.busy = True
        self.Vj = Vj
        self.Qj = Qj
        self.A = A
        self.dest = dest

    def is_ready(self) -> bool:
        """
        Check if the source operand is ready

        returns:
            True if ready, False otherwise
        """
        return self.busy and self.Qj is None
    
    def source_update(self, value: int) -> None:
        """  
        Update the source operand when it becomes ready

        args:
            value: value of the source operand
        """
        self.Vj = value
        self.Qj = None
    
    def compute_address(self) -> int:
        """  
        Compute the effective address for the load instruction
        returns:
            effective address
        """
        if self.Vj is None:
            raise Exception("Source operand not ready")
        self.Vj = None
        self.A = self.Vj + self.A
        return self.A

    def pop(self) -> None:
        """   
        Clear the RS entry
        """
        self.instruction = None
        self.Op = None
        self.busy = False
        self.state = None  # Reset state
        self.dest = None  # Reset dest
        self.Vj = None
        self.Qj = None
        self.A = None

class StoreRS(ReservationStation):
    """Store Reservation Station"""
    def __init__(self):
        super().__init__()
        self.Vj = None
        self.Qj = None
        self.Vk = None
        self.Qk = None
        self.A = None
    
    def push(self, instruction: Instruction, A, dest, Vj=None, Qj=None, Vk=None, Qk=None) -> None:
        """
        Push a new instruction into the StoreRS
        
        args:
            instruction: instruction data structure
            A: base address
            Vj: value of base register (if ready)
            Qj: ROB index producing base register (if not ready)
            Vk: value of source register (if ready)
            Qk: ROB index producing source register (if not ready)
        """
        if self.busy:
            raise Exception("StoreRS is already busy")
        if (Vj is not None and Qj is not None):
            raise Exception("Both Vj and Qj cannot be valid")
        if (Vk is not None and Qk is not None):
            raise Exception("Both Vk and Qk cannot be valid")
        if Vj is None and Qj is None:
            raise Exception("Either Vj or Qj must be valid")
        self.instruction = instruction
        self.Op = 'STORE'
        self.busy = True
        self.Vj = Vj
        self.Qj = Qj
        self.Vk = Vk
        self.Qk = Qk
        self.A = A
        self.dest = dest

    def is_ready(self) -> bool:
        """
        Check if both source operands are ready
        
        returns:
            True if ready, False otherwise
        """
        return self.busy and self.Qj is None and self.Qk is None
    
    def source1_update(self, value: int) -> None:
        """  
        Update the first source operand when it becomes ready
        args:
            value: value of the first source operand
        """
        self.Vj = value
        self.Qj = None
    
    def source2_update(self, value: int) -> None:
        """
        Update the second source operand when it becomes ready
        args:
            value: value of the second source operand
        """
        self.Vk = value
        self.Qk = None
    
    def compute_address(self) -> int:
        """
        Compute the effective address for the store instruction
        returns:
            effective address
        """
        if self.Vj is None:
            raise Exception("Source operand not ready")
        self.Vj = None
        self.A = self.Vj + self.A
        return self.A

    def pop(self) -> None:
        """
        Clear the RS entry
        """
        self.instruction = None
        self.Op = None
        self.busy = False
        self.state = None  # Reset state
        self.dest = None  # Reset dest
        self.Vj = None
        self.Qj = None
        self.Vk = None
        self.Qk = None
        self.A = None
    
class ALURS(ReservationStation):
    """ALU Operations Reservation Station"""
    def __init__(self):
        super().__init__()
        self.Vj = None
        self.Qj = None
        self.Vk = None
        self.Qk = None
    
    def push(self, instruction: Instruction, Op, dest, Vj=None, Qj=None, Vk=None, Qk=None) -> None:
        """   
        Push a new instruction into the ALURS
        args:
            instruction: instruction data structure
            Op: operation code (e.g., 'ADD', 'SUB', 'NAND', 'MUL')
            Vj: value of first operand (if ready)
            Qj: ROB index producing first operand (if not ready)
            Vk: value of second operand (if ready)
            Qk: ROB index producing second operand (if not ready)
        """
        if self.busy:
            raise Exception("ALURS is already busy")
        if (Vj is not None and Qj is not None):
            raise Exception("Both Vj and Qj cannot be valid")
        if (Vk is not None and Qk is not None):
            raise Exception("Both Vk and Qk cannot be valid")
        if Vj is None and Qj is None:
            raise Exception("Either Vj or Qj must be valid")
        if Vk is None and Qk is None:
            raise Exception("Either Vk or Qk must be valid")
        self.instruction = instruction
        self.Op = Op
        self.busy = True
        self.Vj = Vj
        self.Qj = Qj
        self.Vk = Vk
        self.Qk = Qk
        self.dest = dest

    def is_ready(self) -> bool:
        """  
        Check if both source operands are ready
        
        returns:
            True if ready, False otherwise
        """
        return self.busy and self.Qj is None and self.Qk is None
    
    def source1_update(self, value: int) -> None:
        """
        Update the first source operand when it becomes ready

        args:
            value: value of the first source operand
        """
        self.Vj = value
        self.Qj = None
    
    def source2_update(self, value: int) -> None:
        """
        Update the second source operand when it becomes ready

        args:
            value: value of the second source operand
        """
        self.Vk = value
        self.Qk = None

    def pop(self) -> None:
        """
        Clear the RS entry
        """
        self.instruction = None
        self.Op = None
        self.busy = False
        self.Vj = None
        self.Qj = None
        self.Vk = None
        self.Qk = None

class CALLRS(ReservationStation):
    """CALL and Return Reservation Station"""
    def __init__(self):
        super().__init__()
        self.A = None
        self.Vj = None  # For RET: R1 value
        self.Qj = None  # For RET: ROB index producing R1
        self.PC = None  # Instruction index (PC) for CALL/RET
    
    def push(self, instruction: Instruction, Op: str, dest, A: int, Vj=None, Qj=None, PC=None):
        if self.busy:
            raise Exception("CALLRS is already busy")
        self.instruction = instruction
        self.Op = Op
        self.busy = True
        self.A = A
        self.dest = dest
        self.Vj = Vj
        self.Qj = Qj
        self.PC = PC

    def is_ready(self) -> bool:
        # For CALL: always ready (no operands needed)
        # For RET: ready if R1 is available (Qj is None)
        if self.Op == "RET":
            return self.busy and self.Qj is None
        return self.busy
    
    def source_update(self, value: int) -> None:
        """Update R1 value when it becomes ready (for RET)"""
        self.Vj = value
        self.Qj = None

    def pop(self):
        self.instruction = None
        self.Op = None
        self.busy = False
        self.state = None  # Reset state
        self.dest = None  # Reset dest
        self.A = None  # Reset A
        self.Vj = None
        self.Qj = None
        self.PC = None

class BEQRS(ReservationStation):
    """Branch If Equal Reservation Station"""
    def __init__(self):
        super().__init__()
        self.Vj = None
        self.Qj = None
        self.Vk = None
        self.Qk = None
        self.A = None
    
    def push(self, instruction: Instruction, A, dest, Vj=None, Qj=None, Vk=None, Qk=None) -> None:
        """
        Push a new instruction into the BEQRS

        args:
            instruction: instruction data structure
            Vj: value of first operand (if ready)
            Qj: ROB index producing first operand (if not ready)
            Vk: value of second operand (if ready)
            Qk: ROB index producing second operand (if not ready)
        """
        if self.busy:
            raise Exception("BEQRS is already busy")
        if (Vj is not None and Qj is not None):
            raise Exception("Both Vj and Qj cannot be valid")
        if (Vk is not None and Qk is not None):
            raise Exception("Both Vk and Qk cannot be valid")
        if Vj is None and Qj is None:
            raise Exception("Either Vj or Qj must be valid")
        if Vk is None and Qk is None:
            raise Exception("Either Vk or Qk must be valid")
        self.instruction = instruction
        self.Op = 'BEQ'
        self.busy = True
        self.Vj = Vj
        self.Qj = Qj
        self.Vk = Vk
        self.Qk = Qk
        self.A = A
        self.dest = dest

    def is_ready(self) -> bool:
        """
        Check if both source operands are ready

        returns:
            True if ready, False otherwise
        """
        return self.busy and self.Qj is None and self.Qk is None
    
    def source1_update(self, value: int) -> None:
        """
        Update the first source operand when it becomes ready

        args:
            value: value of the first source operand
        """
        self.Vj = value
        self.Qj = None
    
    def source2_update(self, value: int) -> None:
        """
        Update the second source operand when it becomes ready

        args:
            value: value of the second source operand
        """
        self.Vk = value
        self.Qk = None

    def pop(self):
        """
        Clear the RS entry
        """
        self.instruction = None
        self.Op = None
        self.busy = False
        self.state = None  # Reset state
        self.dest = None  # Reset dest
        self.Vj = None
        self.Qj = None
        self.Vk = None
        self.Qk = None
        self.A = None  # Reset A if it exists

    