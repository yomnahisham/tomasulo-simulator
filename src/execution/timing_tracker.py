"""track execution timing per instruction"""

from typing import Dict, Optional


class TimingTracker:
    """tracks execution timing for all instructions"""
    
    def __init__(self):
        """initialize timing tracker"""
        # maps instruction_id -> timing info
        self.timing = {}
    
    def record_issue(self, instr_id: int, cycle: int) -> None:
        """
        record issue cycle for an instruction
        
        args:
            instr_id: instruction identifier
            cycle: issue cycle number
        """
        if instr_id not in self.timing:
            self.timing[instr_id] = {
                "issue": cycle,
                "start_exec": None,
                "finish_exec": None,
                "write": None,
                "commit": None,
            }
        else:
            self.timing[instr_id]["issue"] = cycle
    
    def record_start_exec(self, instr_id: int, cycle: int) -> None:
        """
        record start execution cycle
        
        args:
            instr_id: instruction identifier
            cycle: start execution cycle number
        """
        if instr_id not in self.timing:
            self.timing[instr_id] = {
                "issue": None,
                "start_exec": cycle,
                "finish_exec": None,
                "write": None,
                "commit": None,
            }
        else:
            self.timing[instr_id]["start_exec"] = cycle
    
    def record_finish_exec(self, instr_id: int, cycle: int) -> None:
        """
        record finish execution cycle
        
        args:
            instr_id: instruction identifier
            cycle: finish execution cycle number
        """
        if instr_id not in self.timing:
            self.timing[instr_id] = {
                "issue": None,
                "start_exec": None,
                "finish_exec": cycle,
                "write": None,
                "commit": None,
            }
        else:
            self.timing[instr_id]["finish_exec"] = cycle
    
    def record_write(self, instr_id: int, cycle: int) -> None:
        """
        record write cycle
        
        args:
            instr_id: instruction identifier
            cycle: write cycle number
        """
        if instr_id not in self.timing:
            self.timing[instr_id] = {
                "issue": None,
                "start_exec": None,
                "finish_exec": None,
                "write": cycle,
                "commit": None,
            }
        else:
            self.timing[instr_id]["write"] = cycle
    
    def record_commit(self, instr_id: int, cycle: int) -> None:
        """
        record commit cycle (called by Part 2, but we track it)
        
        args:
            instr_id: instruction identifier
            cycle: commit cycle number
        """
        if instr_id not in self.timing:
            self.timing[instr_id] = {
                "issue": None,
                "start_exec": None,
                "finish_exec": None,
                "write": None,
                "commit": cycle,
            }
        else:
            self.timing[instr_id]["commit"] = cycle
    
    def get_timing(self, instr_id: int) -> Optional[Dict[str, Optional[int]]]:
        """
        get timing information for an instruction
        
        args:
            instr_id: instruction identifier
            
        returns:
            dictionary with timing info or None if not found
        """
        return self.timing.get(instr_id)
    
    def get_all_timing(self) -> Dict[int, Dict[str, Optional[int]]]:
        """
        get timing information for all instructions
        
        returns:
            dictionary mapping instr_id to timing info
        """
        return self.timing.copy()
    
    def clear(self) -> None:
        """clear all timing data"""
        self.timing = {}


