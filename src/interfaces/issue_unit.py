from .instruction import Instruction
from .register_interface import RegisterFile
from ..execution.timing_tracker import TimingTracker

class IssueUnit:
    """
    Issues one instruction per cycle, reads registers, and records the issue cycle
    """
    def __init__(self, instructions, register_file, timing_tracker):
        self._instructions = instructions
        self._register_file = register_file
        self._next_index = 0  # index of the next instruction to issue
        self._issued_instructions = []  # track issued instructions
        self._timing_tracker = timing_tracker

    def issue_next(self, cycle):
        """
        Issue the next instruction in the list.

        args:
            cycle: current cycle number.

        returns:
            instruction: the issued instruction, or None if all issued.
        """
        if self._next_index >= len(self._instructions):
            return None  # nothing left to issue
        
        instr = self._instructions[self._next_index]
        instr.set_issue_cycle(cycle)

        # UPDATE TIMING TRACKER
        self._timing_tracker.record_issue(instr.get_instr_id(), cycle)

        rA_val = self._register_file.read(instr.get_rA()) if instr.get_rA() is not None else None
        rB_val = self._register_file.read(instr.get_rB()) if instr.get_rB() is not None else None
        rC_val = self._register_file.read(instr.get_rC()) if instr.get_rC() is not None else None
        # PART 2 SHOULD HANDLE REGISTER RENAMING !

        # print(f"[Cycle {cycle}] Issued {instr.get_name()} | rA = {rA_val} rB = {rB_val} rC = {rC_val} immediate = {instr.get_immediate()} label = {instr.get_label()}")

        self._issued_instructions.append(instr)
        self._next_index += 1

        return instr
    
    def has_instructions(self):
        """Check if there are instructions left to issue."""
        return self._next_index < len(self._instructions)

    def get_issued_instructions(self):
        """Return list of instructions already issued."""
        return self._issued_instructions