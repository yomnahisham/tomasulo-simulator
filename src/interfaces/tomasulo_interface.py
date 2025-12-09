from typing import Dict, Any, List, Optional
from ..execution.reservation_station import *
from ..execution.rob import ReorderBuffer
from ..interfaces.register_interface import RegisterFile
from ..interfaces.memory_interface import Memory
from ..interfaces.instruction import Instruction

class TomasuloCore:
    def __init__(self, reg_file: RegisterFile = None, mem: Memory = None, reservation_stations: Dict[str, ReservationStation] = None, rob: ReorderBuffer = None, rat: List[Optional[int]] = None):
        self.reg_file = reg_file if reg_file is not None else RegisterFile()
        self.mem = mem if mem is not None else Memory()
        self.reservation_stations = reservation_stations if reservation_stations is not None else {
            'LOAD1': LoadRS(),
            'LOAD2': LoadRS(),
            'STORE': StoreRS(),
            'BEQ1': BEQRS(),
            'BEQ2': BEQRS(),
            'CALL/RET': CALLRS(),
            'ADD/SUB1': ALURS(),
            'ADD/SUB2': ALURS(),
            'ADD/SUB3': ALURS(),
            'ADD/SUB4': ALURS(),
            'NAND': ALURS(),
            'MUL': ALURS()
        }
        self.rob = rob if rob is not None else ReorderBuffer()
        self.rat = rat if rat is not None else [None] * 8
        self._pending_branch_label = None  # Store label for branch jumps
        self._pending_branch_rob_index = None  # Store ROB index of the branch that set the label (for priority)
        self._pending_branch_target = None  # Store target address for RET jumps
        self._recently_flushed_ids = []  # Track instruction IDs flushed in the last cycle
        self._flushed_rs_entry_ids = []  # Track RS entry IDs flushed in the last cycle

    
    def rat_mapping(self, reg: int, rob_index: int) -> None:
        """
        map architectural register to ROB index
        
        args:
            reg: register name (e.g., 'R0', 'R1', ...)
            rob_index: ROB index to map to
        """
        self.rat[reg] = rob_index

    def get_rat_rob_index(self, reg: int) -> Optional[int]:
        """
        get ROB index mapped to architectural register
        
        args:
            reg: register name (e.g., 'R0', 'R1', ...)
            
        returns:
            ROB index mapped to the register, or None if not mapped
        """
        return self.rat[reg]
    
    def clear_rat_mapping(self, dest_reg: int, rob_index: int) -> None:
        """
        clear RAT mapping if it points to the given ROB index
        
        args:
            dest_reg: destination register name (e.g., 'R0', 'R1', ...)
            rob_index: ROB index to check
        """
        if self.rat[dest_reg] == rob_index:
            self.rat[dest_reg] = None

    def update_rat(self, rob_index: int, value: Any) -> None: # TODO: check if the required functionality is the same as clear_rat_mapping
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

    def print_rat(self) -> None:
        """
        print current RAT mappings (for debugging)
        """
        print("\n" + "="*50)
        print("  REGISTER ALIAS TABLE (RAT)")
        print("="*50)
        print(f"{'Reg':<8} {'Mapped to':<15} {'Status'}")
        print("-"*50)
        for reg in range(len(self.rat)):
            if self.rat[reg] is None:
                status = "Ready (in RegFile)"
                mapped = "None"
            else:
                status = f"Waiting on ROB[{self.rat[reg]}]"
                mapped = f"ROB[{self.rat[reg]}]"
            print(f"R{reg:<7} {mapped:<15} {status}")
        print("="*50 + "\n")

    def get_ready_rs_entries(self) -> List[Dict[str, Any]]:
        """    returns:
        list of RS entry dictionaries, each containing:
            - id: RS entry id
            - instruction: instruction data structure (as dict)
            - other RS entry fields"""
        ready_rs_entries = []
        excluded_fields = {"Op", "busy", "state"}
        for rs_name, rs in self.reservation_stations.items():
            # Allow RS entries that are ready, even if they're in EXECUTING state
            # This handles the case where FU was flushed/reset but RS state wasn't updated
            # The execution manager will restart execution if needed
            if rs.is_ready():
                entry = {k: rs.__dict__[k] for k in rs.__dict__ if k not in excluded_fields}
                entry['id'] = rs_name
                # Convert Instruction object to dictionary format expected by ExecutionManager
                if 'instruction' in entry and isinstance(entry['instruction'], Instruction):
                    instr = entry['instruction']
                    entry['instruction'] = {
                        'op': instr.get_name(),
                        'instr_id': instr.get_instr_id(),
                        'rob_index': entry.get('dest'),
                        'rA': instr.get_rA(),
                        'rB': instr.get_rB(),
                        'rC': instr.get_rC(),
                        'immediate': instr.get_immediate(),
                        'label': instr.get_label()
                    }
                ready_rs_entries.append(entry)
        return ready_rs_entries
    
    def get_rs_operands(self, rs_entry: Dict[str, Any]) -> Dict[str, Any]:
        """    args:
            rs_entry: RS entry dictionary (from get_ready_rs_entries)
            
            returns:
                dictionary with operand values:
                    - Vj: value of first operand (if ready) 
                    - Vk: value of second operand (if ready)
                    - Qj: ROB index producing first operand (if not ready)
                    - Qk: ROB index producing second operand (if not ready)
                    - immediate: immediate value if applicable
                    - pc: program counter value if applicable"""
        # rs_entry is already a dictionary, just extract operands
        operands = {}
        if 'Vj' in rs_entry and rs_entry['Vj'] is not None:
            operands['Vj'] = rs_entry['Vj']
        if 'Vk' in rs_entry and rs_entry['Vk'] is not None:
            operands['Vk'] = rs_entry['Vk']
        if 'Qj' in rs_entry and rs_entry['Qj'] is not None:
            operands['Qj'] = rs_entry['Qj']
        if 'Qk' in rs_entry and rs_entry['Qk'] is not None:
            operands['Qk'] = rs_entry['Qk']
        if 'A' in rs_entry and rs_entry['A'] is not None:
            operands['immediate'] = rs_entry['A']
        if 'PC' in rs_entry and rs_entry['PC'] is not None:
            operands['pc'] = rs_entry['PC']
        # Get instruction info for branch instructions
        if 'instruction' in rs_entry and isinstance(rs_entry['instruction'], dict):
            instr = rs_entry['instruction']
            if instr.get('op') == 'BEQ' and 'immediate' not in operands:
                operands['immediate'] = instr.get('immediate', 0) or 0
            # PC is stored in RS entry for CALL/RET, use it if available
            if 'PC' in rs_entry and rs_entry['PC'] is not None:
                operands['pc'] = rs_entry['PC']
            elif instr.get('op') in ['BEQ', 'CALL', 'RET'] and 'pc' not in operands:
                operands['pc'] = 0  # Default PC if not available
        return operands
    
    def print_rs(self) -> None:
        """
        print current RS entries (for debugging)
        """
        print("\n" + "="*80)
        print("  RESERVATION STATIONS")
        print("="*80)
        
        for rs_name, rs in self.reservation_stations.items():
            if rs.busy:
                print(f"\n[{rs_name}] - BUSY - State: {rs.state}")
                print(f"  Instruction: {rs.instruction}")
                print(f"  Op: {rs.Op}")
                
                # Print destination
                if hasattr(rs, 'dest') and rs.dest is not None:
                    print(f"  Destination: ROB[{rs.dest}]")
                
                # Print operands based on RS type
                if hasattr(rs, 'Vj'):
                    vj_str = f"Vj={rs.Vj}" if rs.Vj is not None else "Vj=None"
                    qj_str = f"Qj=ROB[{rs.Qj}]" if rs.Qj is not None else "Qj=None"
                    print(f"  Operand 1: {vj_str}, {qj_str}")
                
                if hasattr(rs, 'Vk'):
                    vk_str = f"Vk={rs.Vk}" if rs.Vk is not None else "Vk=None"
                    qk_str = f"Qk=ROB[{rs.Qk}]" if rs.Qk is not None else "Qk=None"
                    print(f"  Operand 2: {vk_str}, {qk_str}")
                
                if hasattr(rs, 'A'):
                    print(f"  Address: A={rs.A}")
                
                if hasattr(rs, 'PC'):
                    print(f"  PC: {rs.PC}")
                
                if hasattr(rs, 'rob_index'):
                    print(f"  ROB Index: {rs.rob_index}")
                    
                print("-"*80)
            else:
                print(f"[{rs_name}] - FREE")
        
        print("="*80 + "\n")
    
    def update_rob_value(self, rob_index: int, value: Any) -> None:
        """
        update ROB entry with computed result value
        
        args:
            rob_index: ROB entry index
            value: computed result value
        """
        # Check if ROB entry exists and is valid
        if rob_index is not None:
            try:
                # Use the ROB's update method which handles bounds checking
                self.rob.update(rob_index, value)
            except Exception:
                # ROB entry may have been committed already or index invalid, ignore
                pass        

    def forward_to_rs(self, rob_index: int, value: Any) -> None:
        """
        forward result value to waiting RS entries
        
        args:
            rob_index: ROB index that produced the value
            value: result value to forward
            
        note:
            should update Qj/Qk in RS entries that are waiting for this ROB index
        """
        # Qj and Qk store ROB indices, not destination registers
        # Check if ROB entry still exists (might have been flushed)
        rob_entry = None
        try:
            if 0 <= rob_index < self.rob.max_size and self.rob.buffer.count > 0:
                # Try to get the entry - it might have been flushed
                entries = self.rob.buffer.traverse()
                for i, entry in enumerate(entries):
                    actual_index = (self.rob.buffer.head + i) % self.rob.max_size
                    if actual_index == rob_index and entry is not None:
                        rob_entry = entry
                        break
        except Exception:
            # ROB entry doesn't exist (was flushed), skip forwarding
            return

        # If ROB entry was flushed, don't forward (it's already been handled)
        if rob_entry is None:
            return

        # Check if this is a CALL result (dict with return_address)
        # CALL results should only be used by RET, not forwarded to other RS entries
        if isinstance(value, dict):
            # Only forward to RET RS entries (they need the return_address)
            for rs in self.reservation_stations.values():
                if not rs.busy:
                    continue
                if hasattr(rs, 'Op') and rs.Op == "RET" and hasattr(rs, 'Qj') and rs.Qj == rob_index:
                    # Extract return_address from dict for RET
                    return_addr = value.get("return_address", 0)
                    print(f"Forwarding to RET RS (R1): {rs}")
                    rs.source_update(return_addr)
            return  # Don't forward dicts to other RS entries

        for rs in self.reservation_stations.values():
            if not rs.busy:
                continue
            
            # Check for CALLRS (RET uses R1 via Qj)
            if hasattr(rs, 'Op') and rs.Op == "RET" and hasattr(rs, 'Qj') and rs.Qj == rob_index:
                print(f"Forwarding to RET RS (R1): {rs}")
                rs.source_update(value)
            # Check for single-source RS (like LOAD)
            elif hasattr(rs, 'Qj') and not hasattr(rs, 'Qk'):
                if rs.Qj == rob_index:
                    print(f"Forwarding to RS with single source: {rs}")
                    rs.source_update(value)
            else:
                # Check for dual-source RS (like ADD, STORE, BEQ)
                if hasattr(rs, 'Qj') and rs.Qj == rob_index:
                    print(f"Forwarding to RS source1: {rs}")
                    rs.source1_update(value)
                if hasattr(rs, 'Qk') and rs.Qk == rob_index:
                    print(f"Forwarding to RS source2: {rs}")
                    rs.source2_update(value)

    def notify_branch_result(self, rob_index: int, taken: bool, target: int, label: str = None) -> int:
        """
        notify tomasulo core of branch outcome for misprediction handling
        
        args:
            rob_index: ROB index of the branch instruction
            taken: whether branch was actually taken
            target: actual target address
            label: label name for the branch target (optional)
            
        returns:
            target address if taken, None otherwise
            
        note:
            this function is to be implemented by Part 2 (tomasulo core)
            Part 2 should check for misprediction and handle flush if needed
        """
        if taken:
            # If we already have a pending branch label, check if this branch is older
            # Older branches should take priority (they come first in program order)
            if hasattr(self, '_pending_branch_label') and self._pending_branch_label is not None:
                # Check if we have a pending branch ROB index
                if hasattr(self, '_pending_branch_rob_index') and self._pending_branch_rob_index is not None:
                    # Check which branch is older by comparing distances from ROB head
                    # In a circular buffer, we need to check which is closer to the head
                    head = self.rob.buffer.head
                    max_size = self.rob.max_size
                    
                    # Calculate distance from head for both branches
                    dist_current = (rob_index - head + max_size) % max_size
                    dist_pending = (self._pending_branch_rob_index - head + max_size) % max_size
                    
                    # Only update if this branch is older (closer to head)
                    if dist_current < dist_pending:
                        # This branch is older, it should take priority
                        # Flush the previous branch's effects first (it will be flushed by the new flush)
                        flushed_ids = self.flush(rob_index)
                        self._recently_flushed_ids.extend([id for id in flushed_ids if id is not None])
                        self._pending_branch_label = label
                        self._pending_branch_rob_index = rob_index
                        if label is None:
                            self._pending_branch_target = target
                        return target
                    else:
                        # Previous branch is older, keep it (this branch will be flushed)
                        return None
                else:
                    # No pending ROB index, store this one
                    flushed_ids = self.flush(rob_index)
                    self._recently_flushed_ids.extend([id for id in flushed_ids if id is not None])
                    self._pending_branch_label = label
                    self._pending_branch_rob_index = rob_index
                    if label is None:
                        self._pending_branch_target = target
                    return target
            else:
                # No pending branch, store this one
                flushed_ids = self.flush(rob_index)
                # Store flushed instruction IDs for integration layer to track
                self._recently_flushed_ids.extend([id for id in flushed_ids if id is not None])
                # Store label for later use by integration layer (for CALL/BEQ)
                self._pending_branch_label = label
                self._pending_branch_rob_index = rob_index
                # Store target address for RET (when label is None)
                if label is None:
                    self._pending_branch_target = target
                return target
        return None

    def mark_rs_executing(self, rs_entry_id: str) -> None:
        """
        mark RS entry as executing
        
        args:
            rs_entry_id: RS entry id (string key)
        """
        self.reservation_stations[rs_entry_id].change_state("EXECUTING")
    
    def clear_rs_entry(self, rs_entry_id: str) -> None:
        """
        clear a reservation station entry after its result has been written back to ROB
        
        args:
            rs_entry_id: RS entry id (string key)
        """
        if rs_entry_id in self.reservation_stations:
            self.reservation_stations[rs_entry_id].pop()





    def get_oldest_ready_rob_index(self) -> Optional[int]:
        """
        get oldest ROB index for CDB arbitration
        
        returns:
            oldest ROB index that has a ready result, or None
            
        note:
            this function is to be implemented by Part 2 (tomasulo core)
        """
        return self.rob.buffer.head
    
    def commit_rob_entry(self, cycle: int = None, timing_tracker = None) -> Optional[Any]:
        """
        updates the register file / memory with the value of the oldest ROB entry if ready
        clears RAT mapping for the committed entry
        removes the committed entry from the ROB
        
        args:
            cycle: current cycle number for commit timing (optional)
            timing_tracker: timing tracker to record commit timing (optional)
        
        returns:
            committed ROB entry value, or None if not ready
        """
        # Check if ROB is empty before trying to commit
        if self.rob.buffer.count == 0:
            return None
        
        oldest_entry = self.rob.peek_front()
        if oldest_entry is None:
            return None
        
        if oldest_entry.ready:
            # Record commit timing if timing_tracker and cycle are provided
            # If ROB entry is ready, it means the instruction has finished and been written back
            if timing_tracker is not None and cycle is not None and oldest_entry.instr_id is not None:
                timing = timing_tracker.get_timing(oldest_entry.instr_id)
                existing_commit = timing.get("commit") if timing else None
                # Only record commit if not already committed
                if existing_commit is None:
                    if timing:
                        write = timing.get("write")
                        finish_exec = timing.get("finish_exec")
                        # Only record commit if instruction has finished execution and been written back
                        # This ensures commit happens after write (commit >= write)
                        if finish_exec is not None and write is not None:
                            # Commit must happen at or after write time
                            if cycle >= write:
                                timing_tracker.record_commit(oldest_entry.instr_id, cycle)
                        # If finish_exec or write is None, don't record commit yet
                        # The instruction hasn't completed execution/writeback
                    # If no timing entry exists yet, don't record commit (instruction hasn't executed)
            
            if oldest_entry.name in {"LOAD", "ADD", "SUB", "NAND", "MUL"}:
                # Only write if value is not None (shouldn't be None for these instructions)
                if oldest_entry.value is not None:
                    self.reg_file.write(oldest_entry.dest, oldest_entry.value)
                # Clear RAT mapping for register-writing instructions
                if oldest_entry.dest is not None:
                    self.clear_rat_mapping(oldest_entry.dest, self.rob.buffer.head)
            elif oldest_entry.name == "CALL":
                # CALL writes return address to R1 (which is stored in dest)
                if oldest_entry.value is not None:
                    if isinstance(oldest_entry.value, dict):
                        return_addr = oldest_entry.value.get("return_address")
                        if return_addr is not None:
                            self.reg_file.write(oldest_entry.dest, return_addr)
                    else:
                        self.reg_file.write(oldest_entry.dest, oldest_entry.value)
                # Clear RAT mapping for R1 (stored in dest)
                if oldest_entry.dest is not None:
                    self.clear_rat_mapping(oldest_entry.dest, self.rob.buffer.head)
            elif oldest_entry.name == "STORE":
                # STORE doesn't write to registers, just memory (handled in writeback)
                # No RAT mapping to clear
                pass
            else:
                # For other instructions, clear RAT mapping if dest is not None
                if oldest_entry.dest is not None:
                    self.clear_rat_mapping(oldest_entry.dest, self.rob.buffer.head)
            
            self.rob.pop_front()
            return oldest_entry.dest, oldest_entry.value
        return None
        
    def print_all(self, cycle: int = None) -> None:
        """
        Print complete state of the execution core (for debugging)
        
        args:
            cycle: optional cycle number to display
        """
        header = f"CYCLE {cycle}" if cycle is not None else "EXECUTION CORE STATE"
        print("\n" + "#"*90)
        print(f"  {header}")
        print("#"*90)
        
        # Print ROB
        self.rob.print()
        
        # Print RAT
        self.print_rat()
        
        # Print RS
        self.print_rs()
        
        print("#"*90)
        print(f"  END OF {header}")
        print("#"*90 + "\n")
        pass

    def get_operand(self, reg: int) -> tuple[bool, int]:
        """
        Gets the operand needed
        If the register is not in the ROB, then it is read directly from the register file
        If the register is in the ROB and ready, then the value is returned
        If the register is in the ROB but not ready, then the RS entry id is returned

        args:
            reg: register number
        
        returns:
            tuple (ready: bool, value: int or RS entry id)
        """
        rob, index = self.rob.find(reg)
        if rob is None:
            return True, self.reg_file.read(reg)
        if rob.ready:
            return True, rob.value
        return False, index


    def get_source_operands(self, instruction: Instruction) -> tuple[int, int, int, int]:
        if instruction.get_name() == "BEQ":
            rB = instruction.get_rA()
            rC = instruction.get_rB()
        else:
            rB = instruction.get_rB()
            rC = instruction.get_rC()
        
        if rB is not None:
            foundB, valueB = self.get_operand(rB)
            if foundB:
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
        print(f"Vj: {Vj}, Qj: {Qj}, Vk: {Vk}, Qk: {Qk}")
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



    def issue(self, instruction: Instruction) -> bool:
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
        success = self.rob.push(instruction._name, instruction._rA, instruction.get_instr_id())
        if success:
            print(f"Issued instruction {instruction.get_name()} to ROB index {(self.rob.buffer.tail - 1) % self.rob.max_size}")
        else:
            print(f"Failed to issue instruction {instruction.get_name()}: ROB is full")
            return False
        rob_index = (self.rob.buffer.tail - 1) % self.rob.max_size
        self.rat_mapping(instruction._rA, rob_index)
        return success
    
    def flush(self, index: int) -> List[Optional[int]]:
        """
        flush the core state (ROB, RAT, RS)
        
        returns:
            list of instruction IDs that were flushed
        """
        rob_indices, dest_regs, instr_ids = self.rob.flush_tail(index) # flush ROB
        print(rob_indices, dest_regs)

        # Flush RAT - clear mappings to flushed ROB indices
        for i, reg in enumerate(self.rat): # flush RAT
            if reg in rob_indices:
                print(f"Flushing RAT mapping: R{i} from ROB[{reg}]")
                self.rat[i] = None
        
        # Flush RS - clear entries that reference flushed ROB indices
        flushed_rs_entry_ids = []  # Track RS entry IDs that are being flushed
        for key, rs in self.reservation_stations.items(): # flush RS
            if not rs.busy:
                continue
            
            # Check if this RS entry's dest is in flushed indices
            should_flush = False
            if rs.dest in rob_indices:
                print(f"Flushing RS entry: {rs.dest} from RS {key} (dest matches)")
                should_flush = True
            # Also check if RS is waiting on flushed ROB indices (Qj or Qk)
            elif hasattr(rs, 'Qj') and rs.Qj is not None and rs.Qj in rob_indices:
                print(f"Flushing RS entry from RS {key} (Qj={rs.Qj} matches flushed)")
                should_flush = True
            elif hasattr(rs, 'Qk') and rs.Qk is not None and rs.Qk in rob_indices:
                print(f"Flushing RS entry from RS {key} (Qk={rs.Qk} matches flushed)")
                should_flush = True
            # Special case: flush BEQ RS entries when jumping back (they're from previous iteration)
            # This is needed for loops - BEQ instructions from previous iterations should be flushed
            # When we flush ROB entries (backwards jump), also flush any BEQ RS entries that are busy
            # because they're control flow instructions from the previous iteration
            elif key in ['BEQ1', 'BEQ2']:
                # If we're flushing ROB entries (backwards jump), flush all BEQ RS entries
                # They're from previous loop iteration and should be cleared
                if len(rob_indices) > 0:  # We're doing a flush (backwards jump)
                    print(f"Flushing BEQ RS entry from RS {key} (backwards jump - clearing previous iteration)")
                    should_flush = True
            
            if should_flush:
                flushed_rs_entry_ids.append(key)  # Track this RS entry ID
                rs.pop()
                # Make sure state is also reset
                if hasattr(rs, 'state'):
                    rs.state = None
                if hasattr(rs, 'dest'):
                    rs.dest = None
        
        # Store flushed RS entry IDs for execution manager to flush functional units
        self._flushed_rs_entry_ids = flushed_rs_entry_ids
        
        return instr_ids
            
    

    
        

