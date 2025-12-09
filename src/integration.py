"""
Complete integration of Tomasulo Simulator components

This script demonstrates the full integration:
- Parser reads assembly files
- IssueUnit issues instructions
- TomasuloCore manages RS/ROB/RAT
- ExecutionManager executes instructions
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.interfaces.parser import Parser
from src.interfaces.issue_unit import IssueUnit
from src.interfaces.tomasulo_interface import TomasuloCore
from src.interfaces.register_interface import RegisterFile
from src.interfaces.memory_interface import Memory
from src.interfaces.instruction import Instruction
from src.execution.execution_manager import ExecutionManager
from src.execution.timing_tracker import TimingTracker


class IntegratedSimulator:
    """Complete Tomasulo simulator with all components integrated"""
    
    def __init__(self, assembly_file: str):
        """
        Initialize the integrated simulator
        
        Args:
            assembly_file: path to assembly file to execute
        """
        # Parse assembly file
        parser = Parser()
        self.instructions = parser.parse(assembly_file)
        
        # Create core components
        self.register_file = RegisterFile()
        self.memory = Memory()
        self.timing_tracker = TimingTracker()
        self.tomasulo_core = TomasuloCore(
            reg_file=self.register_file,
            mem=self.memory,
            reservation_stations=None,  # Use defaults
            rob=None,  # Use defaults
            rat=None  # Use defaults
        )
        
        # Create issue unit
        self.issue_unit = IssueUnit(
            instructions=self.instructions,
            register_file=self.register_file,
            timing_tracker=self.timing_tracker,
            reservation_stations=self.tomasulo_core.reservation_stations,
            rob=self.tomasulo_core.rob,
            rat=self.tomasulo_core.rat
        )
        
        # Create execution manager
        self.exec_manager = ExecutionManager(
            memory_interface=self.memory,
            tomasulo_interface=self.tomasulo_core
        )
        
        # Share timing tracker
        self.exec_manager.timing_tracker = self.timing_tracker
        
        self.current_cycle = 0
        self.max_cycles = 1000
        self.initial_assembly_file = assembly_file
    
    def run(self, verbose: bool = False) -> dict:
        """
        Run the complete simulation
        
        Args:
            verbose: if True, print detailed cycle information
            
        Returns:
            dictionary with final timing information
        """
        print(f"\n{'='*80}")
        print(f"Starting Tomasulo Simulator")
        print(f"Instructions to execute: {len(self.instructions)}")
        print(f"{'='*80}\n")
        
        while self.current_cycle < self.max_cycles:
            self.current_cycle += 1
            
            if verbose:
                print(f"\n--- CYCLE {self.current_cycle} ---")
            
            # Step 1: Issue next instruction (if available)
            if self.issue_unit.has_instructions():
                issued, _ = self.issue_unit.issue_next(self.current_cycle)
                if issued and verbose:
                    print(f"Issued: {issued.get_name()}")
            
            # Step 2: Execute one cycle
            self.exec_manager.execute_cycle(self.current_cycle)
            
            # Step 3: Commit if possible
            committed = self.tomasulo_core.commit_rob_entry()
            if committed and verbose:
                dest, value = committed
                print(f"Committed: ROB[{dest}] = {value}")
            
            # Check if simulation is complete
            if self._is_complete():
                break
        
        # Get final timing information
        timing_info = self.timing_tracker.get_all_timing()
        
        print(f"\n{'='*80}")
        print(f"Simulation Complete after {self.current_cycle} cycles")
        print(f"{'='*80}\n")
        
        return timing_info
    
    def _is_complete(self) -> bool:
        """Check if simulation is complete"""
        # All instructions issued
        if self.issue_unit.has_instructions():
            return False
        
        # All instructions committed
        if self.tomasulo_core.rob.buffer.count > 0:
            return False
        
        # No functional units executing
        fu_pool = self.exec_manager.fu_pool
        all_fus = (
            fu_pool.add_sub_units +
            fu_pool.nand_units +
            fu_pool.mul_units +
            fu_pool.load_units +
            fu_pool.store_units +
            fu_pool.beq_units +
            fu_pool.call_ret_units
        )
        if any(fu.is_busy() for fu in all_fus):
            return False
        
        # No reservation stations busy
        if any(rs.busy for rs in self.tomasulo_core.reservation_stations.values()):
            return False
        
        return True
    
    def print_timing_table(self):
        """Print the timing table for all instructions"""
        timing_info = self.timing_tracker.get_all_timing()
        
        print("\n" + "="*80)
        print("TIMING TABLE")
        print("="*80)
        print(f"{'ID':<5} {'Instruction':<15} {'Issue':<8} {'Exec':<8} {'Finish':<8} {'Write':<8} {'Commit':<8}")
        print("-"*80)
        
        for instr_id, timing in sorted(timing_info.items()):
            # Find instruction name
            instr = next((i for i in self.instructions if i.get_instr_id() == instr_id), None)
            name = instr.get_name() if instr else "UNKNOWN"
            
            issue = timing.get("issue", "-")
            start_exec = timing.get("start_exec", "-")
            finish_exec = timing.get("finish_exec", "-")
            write = timing.get("write", "-")
            commit = timing.get("commit", "-")
            
            print(f"{instr_id:<5} {name:<15} {issue:<8} {start_exec:<8} {finish_exec:<8} {write:<8} {commit:<8}")
        
        print("="*80 + "\n")
    
    def print_final_state(self):
        """Print final state of registers and memory"""
        print("\n" + "="*80)
        print("FINAL STATE")
        print("="*80)
        
        print("\nRegisters:")
        for i in range(8):
            val = self.register_file.read(i)
            if val != 0:
                print(f"  R{i} = {val}")
        
        print("\nMemory (non-zero values):")
        # Memory interface doesn't expose all memory, so we'll just note it
        print("  (Memory state available through memory interface)")
        
        print("\nROB:")
        if self.tomasulo_core.rob.buffer.count == 0:
            print("  (empty)")
        else:
            self.tomasulo_core.rob.print()
        
        print("="*80 + "\n")
    
    def get_current_state(self) -> dict:
        """
        Get complete processor state for GUI visualization
        
        Returns:
            Dictionary containing all processor state information
        """
        # Get instruction statuses
        timing_info = self.timing_tracker.get_all_timing()
        instructions_state = []
        for instr in self.instructions:
            instr_id = instr.get_instr_id()
            timing = timing_info.get(instr_id, {})
            
            # Determine instruction status
            # Stages: pending -> issued -> executing -> write-back -> commit
            issue_cycle = timing.get("issue")
            start_exec_cycle = timing.get("start_exec")
            finish_exec_cycle = timing.get("finish_exec")
            write_cycle = timing.get("write")
            commit_cycle = timing.get("commit")
            
            if commit_cycle is not None:
                status = "commit"
            elif write_cycle is not None:
                status = "write-back"
            elif finish_exec_cycle is not None:
                # Finished execution but not yet written back
                status = "executing"  # Still in execution phase until write-back
            elif start_exec_cycle is not None:
                # If both issue and start_exec happened in the same cycle, show "issued" 
                # only in that cycle, then "executing" in subsequent cycles
                if issue_cycle is not None and start_exec_cycle == issue_cycle:
                    if self.current_cycle == issue_cycle:
                        status = "issued"
                    else:
                        status = "executing"
                else:
                    status = "executing"
            elif issue_cycle is not None:
                status = "issued"
            else:
                status = "pending"
            
            instructions_state.append({
                "id": instr_id,
                "name": instr.get_name(),
                "rA": instr.get_rA(),
                "rB": instr.get_rB(),
                "rC": instr.get_rC(),
                "immediate": instr.get_immediate(),
                "label": instr.get_label(),
                "status": status,
                "timing": timing
            })
        
        # Get reservation stations state
        rs_state = {}
        for rs_name, rs in self.tomasulo_core.reservation_stations.items():
            rs_dict = {
                "name": rs_name,
                "busy": rs.busy,
                "state": rs.state if hasattr(rs, 'state') else None,
            }
            
            if rs.busy:
                if hasattr(rs, 'instruction') and rs.instruction:
                    if isinstance(rs.instruction, Instruction):
                        rs_dict["instruction"] = {
                            "id": rs.instruction.get_instr_id(),
                            "name": rs.instruction.get_name(),
                            "rA": rs.instruction.get_rA(),
                            "rB": rs.instruction.get_rB(),
                            "rC": rs.instruction.get_rC(),
                        }
                    else:
                        rs_dict["instruction"] = rs.instruction
                
                if hasattr(rs, 'Op'):
                    rs_dict["op"] = rs.Op
                if hasattr(rs, 'dest'):
                    rs_dict["dest"] = rs.dest
                if hasattr(rs, 'Vj'):
                    rs_dict["Vj"] = rs.Vj
                if hasattr(rs, 'Vk'):
                    rs_dict["Vk"] = rs.Vk
                if hasattr(rs, 'Qj'):
                    rs_dict["Qj"] = rs.Qj
                if hasattr(rs, 'Qk'):
                    rs_dict["Qk"] = rs.Qk
                if hasattr(rs, 'A'):
                    rs_dict["A"] = rs.A
                if hasattr(rs, 'PC'):
                    rs_dict["PC"] = rs.PC
            
            rs_state[rs_name] = rs_dict
        
        # Get ROB state
        rob_entries = []
        if self.tomasulo_core.rob.buffer.count > 0:
            entries = self.tomasulo_core.rob.buffer.traverse()
            for i, entry in enumerate(entries):
                if entry:
                    # Calculate actual index in circular buffer
                    actual_index = (self.tomasulo_core.rob.buffer.head + i) % self.tomasulo_core.rob.max_size
                    rob_entries.append({
                        "index": actual_index,
                        "name": entry.name,
                        "dest": entry.dest,
                        "ready": entry.ready,
                        "value": entry.value,
                        "is_head": (i == 0),
                        "is_tail": (i == len(entries) - 1)
                    })
        
        # Get RAT state
        rat_state = [self.tomasulo_core.rat[i] for i in range(8)]
        
        # Get register file state
        registers_state = [self.register_file.read(i) for i in range(8)]
        
        # Get memory state (non-zero addresses)
        memory_dump = self.memory.dump()
        memory_state = {addr: val for addr, val in memory_dump.items() if val != 0}
        
        # Get functional units state
        fu_state = self.exec_manager.get_fu_status()
        
        # Get CDB state
        cdb_state = self.exec_manager.get_cdb_state()
        
        return {
            "cycle": self.current_cycle,
            "instructions": instructions_state,
            "reservation_stations": rs_state,
            "rob": rob_entries,
            "rat": rat_state,
            "registers": registers_state,
            "memory": memory_state,
            "functional_units": fu_state,
            "cdb": cdb_state,
            "timing": timing_info,
            "is_complete": self._is_complete(),
            "has_instructions": self.issue_unit.has_instructions()
        }
    
    def step_cycle(self) -> dict:
        """
        Execute one cycle and return new state
        
        Returns:
            Dictionary containing updated processor state
        """
        # Check if already complete - if so, just return current state
        if self._is_complete():
            return self.get_current_state()
        
        self.current_cycle += 1
        
        # Step 1: Issue next instruction (if available)
        issued_instr = None
        if self.issue_unit.has_instructions():
            issued_instr, _ = self.issue_unit.issue_next(self.current_cycle)
        
        # Step 2: Execute one cycle
        self.exec_manager.execute_cycle(self.current_cycle)
        
        # Step 3: Commit if possible (can commit multiple entries per cycle)
        committed = None
        while True:
            commit_result = self.tomasulo_core.commit_rob_entry()
            if commit_result is None:
                break
            committed = commit_result  # Track the last committed entry
        
        # Return updated state
        state = self.get_current_state()
        state["last_issued"] = issued_instr.get_name() if issued_instr else None
        state["last_committed"] = committed[0] if committed else None
        
        return state
    
    def reset(self) -> dict:
        """
        Reset simulator to initial state
        
        Returns:
            Dictionary containing reset processor state
        """
        # Reinitialize all components
        parser = Parser()
        self.instructions = parser.parse(self.initial_assembly_file)
        
        # Reset components
        self.register_file = RegisterFile()
        self.memory = Memory()
        self.timing_tracker = TimingTracker()
        self.tomasulo_core = TomasuloCore(
            reg_file=self.register_file,
            mem=self.memory,
            reservation_stations=None,
            rob=None,
            rat=None
        )
        
        # Recreate issue unit
        self.issue_unit = IssueUnit(
            instructions=self.instructions,
            register_file=self.register_file,
            timing_tracker=self.timing_tracker,
            reservation_stations=self.tomasulo_core.reservation_stations,
            rob=self.tomasulo_core.rob,
            rat=self.tomasulo_core.rat
        )
        
        # Recreate execution manager
        self.exec_manager = ExecutionManager(
            memory_interface=self.memory,
            tomasulo_interface=self.tomasulo_core
        )
        self.exec_manager.timing_tracker = self.timing_tracker
        
        self.current_cycle = 0
        
        return self.get_current_state()
    
    def load_program(self, assembly_file: str) -> dict:
        """
        Load a new program and reset simulator
        
        Args:
            assembly_file: path to assembly file to load
            
        Returns:
            Dictionary containing reset processor state with new program
        """
        if not os.path.exists(assembly_file):
            raise FileNotFoundError(f"Assembly file '{assembly_file}' not found")
        
        self.initial_assembly_file = assembly_file
        return self.reset()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python -m src.integration <assembly_file> [--verbose]")
        print("Example: python -m src.integration testcases/test1.s")
        sys.exit(1)
    
    assembly_file = sys.argv[1]
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    if not os.path.exists(assembly_file):
        print(f"Error: Assembly file '{assembly_file}' not found")
        sys.exit(1)
    
    # Create and run simulator
    simulator = IntegratedSimulator(assembly_file)
    timing_info = simulator.run(verbose=verbose)
    
    # Print results
    simulator.print_timing_table()
    simulator.print_final_state()
    
    return timing_info


if __name__ == "__main__":
    main()


