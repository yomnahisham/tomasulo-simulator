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
                issued = self.issue_unit.issue_next(self.current_cycle)
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
        if self.tomasulo_core.rob.buffer.size() > 0:
            return False
        
        # No functional units executing
        if any(fu.is_busy() for fu in self.exec_manager.fu_pool._functional_units):
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
        if self.tomasulo_core.rob.buffer.size() == 0:
            print("  (empty)")
        else:
            self.tomasulo_core.rob.print()
        
        print("="*80 + "\n")


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
