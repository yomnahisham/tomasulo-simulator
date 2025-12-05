"""common data bus implementation"""

from typing import Optional, Tuple, Any


class CDB:
    """common data bus - only one write-back per cycle"""
    
    def __init__(self):
        """initialize CDB"""
        self.current_broadcast = None  # (rob_index, value, instruction_type)
        self.is_busy = False
        self.pending_broadcasts = []  # queue for when multiple finish same cycle
    
    def broadcast(self, rob_index: int, value: Any, instruction_type: str) -> bool:
        """
        attempt to broadcast a result on the CDB
        
        args:
            rob_index: ROB entry index
            value: result value to broadcast
            instruction_type: type of instruction
            
        returns:
            True if broadcast succeeded, False if CDB already busy
        """
        if self.is_busy:
            # queue for next cycle
            self.pending_broadcasts.append((rob_index, value, instruction_type))
            return False
        
        self.current_broadcast = (rob_index, value, instruction_type)
        self.is_busy = True
        return True
    
    def get_broadcast(self) -> Optional[Tuple[int, Any, str]]:
        """
        get current broadcast data
        
        returns:
            tuple of (rob_index, value, instruction_type) or None
        """
        return self.current_broadcast
    
    def clear(self) -> None:
        """clear CDB after cycle (pending broadcasts handled in next write-back stage)"""
        self.current_broadcast = None
        self.is_busy = False
        # note: pending broadcasts remain in queue and will be processed
        # in the next cycle's write-back stage
    
    def has_broadcast(self) -> bool:
        """
        check if CDB is currently broadcasting
        
        returns:
            True if broadcasting, False otherwise
        """
        return self.is_busy
    
    def get_state(self) -> dict:
        """
        get current CDB state for GUI visualization
        
        returns:
            dictionary with CDB state information
        """
        if self.current_broadcast:
            rob_index, value, inst_type = self.current_broadcast
            return {
                "busy": True,
                "rob_index": rob_index,
                "value": value,
                "instruction_type": inst_type,
                "pending_count": len(self.pending_broadcasts),
            }
        else:
            return {
                "busy": False,
                "rob_index": None,
                "value": None,
                "instruction_type": None,
                "pending_count": len(self.pending_broadcasts),
            }

