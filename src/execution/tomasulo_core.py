from typing import Dict, Any, List, Optional
from .reservation_station import *
from .rob import ReorderBuffer
from .rat import RAT
from ..interfaces.register_interface import RegisterFile
from ..interfaces.memory_interface import Memory
from ..interfaces.instruction import Instruction

class TomasuloCore:
    def __init__(self):
        self.reg_file = RegisterFile()
        self.mem = Memory()
        self.reservation_stations = {
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
        self.rob = ReorderBuffer()
        self.rat = [None] * 8
    
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
    
    def commit_rob_entry(self) -> Optional[Any]:
        """
        updates the register file / memory with the value of the oldest ROB entry if ready
        clears RAT mapping for the committed entry
        removes the committed entry from the ROB
        
        returns:
            committed ROB entry value, or None if not ready
        """
        oldest_entry = self.rob.peek_front()
        if oldest_entry.ready:
            if oldest_entry.name in {"LOAD", "ADD", "SUB", "NAND", "MUL"}:
                self.reg_file.write(oldest_entry.dest, oldest_entry.value)
            elif oldest_entry.name == "CALL":
                self.reg_file.write(1, oldest_entry.value["return_address"])  # R1 holds return address
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
        success = self.rob.push(instruction._name, instruction._rA)
        if success:
            print(f"Issued instruction {instruction.get_name()} to ROB index {(self.rob.buffer.tail - 1) % self.rob.max_size}")
        else:
            print(f"Failed to issue instruction {instruction.get_name()}: ROB is full")
            return False
        rob_index = (self.rob.buffer.tail - 1) % self.rob.max_size
        self.rat_mapping(instruction._rA, rob_index)
        return success
    
    def flush(self, index: int) -> None:
        """
        flush the core state (ROB, RAT, RS)
        """
        rob_indices, dest_regs = self.rob.flush_tail(index) # flush ROB
        print(rob_indices, dest_regs)

        for i, reg in enumerate(self.rat): # flush RAT
            if reg in rob_indices:
                print(f"Flushing RAT mapping: R{i} from ROB[{reg}]")
                self.rat[i] = None
        
        for key, rs in self.reservation_stations.items(): # flush RS
            if rs.dest in rob_indices:
                print(f"Flushing RS entry: {rs.dest} from RS {key}")
                rs.pop()
            
    
    def branch_speculation(self, rob_index: int, taken: bool, target: int) -> int:
        """
        handle branch speculation outcome
        
        args:
            rob_index: ROB index of the branch instruction
            taken: whether branch was actually taken
            target: actual target address
        """
        if taken:
            self.flush(rob_index)
            return target
        return None
    
        

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
    
    

