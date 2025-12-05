"""tomasulo core interface - to be implemented by Part 2"""

from typing import Dict, Any, List, Optional


def get_ready_rs_entries() -> List[Dict[str, Any]]:
    """
    get list of RS entries that have ready operands and are not yet executing
    
    returns:
        list of RS entry dictionaries, each containing:
            - id: RS entry id
            - instruction: instruction data structure
            - other RS entry fields
            
    note:
        this function is to be implemented by Part 2 (tomasulo core)
    """
    pass  # implemented by Part 2


def get_rs_operands(rs_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    get operand values and dependencies for an RS entry
    
    args:
        rs_entry: RS entry dictionary
        
    returns:
        dictionary with operand values:
            - Vj: value of first operand (if ready)
            - Vk: value of second operand (if ready)
            - Qj: ROB index producing first operand (if not ready)
            - Qk: ROB index producing second operand (if not ready)
            - immediate: immediate value if applicable
            - pc: program counter value if applicable
            
    note:
        this function is to be implemented by Part 2 (tomasulo core)
    """
    pass  # implemented by Part 2


def update_rob_value(rob_index: int, value: Any) -> None:
    """
    update ROB entry with computed result value
    
    args:
        rob_index: ROB entry index
        value: computed result value
        
    note:
        this function is to be implemented by Part 2 (tomasulo core)
    """
    pass  # implemented by Part 2


def forward_to_rs(rob_index: int, value: Any) -> None:
    """
    forward result value to waiting RS entries
    
    args:
        rob_index: ROB index that produced the value
        value: result value to forward
        
    note:
        this function is to be implemented by Part 2 (tomasulo core)
        should update Qj/Qk in RS entries that are waiting for this ROB index
    """
    pass  # implemented by Part 2


def update_rat(rob_index: int, value: Any) -> None:
    """
    update RAT if mapping is still active
    
    args:
        rob_index: ROB index that produced the value
        value: result value
        
    note:
        this function is to be implemented by Part 2 (tomasulo core)
        should update RAT entry if it still points to this ROB index
    """
    pass  # implemented by Part 2


def notify_branch_result(rob_index: int, taken: bool, target: int) -> None:
    """
    notify tomasulo core of branch outcome for misprediction handling
    
    args:
        rob_index: ROB index of the branch instruction
        taken: whether branch was actually taken
        target: actual target address
        
    note:
        this function is to be implemented by Part 2 (tomasulo core)
        Part 2 should check for misprediction and handle flush if needed
    """
    pass  # implemented by Part 2


def mark_rs_executing(rs_entry_id: int) -> None:
    """
    mark RS entry as executing
    
    args:
        rs_entry_id: RS entry id
        
    note:
        this function is to be implemented by Part 2 (tomasulo core)
    """
    pass  # implemented by Part 2


def get_oldest_ready_rob_index() -> Optional[int]:
    """
    get oldest ROB index for CDB arbitration
    
    returns:
        oldest ROB index that has a ready result, or None
        
    note:
        this function is to be implemented by Part 2 (tomasulo core)
    """
    pass  # implemented by Part 2

