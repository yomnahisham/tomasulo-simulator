"""
example usage of execution engine

this file shows how the execution engine integrates with Parts 1 and 2
note: this is just an examplem
"""

from execution_manager import ExecutionManager


class MockMemoryInterface:
    """mock memory interface (Part 1 responsibility)"""
    
    def read_memory(self, address: int) -> int:
        """read from memory - to be implemented by Part 1"""
        return 0
    
    def write_memory(self, address: int, value: int) -> None:
        """write to memory - to be implemented by Part 1"""
        pass


class MockTomasuloInterface:
    """mock tomasulo interface (Part 2 responsibility)"""
    
    def get_ready_rs_entries(self):
        """get ready RS entries - to be implemented by Part 2"""
        return []
    
    def get_rs_operands(self, rs_entry):
        """get RS operands - to be implemented by Part 2"""
        return {}
    
    def update_rob_value(self, rob_index: int, value) -> None:
        """update ROB value - to be implemented by Part 2"""
        pass
    
    def forward_to_rs(self, rob_index: int, value) -> None:
        """forward to RS - to be implemented by Part 2"""
        pass
    
    def update_rat(self, rob_index: int, value) -> None:
        """update RAT - to be implemented by Part 2"""
        pass
    
    def notify_branch_result(self, rob_index: int, taken: bool, target: int) -> None:
        """notify branch result - to be implemented by Part 2"""
        pass
    
    def mark_rs_executing(self, rs_entry_id: int) -> None:
        """mark RS as executing - to be implemented by Part 2"""
        pass


def example_usage():
    """example of how to use the execution engine"""
    
    # create interfaces (these will be implemented by Parts 1 and 2)
    memory_interface = MockMemoryInterface()
    tomasulo_interface = MockTomasuloInterface()
    
    # create execution manager
    exec_manager = ExecutionManager(memory_interface, tomasulo_interface)
    
    # simulate cycles
    max_cycles = 100
    for cycle in range(1, max_cycles + 1):
        # execute one cycle
        exec_manager.execute_cycle(cycle)
        
        # get execution state for GUI visualization
        state = exec_manager.get_execution_state()
        print(f"Cycle {cycle}: {state['writeback_queue_length']} results in writeback queue")
        
        # get timing information
        timing = exec_manager.get_timing_info()
        # timing can be used to generate the timing table output
    
    # get final timing information
    final_timing = exec_manager.get_timing_info()
    return final_timing


if __name__ == "__main__":
    example_usage()


