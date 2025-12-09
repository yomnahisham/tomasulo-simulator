"""functional unit classes for executing instructions"""

from enum import Enum
from typing import Optional, Dict, Any, List


class FUState(Enum):
    """execution state of a functional unit"""
    idle = "idle"
    executing = "executing"
    finished = "finished"


class FunctionalUnit:
    """base class for all functional units"""
    
    def __init__(self, unit_type: str, latency: int):
        """
        initialize functional unit
        
        args:
            unit_type: type of instruction this FU handles
            latency: number of cycles needed for execution
        """
        self.unit_type = unit_type
        self.latency = latency
        self.cycles_remaining = 0
        self.state = FUState.idle
        self.current_instruction = None
        self.rs_entry_id = None
        self.result = None
        self.operands = {}
        
    def start_execution(self, instruction: Dict[str, Any], rs_entry_id: int, operands: Dict[str, Any]) -> None:
        """
        start executing an instruction on this FU
        
        args:
            instruction: instruction data structure
            rs_entry_id: reservation station entry id
            operands: dictionary with operand values
        """
        self.current_instruction = instruction
        self.rs_entry_id = rs_entry_id
        self.operands = operands
        self.cycles_remaining = self.latency
        self.state = FUState.executing
        self.result = None
        
    def tick(self) -> bool:
        """
        decrement cycle counter, return True if execution finished
        
        returns:
            True if execution completed this cycle, False otherwise
        """
        if self.state != FUState.executing:
            return False
            
        self.cycles_remaining -= 1
        
        if self.cycles_remaining <= 0:
            self.state = FUState.finished
            self.result = self.compute_result()
            return True
            
        return False
    
    def compute_result(self) -> Any:
        """
        compute the result of the instruction
        to be overridden by subclasses
        
        returns:
            computed result value
        """
        raise NotImplementedError("subclasses must implement compute_result")
    
    def get_result(self) -> Optional[Any]:
        """
        get the computed result
        
        returns:
            result value if execution finished, None otherwise
        """
        return self.result
    
    def reset(self) -> None:
        """clear current execution and reset to idle state"""
        self.current_instruction = None
        self.rs_entry_id = None
        self.operands = {}
        self.cycles_remaining = 0
        self.state = FUState.idle
        self.result = None
    
    def is_busy(self) -> bool:
        """
        check if this FU is currently executing
        
        returns:
            True if executing, False if idle
        """
        return self.state == FUState.executing


class AddSubFU(FunctionalUnit):
    """functional unit for ADD and SUB instructions (2 cycles)"""
    
    def __init__(self):
        super().__init__("ADD/SUB", 2)
    
    def compute_result(self) -> int:
        """compute ADD or SUB result"""
        op = self.current_instruction.get("op", "")
        rB_val = self.operands.get("Vj", 0)
        rC_val = self.operands.get("Vk", 0)
        
        if op == "ADD":
            return (rB_val + rC_val) & 0xFFFF  # 16-bit result
        elif op == "SUB":
            return (rB_val - rC_val) & 0xFFFF  # 16-bit result
        else:
            return 0


class NandFU(FunctionalUnit):
    """functional unit for NAND instructions (1 cycle)"""
    
    def __init__(self):
        super().__init__("NAND", 1)
    
    def compute_result(self) -> int:
        """compute NAND result"""
        rB_val = self.operands.get("Vj", 0)
        rC_val = self.operands.get("Vk", 0)
        return (~(rB_val & rC_val)) & 0xFFFF  # 16-bit result


class MulFU(FunctionalUnit):
    """functional unit for MUL instructions (12 cycles)"""
    
    def __init__(self):
        super().__init__("MUL", 12)
    
    def compute_result(self) -> int:
        """compute MUL result (least significant 16 bits)"""
        rB_val = self.operands.get("Vj", 0)
        rC_val = self.operands.get("Vk", 0)
        result = (rB_val * rC_val) & 0xFFFF  # least significant 16 bits
        return result


