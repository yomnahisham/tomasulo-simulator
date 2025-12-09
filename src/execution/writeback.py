"""write-back stage implementation"""

from typing import Dict, Any, Optional
from .cdb import CDB


class WriteBackStage:
    """handles write-back of execution results"""
    
    def __init__(self, cdb: CDB, tomasulo_interface, memory_interface):
        """
        initialize write-back stage
        
        args:
            cdb: common data bus instance
            tomasulo_interface: interface to Part 2 (RS/ROB/RAT)
            memory_interface: interface to Part 1 (memory)
        """
        self.cdb = cdb
        self.tomasulo_interface = tomasulo_interface
        self.memory_interface = memory_interface
        self.write_queue = []  # queue of results waiting to be written back
    
    def add_result(self, rob_index: int, value: Any, instruction_type: str, instruction: Dict[str, Any], rs_entry_id: str) -> None:
        """
        add a finished execution result to write-back queue
        
        args:
            rob_index: ROB entry index
            value: computed result value
            instruction_type: type of instruction
            instruction: instruction data structure
            rs_entry_id: reservation station entry id
        """
        self.write_queue.append({
            "rob_index": rob_index,
            "value": value,
            "instruction_type": instruction_type,
            "instruction": instruction,
            "rs_entry_id": rs_entry_id,
        })
    
    def process_write_back(self, current_cycle: int, timing_tracker) -> None:
        """
        process write-back for this cycle (one per cycle via CDB)
        
        args:
            current_cycle: current simulation cycle
            timing_tracker: timing tracker instance
        """
        if not self.write_queue:
            return
        
        # arbitration: get oldest ROB entry
        # try to use Part 2's arbitration function if available
        oldest_rob = None
        if hasattr(self.tomasulo_interface, 'get_oldest_ready_rob_index'):
            oldest_rob = self.tomasulo_interface.get_oldest_ready_rob_index()
        
        if oldest_rob is not None:
            # find result with this ROB index
            result = None
            for i, r in enumerate(self.write_queue):
                if r["rob_index"] == oldest_rob:
                    result = self.write_queue.pop(i)
                    break
            if result is None:
                # fallback to sorting if oldest not found
                self.write_queue.sort(key=lambda x: x["rob_index"])
                result = self.write_queue.pop(0)
        else:
            # fallback: sort by ROB index (assuming lower index = older)
            self.write_queue.sort(key=lambda x: x["rob_index"])
            result = self.write_queue.pop(0)
        rob_index = result["rob_index"]
        value = result["value"]
        inst_type = result["instruction_type"]
        instruction = result["instruction"]
        rs_entry_id = result["rs_entry_id"]
        
        # try to broadcast on CDB
        if self.cdb.broadcast(rob_index, value, inst_type):
            # handle STORE memory write (STORE doesn't produce register result)
            if inst_type == "STORE":
                # for STORE, value is a dict with "address" and "value" keys
                if isinstance(value, dict):
                    store_address = value.get("address", 0)
                    store_value = value.get("value", 0)
                    self.handle_store_write(store_address, store_value)
                else:
                    # fallback: assume value is address, try to get store value from instruction
                    store_address = value
                    store_value = instruction.get("store_value", 0)
                    self.handle_store_write(store_address, store_value)
                
                # STORE doesn't update ROB/RAT/RS with a value, just marks completion
                # Part 2 will handle marking STORE as ready in ROB
                self.tomasulo_interface.update_rob_value(rob_index, None)  # None indicates STORE completion
            else:
                # for other instructions, update ROB, forward to RS, update RAT
                self.tomasulo_interface.update_rob_value(rob_index, value)
                self.tomasulo_interface.forward_to_rs(rob_index, value)
                self.tomasulo_interface.update_rat(rob_index, value)
            
            # record write cycle timing
            if timing_tracker:
                timing_tracker.record_write(instruction.get("instr_id"), current_cycle)
            
            # clear the reservation station entry after successful writeback
            if rs_entry_id is not None:
                self.tomasulo_interface.clear_rs_entry(rs_entry_id) 
    
    def handle_store_write(self, address: int, value: int) -> None:
        """
        handle memory write for STORE instruction
        
        args:
            address: memory address to write to
            value: value to write
        """
        self.memory_interface.write_memory(address, value)
    
    def get_queue_length(self) -> int:
        """
        get number of results waiting in write-back queue
        
        returns:
            number of queued results
        """
        return len(self.write_queue)

