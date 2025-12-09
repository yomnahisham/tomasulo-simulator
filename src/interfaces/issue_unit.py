from typing import Optional

from execution.rob import ReorderBuffer
from .instruction import Instruction
from .register_interface import RegisterFile
from ..execution.timing_tracker import TimingTracker

class IssueUnit:
    """
    Issues one instruction per cycle, reads registers, and records the issue cycle
    """
    def __init__(self, instructions, register_file: RegisterFile, timing_tracker: TimingTracker, reservation_stations: dict, rob: ReorderBuffer, rat: list):
        self._instructions = instructions
        self._register_file = register_file
        self._next_index = 0  # index of the next instruction to issue
        self._issued_instructions = []  # track issued instructions
        self._timing_tracker = timing_tracker
        self.reservation_stations = reservation_stations
        self.rob = rob
        self.rat = rat

    def rat_mapping(self, reg: int, rob_index: int) -> None:
        """
        map architectural register to ROB index
        
        args:
            reg: register name (e.g., 'R0', 'R1', ...)
            rob_index: ROB index to map to
        """
        self.rat[reg] = rob_index

    def rs_issue(self, instruction: Instruction, rob_index: int) -> tuple[bool, str]:
        """
        issue instruction to appropriate RS
        
        args:
            instruction: instruction to issue
        """
        name = instruction.get_name()
        Vj, Qj, Vk, Qk = self.get_source_operands(instruction)
        if name == "LOAD":
            for rs_name in ['LOAD1', 'LOAD2']:
                if not self.reservation_stations[rs_name].busy:
                    self.reservation_stations[rs_name].push(instruction, A=instruction.get_immediate(), dest=rob_index, Vj=Vj, Qj=Qj)
                    message = (f"Issued {name} to RS {rs_name}")
                    return True, message
            return False, "LOAD RSs are busy"
        elif name == "STORE":
            if not self.reservation_stations['STORE'].busy:
                self.reservation_stations['STORE'].push(instruction, A=instruction.get_immediate(), dest=rob_index, Vj=Vj, Qj=Qj, Vk=Vk, Qk=Qk)
                message = (f"Issued {name} to RS STORE")
                return True, message
            else:
                return False, "STORE RS is busy"
        elif name == "BEQ":
            for rs_name in ['BEQ1', 'BEQ2']:
                if not self.reservation_stations[rs_name].busy:
                    self.reservation_stations[rs_name].push(instruction, A=instruction.get_immediate(), dest=rob_index, Vj=Vj, Qj=Qj, Vk=Vk, Qk=Qk)
                    message = (f"Issued {name} to RS {rs_name}")
                    return True, message
            return False, "BEQ RSs are busy"
        elif name in {'CALL', 'RET'}:
            if not self.reservation_stations['CALL/RET'].busy:
                self.reservation_stations['CALL/RET'].push(instruction, Op=name, A=instruction.get_immediate(), dest=rob_index)
                message = (f"Issued {name} to RS CALL/RET")
                return True, message
            else:
                return False, "CALL/RET RS is busy"
        elif name in {"ADD", "SUB"}:
            for rs_name in ['ADD/SUB1', 'ADD/SUB2', 'ADD/SUB3', 'ADD/SUB4']:
                if not self.reservation_stations[rs_name].busy:
                    self.reservation_stations[rs_name].push(instruction, Op=name, dest=rob_index, Vj=Vj, Qj=Qj, Vk=Vk, Qk=Qk)
                    message = (f"Issued {name} to RS {rs_name}")
                    return True, message
            return False, "ADD/SUB RSs are busy"
        elif name == 'NAND':
            if not self.reservation_stations['NAND'].busy:
                self.reservation_stations['NAND'].push(instruction, Op=name, dest=rob_index, Vj=Vj, Qj=Qj, Vk=Vk, Qk=Qk)
                message = (f"Issued {name} to RS NAND")
                return True, message
            else:
                return False, "NAND RS is busy"
        elif name == 'MUL':
            if not self.reservation_stations['MUL'].busy:
                self.reservation_stations['MUL'].push(instruction, Op=name, dest=rob_index, Vj=Vj, Qj=Qj, Vk=Vk, Qk=Qk)
                message = (f"Issued {name} to RS MUL")
                return True, message
            else:
                return False, "MUL RS is busy"
        return False, "Unsupported instruction type"

    def issue_next(self, cycle, instruction: Instruction):
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
        """
        push a new entry into the ROB and link it to RAT
        
        args:
            name: name of instruction (e.g., 'LOAD', 'STORE', 'ALU', 'CALL', 'BEQ')
            dest: destination register or memory address
            
        returns:
            index of the new ROB entry
        """
        rob_index = (self.rob.buffer.tail) % self.rob.max_size
        success, rs_message = self.rs_issue(instruction, rob_index)
        print(rs_message)
        if not success:
            return False
        success = self.rob.push(instruction._name, instruction._rA)
        if success:
            print(f"Issued instruction {instruction.get_name()} to ROB index {(self.rob.buffer.tail - 1) % self.rob.max_size}")
        else:
            print(f"Failed to issue instruction {instruction.get_name()}: ROB is full")
            return False
        rob_index = (self.rob.buffer.tail - 1) % self.rob.max_size
        self.rat_mapping(instruction._rA, rob_index)

        # print(f"[Cycle {cycle}] Issued {instr.get_name()} | rA = {rA_val} rB = {rB_val} rC = {rC_val} immediate = {instr.get_immediate()} label = {instr.get_label()}")

        self._issued_instructions.append(instr)
        self._next_index += 1

        return instr, success
    
    def has_instructions(self):
        """Check if there are instructions left to issue."""
        return self._next_index < len(self._instructions)

    def get_issued_instructions(self):
        """Return list of instructions already issued."""
        return self._issued_instructions