if __name__ == "__main__":
    core = TomasuloCore()

    core.reg_file.write(0, 0)  # R0 is always 0
    core.reg_file.write(1, 10)
    core.reg_file.write(2, 20)
    core.reg_file.write(3, 30)
    core.reg_file.write(4, 40)
    core.reg_file.write(5, 50)
    core.reg_file.write(6, 60)
    core.reg_file.write(7, 70)

    instruction2 = Instruction(name="ADD", rA=1, rB=2, rC=3, instr_id=1)
    instruction3 = Instruction(name="STORE", rA=4, rB=5, immediate=200, instr_id=2)
    instruction4 = Instruction(name="BEQ", rA=6, rB=7, label="LABEL", instr_id=3)
    instruction5 = Instruction(name="CALL", rA=1, immediate=300, instr_id=4)
    instruction6 = Instruction(name="MUL", rA=2, rB=3, rC=4, instr_id=5)
    instruction7 = Instruction(name="NAND", rA=5, rB=6, rC=7, instr_id=6)
    
    core.issue(instruction2)
    core.issue(instruction3)
    core.issue(instruction4)
    core.issue(instruction5)
    core.issue(instruction6)
    core.issue(instruction7)
    
    core.rob.print()
    # core.print_rat()
    core.print_rs()
    core.flush(2)
    # core.rob.print()
    # core.print_rat()
    core.print_rs()

    # core.flush(3)

    # core.rob.print()
    # core.print_rat()
    # core.print_rs()

