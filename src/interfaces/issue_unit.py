from typing import Optional

from ..execution.rob import ReorderBuffer
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
        self._last_jump_index = None  # Track the last jump target to allow re-issuing loop instructions

    def rat_mapping(self, reg: int, rob_index: int) -> None:
        """
        map architectural register to ROB index
        
        args:
            reg: register name (e.g., 'R0', 'R1', ...)
            rob_index: ROB index to map to
        """
        self.rat[reg] = rob_index

    def get_operand(self, reg: int) -> tuple[bool, int]:
        """
        Gets the operand needed
        If the register is not in the ROB, then it is read directly from the register file
        If the register is in the ROB and ready, then the value is returned
        If the register is in the ROB but not ready, then the ROB index is returned
        If the register is in the ROB and ready but value is None, read from register file
        If the ROB entry is for an instruction that doesn't write to registers (BEQ/STORE), read from register file

        args:
            reg: register number
        
        returns:
            tuple (ready: bool, value: int or ROB index)
        """
        rob_entry, index = self.rob.find(reg)
        if rob_entry is None:
            return True, self._register_file.read(reg)
        
        # If ROB entry is for an instruction that doesn't write to registers, read from register file
        if rob_entry.name in ["BEQ", "STORE"]:
            # These instructions don't produce register values, so read from register file
            return True, self._register_file.read(reg)
        
        if rob_entry.ready:
            # If value is None (e.g., from BEQ/STORE), read from register file
            if rob_entry.value is None:
                return True, self._register_file.read(reg)
            # If value is a dict (e.g., from CALL), extract return_address for RET, or read from register file for others
            if isinstance(rob_entry.value, dict):
                # For CALL, the dict contains return_address
                # Only RET should use this directly, others should read from register file
                # But since we're in get_operand, we'll extract return_address if it's a dict
                return_addr = rob_entry.value.get("return_address", 0)
                return True, return_addr
            return True, rob_entry.value
        return False, index

    def get_source_operands(self, instruction: Instruction) -> tuple[int, int, int, int]:
        """
        Get source operands for an instruction, handling register renaming via RAT
        
        args:
            instruction: instruction to get operands for
        
        returns:
            tuple (Vj, Qj, Vk, Qk) where:
            - Vj, Vk are values if ready, None otherwise
            - Qj, Qk are ROB indices if not ready, None otherwise
        """
        name = instruction.get_name()
        
        if name == "BEQ":
            # BEQ: rA and rB are the operands to compare
            rB = instruction.get_rA()
            rC = instruction.get_rB()
        elif name == "STORE":
            # STORE: rA is the value to store (Vj), rB is base for address (Vk)
            rB = instruction.get_rA()  # Value to store
            rC = instruction.get_rB()  # Base register for address
        elif name == "RET":
            # RET: R1 is the operand (return address)
            rB = 1  # R1 contains return address
            rC = None
        else:
            # Other instructions: rB and rC are the source operands
            rB = instruction.get_rB()
            rC = instruction.get_rC()
        
        if rB is not None:
            foundB, valueB = self.get_operand(rB)
            if foundB:
                # If value is None, treat it as not ready (shouldn't happen for normal instructions)
                if valueB is None:
                    Vj = None
                    Qj = None  # This will cause an error, but it's better than forwarding None
                else:
                    Vj = valueB
                    Qj = None
            else:
                Vj = None
                Qj = valueB
        else:
            Vj = None
            Qj = None
        
        if rC is not None:
            foundC, valueC = self.get_operand(rC)
            if foundC:
                # If value is None, treat it as not ready (shouldn't happen for normal instructions)
                if valueC is None:
                    Vk = None
                    Qk = None  # This will cause an error, but it's better than forwarding None
                else:
                    Vk = valueC
                    Qk = None
            else:
                Vk = None
                Qk = valueC
        else:
            Vk = None
            Qk = None
            
        return Vj, Qj, Vk, Qk

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
                    # Store instruction index as PC (for computing branch target)
                    instruction_pc = self._next_index  # Current instruction index
                    self.reservation_stations[rs_name].push(instruction, A=instruction.get_immediate(), dest=rob_index, Vj=Vj, Qj=Qj, Vk=Vk, Qk=Qk, PC=instruction_pc)
                    message = (f"Issued {name} to RS {rs_name}")
                    return True, message
            return False, "BEQ RSs are busy"
        elif name in {'CALL', 'RET'}:
            if not self.reservation_stations['CALL/RET'].busy:
                # For RET, pass R1 operand (Vj/Qj)
                # For CALL, Vj and Qj are None (no operands needed)
                ret_Vj = Vj if name == "RET" else None
                ret_Qj = Qj if name == "RET" else None
                # Store instruction index as PC (for computing return address)
                instruction_pc = self._next_index  # Current instruction index
                self.reservation_stations['CALL/RET'].push(instruction, Op=name, A=instruction.get_immediate(), dest=rob_index, Vj=ret_Vj, Qj=ret_Qj, PC=instruction_pc)
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

    def issue_next(self, cycle):
        """
        Issue the next instruction in the list.
        Allows re-issuing instructions that are not in-flight (e.g., for loops).

        args:
            cycle: current cycle number.

        returns:
            tuple: (instruction, success) where instruction is the issued instruction or None, and success is a boolean
        """
        if self._next_index >= len(self._instructions):
            return None, False  # nothing left to issue
        
        instr = self._instructions[self._next_index]
        
        # Check if this instruction is still in-flight
        # If it is, we cannot re-issue it (wait for it to commit first)
        # EXCEPTION: If we just jumped back to a loop (backwards jump), allow re-issuing
        # even if in-flight, because we want to execute the loop again with updated values
        if self.is_instruction_in_flight(instr.get_instr_id()):
            # If we're at or after a jump target (loop), allow re-issuing
            if self._last_jump_index is not None and self._next_index >= self._last_jump_index:
                # Allow re-issuing even if in-flight (will create new ROB entry)
                # Keep _last_jump_index set until we encounter a forward jump or branch that takes us forward
                pass
            else:
                # Instruction is still in-flight and not at a loop, cannot re-issue yet
                return None, False
        
        # Instruction is not in-flight (committed or never issued), safe to issue/re-issue
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
        success, rs_message = self.rs_issue(instr, rob_index)
        print(rs_message)
        if not success:
            return None, False
        
        # For CALL, dest should be R1 (where return address is written)
        # For RET, dest is None (doesn't write to registers, just branches)
        # For other instructions, use rA from instruction
        if instr._name == "CALL":
            dest_reg = 1
        elif instr._name == "RET":
            dest_reg = None
        else:
            dest_reg = instr._rA
        
        success = self.rob.push(instr._name, dest_reg, instr.get_instr_id())
        if success:
            print(f"Issued instruction {instr.get_name()} to ROB index {(self.rob.buffer.tail - 1) % self.rob.max_size}")
        else:
            print(f"Failed to issue instruction {instr.get_name()}: ROB is full")
            return None, False
        rob_index = (self.rob.buffer.tail - 1) % self.rob.max_size
        if dest_reg is not None:
            self.rat_mapping(dest_reg, rob_index)

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
    
    def jump_to_label(self, label: str, label_map: dict) -> bool:
        """
        Jump to the instruction with the given label.
        
        args:
            label: label name to jump to
            label_map: dictionary mapping label names to instruction indices
            
        returns:
            True if label found and jump successful, False otherwise
        """
        if label in label_map:
            target_index = label_map[label]
            return self.jump_to_index(target_index)
        return False
    
    def is_instruction_in_flight(self, instr_id: int) -> bool:
        """
        Check if an instruction is still in-flight (in ROB or RS).
        
        An instruction is in-flight if:
        - It has a ROB entry that hasn't been committed yet
        - It's in a reservation station
        
        args:
            instr_id: instruction ID to check
            
        returns:
            True if instruction is in-flight, False otherwise
        """
        # Check if instruction is in ROB
        if self.rob.buffer.count > 0:
            entries = self.rob.buffer.traverse()
            for entry in entries:
                if entry is not None and entry.instr_id == instr_id:
                    return True  # Instruction is still in ROB (not committed)
        
        # Check if instruction is in any reservation station
        for rs in self.reservation_stations.values():
            if rs.busy and hasattr(rs, 'instruction'):
                if isinstance(rs.instruction, Instruction):
                    if rs.instruction.get_instr_id() == instr_id:
                        return True  # Instruction is in a reservation station
        
        return False  # Instruction is not in-flight (committed or never issued)
    
    def jump_to_index(self, target_index: int) -> bool:
        """
        Jump to a specific instruction index.
        Allows re-issuing instructions that are not in-flight (e.g., for loops).
        When jumping backwards (to a loop), we allow re-issuing even if instructions are in-flight.
        
        args:
            target_index: instruction index to jump to
            
        returns:
            True if index is valid, False otherwise
        """
        if 0 <= target_index < len(self._instructions):
            # If jumping backwards (to a loop), mark this as a jump target
            # If jumping forwards, clear the jump marker (we're exiting the loop)
            if target_index < self._next_index:
                self._last_jump_index = target_index
            elif target_index > self._next_index:
                # Forward jump - clear loop marker
                self._last_jump_index = None
            # If target_index == self._next_index, it's a no-op, keep current state
            self._next_index = target_index
            return True
        return False