class LoadFU(FunctionalUnit):
    """functional unit for LOAD instructions (6 cycles: 2 address + 4 memory)"""
    
    def __init__(self, memory_interface):
        super().__init__("LOAD", 6)
        self.memory_interface = memory_interface
        self.address_phase = True  # first 2 cycles for address calculation
        self.computed_address = None
    
    def start_execution(self, instruction: Dict[str, Any], rs_entry_id: int, operands: Dict[str, Any]) -> None:
        """start load execution"""
        super().start_execution(instruction, rs_entry_id, operands)
        self.address_phase = True
        self.computed_address = None
    
    def tick(self) -> bool:
        """handle load execution with address and memory phases"""
        if self.state != FUState.executing:
            return False
        
        self.cycles_remaining -= 1
        
        # first 2 cycles: address calculation
        if self.address_phase and self.cycles_remaining == 4:
            rB_val = self.operands.get("Vj", 0) or 0
            offset = self.operands.get("immediate", 0) or 0
            self.computed_address = (rB_val + offset) & 0xFFFF
            self.address_phase = False
        
        # last 4 cycles: memory read
        if self.cycles_remaining <= 0:
            # read from memory
            if self.computed_address is not None:
                self.result = self.memory_interface.read_memory(self.computed_address)
            else:
                self.result = 0
            self.state = FUState.finished
            return True
        
        return False
    
    def compute_result(self) -> int:
        """result already computed during tick, just return it"""
        return self.result if self.result is not None else 0


class StoreFU(FunctionalUnit):
    """functional unit for STORE instructions (6 cycles: 2 address + 4 memory)"""
    
    def __init__(self, memory_interface):
        super().__init__("STORE", 6)
        self.memory_interface = memory_interface
        self.address_phase = True
        self.computed_address = None
        self.store_value = None
    
    def start_execution(self, instruction: Dict[str, Any], rs_entry_id: int, operands: Dict[str, Any]) -> None:
        """start store execution"""
        super().start_execution(instruction, rs_entry_id, operands)
        self.address_phase = True
        self.computed_address = None
        self.store_value = self.operands.get("Vj", 0)  # value to store
    
    def tick(self) -> bool:
        """handle store execution with address and memory phases"""
        if self.state != FUState.executing:
            return False
        
        self.cycles_remaining -= 1
        
        # first 2 cycles: address calculation
        if self.address_phase and self.cycles_remaining == 4:
            rB_val = self.operands.get("Vk", 0) or 0
            offset = self.operands.get("immediate", 0) or 0
            self.computed_address = (rB_val + offset) & 0xFFFF
            self.address_phase = False
        
        # last 4 cycles: memory write (handled by writeback stage)
        if self.cycles_remaining <= 0:
            self.result = self.computed_address  # return address for writeback
            self.state = FUState.finished
            return True
        
        return False
    
    def compute_result(self) -> int:
        """return computed address"""
        return self.computed_address if self.computed_address is not None else 0
    
    def get_store_value(self) -> int:
        """get the value to be stored"""
        return self.store_value if self.store_value is not None else 0


class BeqFU(FunctionalUnit):
    """functional unit for BEQ instructions (1 cycle)"""
    
    def __init__(self):
        super().__init__("BEQ", 1)
    
    def compute_result(self) -> Dict[str, Any]:
        """compute BEQ condition result"""
        rA_val = self.operands.get("Vj", 0)
        rB_val = self.operands.get("Vk", 0)
        offset = self.operands.get("immediate", 0)
        pc = self.operands.get("pc", 0)
        
        # compare operands
        condition_met = (rA_val == rB_val)
        
        # compute target address
        if condition_met:
            target = (pc + 1 + offset) & 0xFFFF
        else:
            target = (pc + 1) & 0xFFFF
        
        return {
            "taken": condition_met,
            "target": target,
            "condition_met": condition_met,
        }


class CallRetFU(FunctionalUnit):
    """functional unit for CALL and RET instructions (1 cycle)"""
    
    def __init__(self):
        super().__init__("CALL/RET", 1)
    
    def compute_result(self) -> Dict[str, Any]:
        """compute CALL or RET target address"""
        op = self.current_instruction.get("op", "")
        pc = self.operands.get("pc", 0)
        
        if op == "CALL":
            # label is encoded as 7-bit signed constant in immediate
            label_offset = self.operands.get("immediate", 0)
            target = (pc + 1 + label_offset) & 0xFFFF
            return {
                "target": target,
                "return_address": (pc + 1) & 0xFFFF,
            }
        elif op == "RET":
            # return address is in R1
            r1_val = self.operands.get("Vj", 0)  # R1 value
            # If R1 contains a dict (from CALL forwarding), extract return_address
            if isinstance(r1_val, dict):
                r1_val = r1_val.get("return_address", 0)
            # Ensure r1_val is an integer
            if not isinstance(r1_val, int):
                r1_val = 0
            return {
                "target": r1_val & 0xFFFF,
            }
        else:
            return {"target": (pc + 1) & 0xFFFF}


