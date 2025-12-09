"""execution manager coordinates all functional units"""

from typing import Dict, Any, List, Optional
from .functional_units import FUPool
from .cdb import CDB
from .writeback import WriteBackStage
from .branch_evaluator import BranchEvaluator
from .timing_tracker import TimingTracker


class ExecutionManager:
    """manages execution of instructions on functional units"""
    
    def __init__(self, memory_interface, tomasulo_interface):
        """
        initialize execution manager
        
        args:
            memory_interface: interface to Part 1 (memory)
            tomasulo_interface: interface to Part 2 (RS/ROB/RAT)
        """
        self.memory_interface = memory_interface
        self.tomasulo_interface = tomasulo_interface
        
        # create components
        self.fu_pool = FUPool(memory_interface)
        self.cdb = CDB()
        self.writeback_stage = WriteBackStage(self.cdb, tomasulo_interface, memory_interface)
        self.branch_evaluator = BranchEvaluator()
        self.timing_tracker = TimingTracker()
        
        self.current_cycle = 0
    
    def execute_cycle(self, current_cycle: int) -> None:
        """
        execute one cycle of the execution engine
        
        args:
            current_cycle: current simulation cycle number
        """
        self.current_cycle = current_cycle
        
        # step 0: clear CDB from previous cycle (before processing new write-back)
        # this allows the CDB to remain busy during the cycle it broadcasts
        # and only be cleared at the start of the next cycle
        self.cdb.clear()
        
        # step 1: process write-back from previous cycle (CDB broadcast)
        # this makes results available for instructions waiting in RS
        self.writeback_stage.process_write_back(current_cycle, self.timing_tracker)
        
        # step 2: advance all executing FUs (decrement cycles)
        finished_executions = self.fu_pool.tick_all()
        
        # step 3: handle finished executions (add to write-back queue)
        for fu, rs_entry_id, instruction, result in finished_executions:
            self._handle_finished_execution(fu, rs_entry_id, instruction, result)
        
        # step 4: try to write-back any newly finished instructions (if CDB available)
        # this allows same-cycle write-back for instructions that just finished
        self.writeback_stage.process_write_back(current_cycle, self.timing_tracker)
        
        # step 5: check for ready instructions and start execution
        # instructions can now use results that were just written back
        self._start_ready_instructions()
        
        # note: CDB is NOT cleared here - it remains busy during this cycle
        # and will be cleared at the start of the next cycle (step 0 above)
    
    def _handle_finished_execution(self, fu, rs_entry_id: int, instruction: Dict[str, Any], result: Any) -> None:
        """
        handle a finished execution
        
        args:
            fu: functional unit that finished
            rs_entry_id: reservation station entry id
            instruction: instruction data structure
            result: computed result
        """
        inst_type = instruction.get("op", "")
        rob_index = instruction.get("rob_index")
        instr_id = instruction.get("instr_id")
        
        # record finish execution timing
        if instr_id is not None:
            self.timing_tracker.record_finish_exec(instr_id, self.current_cycle)
        
        # handle branch instructions specially
        if inst_type == "BEQ":
            # evaluate branch
            operand_a = fu.operands.get("Vj", 0)
            operand_b = fu.operands.get("Vk", 0)
            offset = fu.operands.get("immediate", 0)
            pc = fu.operands.get("pc", 0)
            
            branch_result = self.branch_evaluator.evaluate_beq(
                operand_a, operand_b, offset, pc
            )
            
            # Get label from instruction for branch target resolution
            branch_label = instruction.get("label")
            
            # notify Part 2 of branch result
            self.tomasulo_interface.notify_branch_result(
                rob_index,
                branch_result["taken"],
                branch_result["target"],
                branch_label
            )
            
            # result for BEQ is the branch outcome info
            result = branch_result
        
        elif inst_type in ["CALL", "RET"]:
            # handle call/ret
            if inst_type == "CALL":
                label_offset = fu.operands.get("immediate", 0)
                pc = fu.operands.get("pc", 0)
                call_result = self.branch_evaluator.evaluate_call(label_offset, pc)
                # Get label from instruction for CALL target resolution
                call_label = instruction.get("label")
                
                # notify Part 2 of CALL target (unconditional branch)
                self.tomasulo_interface.notify_branch_result(
                    rob_index,
                    True,  # CALL is always taken
                    call_result["target"],
                    call_label
                )
                result = call_result
            elif inst_type == "RET":
                r1_val = fu.operands.get("Vj", 0)
                ret_result = self.branch_evaluator.evaluate_ret(r1_val)
                # notify Part 2 of RET target (unconditional branch)
                self.tomasulo_interface.notify_branch_result(
                    rob_index,
                    True,  # RET is always taken
                    ret_result["target"]
                )
                result = ret_result
        
        elif inst_type == "STORE":
            # for STORE, we need to handle the memory write
            # the result from FU is the address
            store_address = result
            store_value = fu.get_store_value() if hasattr(fu, 'get_store_value') else fu.operands.get("Vj", 0)
            # store the value for writeback to handle
            result = {
                "address": store_address,
                "value": store_value,
            }
        
        # add result to write-back queue
        if rob_index is not None:
            self.writeback_stage.add_result(
                rob_index,
                result,
                inst_type,
                instruction,
                rs_entry_id
            )
        
        # reset FU
        fu.reset()
    
    def _start_ready_instructions(self) -> None:
        """check RS entries for ready operands and start execution"""
        # get RS entries with ready operands from Part 2
        ready_rs_entries = self.tomasulo_interface.get_ready_rs_entries()
        
        for rs_entry in ready_rs_entries:
            instruction = rs_entry.get("instruction")
            if instruction is None:
                continue
            
            inst_type = instruction.get("op", "")
            rs_entry_id = rs_entry.get("id")
            
            # check if FU is available
            if not self.fu_pool.is_available(inst_type):
                continue
            
            # get available FU
            fu = self.fu_pool.get_available_fu(inst_type)
            if fu is None:
                continue
            
            # get operands from Part 2
            operands = self.tomasulo_interface.get_rs_operands(rs_entry)
            
            # start execution
            fu.start_execution(instruction, rs_entry_id, operands)
            
            # record start execution timing
            instr_id = instruction.get("instr_id")
            if instr_id is not None:
                self.timing_tracker.record_start_exec(instr_id, self.current_cycle)
            
            # mark RS entry as executing in Part 2
            self.tomasulo_interface.mark_rs_executing(rs_entry_id)
    
    def is_fu_available(self, instruction_type: str) -> bool:
        """
        check if FU is available for instruction type
        
        args:
            instruction_type: type of instruction
            
        returns:
            True if FU available, False otherwise
        """
        return self.fu_pool.is_available(instruction_type)
    
    def get_execution_state(self) -> Dict[str, Any]:
        """
        get current execution state for GUI visualization
        
        returns:
            dictionary with execution state information
        """
        return {
            "current_cycle": self.current_cycle,
            "fu_status": self.fu_pool.get_all_fu_status(),
            "cdb_state": self.cdb.get_state(),
            "writeback_queue_length": self.writeback_stage.get_queue_length(),
        }
    
    def get_fu_status(self) -> Dict[str, list]:
        """
        get status of all functional units
        
        returns:
            dictionary mapping instruction types to FU status lists
        """
        return self.fu_pool.get_all_fu_status()
    
    def get_cdb_state(self) -> Dict[str, Any]:
        """
        get current CDB state
        
        returns:
            dictionary with CDB state information
        """
        return self.cdb.get_state()
    
    def get_timing_info(self) -> Dict[int, Dict[str, Optional[int]]]:
        """
        get timing information for all instructions
        
        returns:
            dictionary mapping instruction_id to timing info
        """
        return self.timing_tracker.get_all_timing()
    
    def get_timing_tracker(self) -> TimingTracker:
        """
        get timing tracker instance (for Part 2 to record commit)
        
        returns:
            TimingTracker instance
        """
        return self.timing_tracker
    
    def flush_functional_units(self, rs_entry_ids: List[str]) -> None:
        """
        flush functional units that are executing instructions for the given RS entry IDs
        
        args:
            rs_entry_ids: list of RS entry IDs (RS names) to flush
        """
        if rs_entry_ids:
            self.fu_pool.flush_rs_entries(rs_entry_ids)

