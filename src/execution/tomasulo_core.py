from typing import Dict, Any, List, Optional
from .reservation_station import ReservationStation, LoadRS, StoreRS, ALURS, CALLRS
from .rob import ReorderBuffer
from .rat import RAT

class ExecutionCore:
    def __init__(self):
        self.reservation_stations = {
            'LOAD1': LoadRS(),
            'LOAD2': LoadRS(),
            'STORE': StoreRS(),
            'BEQ1': ALURS(),
            'BEQ2': ALURS(),
            'CALL/RET': CALLRS(),
            'ADD/SUB1': ALURS(),
            'ADD/SUB2': ALURS(),
            'ADD/SUB3': ALURS(),
            'ADD/SUB4': ALURS(),
            'NAND': ALURS(),
            'MUL': ALURS()
        }
        self.rob = ReorderBuffer()
        self.rat = RAT(8) 

    def get_ready_rs_entries(self) -> List[Dict[str, Any]]:
        """    returns:
        list of RS entry dictionaries, each containing:
            - id: RS entry id
            - instruction: instruction data structure
            - other RS entry fields"""
        ready_rs_entries = []
        excluded_fields = {"Op", "busy", "state"}
        for rs_name, rs in self.reservation_stations.items():
            if rs.is_ready() and not rs.is_executing():
                entry = {k: rs.__dict__[k] for k in rs.__dict__ if k not in excluded_fields}
                entry['id'] = rs_name
                ready_rs_entries.append(entry)
        return ready_rs_entries
    
    def get_rs_operands(self, rs_entry: ReservationStation) -> Dict[str, Any]:
        """    args:
            rs_entry: RS entry dictionary
            
            returns:
                dictionary with operand values:
                    - Vj: value of first operand (if ready) 
                    - Vk: value of second operand (if ready)
                    - Qj: ROB index producing first operand (if not ready)
                    - Qk: ROB index producing second operand (if not ready)
                    - immediate: immediate value if applicable
                    - pc: program counter value if applicable"""
        excluded_fields = {"Op", "busy", "state"}
        dictionnary = {k: rs_entry.__dict__[k] for k in rs_entry.__dict__ if k not in excluded_fields and rs_entry.__dict__[k] is not None}
        return dictionnary
    
    def update_rob_value(self, rob_index: int, value: Any) -> None:
        """
        update ROB entry with computed result value
        
        args:
            rob_index: ROB entry index
            value: computed result value
        """
        self.rob.update(rob_index, value)

    def forward_to_rs(self, rob_index: int, value: Any) -> None:
        """
        forward result value to waiting RS entries
        
        args:
            rob_index: ROB index that produced the value
            value: result value to forward
            
        note:
            should update Qj/Qk in RS entries that are waiting for this ROB index
        """
        for rs in self.reservation_stations.values():
            if hasattr(rs, 'Qj') and not hasattr(rs, 'Qk') and rs.Qj == self.rob.buffer.at(rob_index).dest:
                print(f"Forwarding to RS with single source: {rs}")
                rs.source_update(value)
            else:
                if hasattr(rs, 'Qj') and rs.Qj == self.rob.buffer.at(rob_index).dest:
                    print(f"Forwarding to RS source1: {rs}")
                    rs.source1_update(value)
                if hasattr(rs, 'Qk') and rs.Qk == self.rob.buffer.at(rob_index).dest:
                    print(f"Forwarding to RS source2: {rs}")
                    rs.source2_update(value)
    
    def update_rat(self, rob_index: int, value: Any) -> None:
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

    def notify_branch_result(self, rob_index: int, taken: bool, target: int) -> None:
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

    def mark_rs_executing(self, rs_entry_id: str) -> None:
        """
        mark RS entry as executing
        
        args:
            rs_entry_id: RS entry id (string key)
        """
        self.reservation_stations[rs_entry_id].change_state("EXECUTING")

    def get_oldest_ready_rob_index(self) -> Optional[int]:
        """
        get oldest ROB index for CDB arbitration
        
        returns:
            oldest ROB index that has a ready result, or None
            
        note:
            this function is to be implemented by Part 2 (tomasulo core)
        """
        return self.rob.buffer.head


if __name__ == "__main__":
    core = ExecutionCore()
    core.rob.push(type="ALU", dest=0)
    core.rob.update(0, 42)
    core.rob.push(type="LOAD", dest=1)
    core.rob.update(1, 84)
    core.rob.push(type="LOAD", dest=2)
    core.rob.update(2, 84)
    core.rob.push(type="LOAD", dest=3)
    core.rob.update(3, 84)
    core.rob.push(type="LOAD", dest=4)
    core.rob.update(4, 84)
    core.rob.push(type="LOAD", dest=5)
    core.rob.update(5, 84)
    core.rob.push(type="ALU", dest=6)
    core.rob.update(6, 42)
    core.rob.push(type="LOAD", dest=7)
    core.rob.update(7, 84)
    print(core.get_oldest_ready_rob_index())
    core.rob.pop()
    print(core.get_oldest_ready_rob_index())
    core.rob.push(type="LOAD", dest=7)
    core.rob.update(7, 84)
    print(core.get_oldest_ready_rob_index())