class FUPool:
    """manages all functional units"""
    
    def __init__(self, memory_interface):
        """
        initialize FU pool with all functional units
        
        args:
            memory_interface: interface for memory operations
        """
        # create FUs according to spec
        self.add_sub_units = [AddSubFU() for _ in range(4)]
        self.nand_units = [NandFU() for _ in range(2)]
        self.mul_units = [MulFU() for _ in range(1)]
        self.load_units = [LoadFU(memory_interface) for _ in range(2)]
        self.store_units = [StoreFU(memory_interface) for _ in range(1)]
        self.beq_units = [BeqFU() for _ in range(2)]
        self.call_ret_units = [CallRetFU() for _ in range(1)]
        
        # map instruction types to FU lists
        self.fu_map = {
            "ADD": self.add_sub_units,
            "SUB": self.add_sub_units,
            "NAND": self.nand_units,
            "MUL": self.mul_units,
            "LOAD": self.load_units,
            "STORE": self.store_units,
            "BEQ": self.beq_units,
            "CALL": self.call_ret_units,
            "RET": self.call_ret_units,
        }
    
    def get_available_fu(self, instruction_type: str) -> Optional[FunctionalUnit]:
        """
        get an available FU for the given instruction type
        
        args:
            instruction_type: type of instruction (ADD, SUB, etc.)
            
        returns:
            available FU or None if all busy
        """
        fu_list = self.fu_map.get(instruction_type)
        if fu_list is None:
            return None
        
        for fu in fu_list:
            if not fu.is_busy():
                return fu
        
        return None
    
    def is_available(self, instruction_type: str) -> bool:
        """
        check if any FU is available for the instruction type
        
        args:
            instruction_type: type of instruction
            
        returns:
            True if at least one FU is available
        """
        return self.get_available_fu(instruction_type) is not None
    
    def tick_all(self) -> list:
        """
        tick all FUs and return list of finished executions
        
        returns:
            list of (fu, rs_entry_id, instruction, result) tuples for finished executions
        """
        finished = []
        
        for fu_list in [
            self.add_sub_units,
            self.nand_units,
            self.mul_units,
            self.load_units,
            self.store_units,
            self.beq_units,
            self.call_ret_units,
        ]:
            for fu in fu_list:
                if fu.tick():
                    finished.append((
                        fu,
                        fu.rs_entry_id,
                        fu.current_instruction,
                        fu.get_result(),
                    ))
        
        return finished
    
    def get_all_fu_status(self) -> Dict[str, list]:
        """
        get status of all FUs for GUI visualization
        
        returns:
            dictionary mapping instruction types to lists of FU status dicts
        """
        status = {}
        
        for inst_type, fu_list in self.fu_map.items():
            status[inst_type] = []
            for i, fu in enumerate(fu_list):
                status[inst_type].append({
                    "id": i,
                    "busy": fu.is_busy(),
                    "cycles_remaining": fu.cycles_remaining,
                    "rs_entry_id": fu.rs_entry_id,
                    "state": fu.state.value,
                })
        
        return status
    
    def flush_rs_entries(self, rs_entry_ids: List[str]) -> None:
        """
        flush functional units that are executing instructions for the given RS entry IDs
        
        args:
            rs_entry_ids: list of RS entry IDs to flush
        """
        if not rs_entry_ids:
            return
        
        flushed_count = 0
        for fu_list in [
            self.add_sub_units,
            self.nand_units,
            self.mul_units,
            self.load_units,
            self.store_units,
            self.beq_units,
            self.call_ret_units,
        ]:
            for fu in fu_list:
                # Flush if FU is executing or finished (hasn't been reset yet) and matches RS entry ID
                if fu.rs_entry_id in rs_entry_ids and (fu.is_busy() or fu.state == FUState.finished):
                    print(f"Flushing FU {fu.unit_type} (state: {fu.state.value}) executing RS entry {fu.rs_entry_id}")
                    fu.reset()
                    flushed_count += 1
        
        if flushed_count > 0:
            print(f"Flushed {flushed_count} functional unit(s)")

