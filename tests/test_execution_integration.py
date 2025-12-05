"""integration tests for execution engine with mock interfaces"""

import unittest
from src.execution.execution_manager import ExecutionManager
from src.execution.timing_tracker import TimingTracker


class MockMemoryInterface:
    """mock memory interface for testing"""
    
    def __init__(self):
        self.memory = {}
    
    def read_memory(self, address: int) -> int:
        """read from memory"""
        return self.memory.get(address, 0)
    
    def write_memory(self, address: int, value: int) -> None:
        """write to memory"""
        self.memory[address] = value & 0xFFFF


class MockTomasuloInterface:
    """mock tomasulo interface for testing"""
    
    def __init__(self):
        self.rs_entries = []
        self.rob_values = {}
        self.forwarded_values = []
        self.rat_updates = []
        self.branch_notifications = []
        self.executing_rs = set()
        self.rob_counter = 0
    
    def get_ready_rs_entries(self):
        """get RS entries with ready operands"""
        ready = []
        for rs_entry in self.rs_entries:
            if rs_entry.get("ready") and rs_entry.get("id") not in self.executing_rs:
                ready.append(rs_entry)
        return ready
    
    def get_rs_operands(self, rs_entry):
        """get operand values for RS entry"""
        return rs_entry.get("operands", {})
    
    def update_rob_value(self, rob_index: int, value) -> None:
        """update ROB with result"""
        self.rob_values[rob_index] = value
    
    def forward_to_rs(self, rob_index: int, value) -> None:
        """forward value to waiting RS entries"""
        self.forwarded_values.append((rob_index, value))
        # update any RS entries waiting for this ROB index
        for rs_entry in self.rs_entries:
            operands = rs_entry.get("operands", {})
            if operands.get("Qj") == rob_index:
                operands["Vj"] = value
                operands["Qj"] = None
            if operands.get("Qk") == rob_index:
                operands["Vk"] = value
                operands["Qk"] = None
    
    def update_rat(self, rob_index: int, value) -> None:
        """update RAT"""
        self.rat_updates.append((rob_index, value))
    
    def notify_branch_result(self, rob_index: int, taken: bool, target: int) -> None:
        """notify branch result"""
        self.branch_notifications.append({
            "rob_index": rob_index,
            "taken": taken,
            "target": target
        })
    
    def mark_rs_executing(self, rs_entry_id: int) -> None:
        """mark RS as executing"""
        self.executing_rs.add(rs_entry_id)
    
    def get_oldest_ready_rob_index(self):
        """get oldest ROB index for arbitration"""
        if self.rob_values:
            return min(self.rob_values.keys())
        return None
    
    def add_rs_entry(self, instruction, operands, ready=True):
        """helper to add an RS entry for testing"""
        rs_id = len(self.rs_entries)
        rob_index = self.rob_counter
        self.rob_counter += 1
        
        entry = {
            "id": rs_id,
            "instruction": instruction,
            "operands": operands,
            "ready": ready,
        }
        self.rs_entries.append(entry)
        return rs_id, rob_index


class TestExecutionIntegration(unittest.TestCase):
    """test execution engine with mock interfaces"""
    
    def setUp(self):
        self.memory = MockMemoryInterface()
        self.tomasulo = MockTomasuloInterface()
        self.exec_manager = ExecutionManager(self.memory, self.tomasulo)
    
    def test_add_instruction_execution(self):
        """test ADD instruction execution"""
        # add instruction to RS
        instruction = {
            "op": "ADD",
            "instr_id": 1,
            "rob_index": 0,
        }
        operands = {"Vj": 10, "Vk": 5, "Qj": None, "Qk": None}
        rs_id, rob_index = self.tomasulo.add_rs_entry(instruction, operands)
        instruction["rob_index"] = rob_index
        
        # execute cycles
        self.exec_manager.execute_cycle(1)  # should start execution
        
        # check that execution started
        self.assertIn(rs_id, self.tomasulo.executing_rs)
        
        # advance 2 cycles (ADD takes 2 cycles)
        self.exec_manager.execute_cycle(2)  # cycle 2 of execution
        self.exec_manager.execute_cycle(3)  # should finish and write-back
        
        # check timing
        timing = self.exec_manager.get_timing_info()
        self.assertIsNotNone(timing.get(1))
        self.assertEqual(timing[1]["start_exec"], 1)
        self.assertEqual(timing[1]["finish_exec"], 3)
        self.assertEqual(timing[1]["write"], 3)
        
        # check that result was forwarded
        self.assertEqual(len(self.tomasulo.forwarded_values), 1)
        self.assertEqual(self.tomasulo.forwarded_values[0][1], 15)
    
    def test_mul_instruction_execution(self):
        """test MUL instruction execution (12 cycles)"""
        instruction = {
            "op": "MUL",
            "instr_id": 2,
            "rob_index": 1,
        }
        operands = {"Vj": 5, "Vk": 4, "Qj": None, "Qk": None}
        rs_id, rob_index = self.tomasulo.add_rs_entry(instruction, operands)
        instruction["rob_index"] = rob_index
        
        # start execution
        self.exec_manager.execute_cycle(1)
        self.assertIn(rs_id, self.tomasulo.executing_rs)
        
        # advance 12 cycles
        for cycle in range(2, 14):
            self.exec_manager.execute_cycle(cycle)
        
        # should finish at cycle 13
        timing = self.exec_manager.get_timing_info()
        self.assertEqual(timing[2]["finish_exec"], 13)
        self.assertEqual(timing[2]["write"], 13)
        self.assertEqual(self.tomasulo.rob_values[rob_index], 20)
    
    def test_load_instruction_execution(self):
        """test LOAD instruction execution (6 cycles)"""
        # set up memory
        self.memory.write_memory(100, 42)
        
        instruction = {
            "op": "LOAD",
            "instr_id": 3,
        }
        operands = {"Vj": 100, "immediate": 0, "Qj": None}
        rs_id, rob_index = self.tomasulo.add_rs_entry(instruction, operands)
        instruction["rob_index"] = rob_index
        
        # execute 6 cycles
        for cycle in range(1, 8):
            self.exec_manager.execute_cycle(cycle)
        
        # should have loaded value
        timing = self.exec_manager.get_timing_info()
        self.assertEqual(timing[3]["finish_exec"], 7)
        self.assertEqual(self.tomasulo.rob_values[rob_index], 42)
    
    def test_store_instruction_execution(self):
        """test STORE instruction execution"""
        instruction = {
            "op": "STORE",
            "instr_id": 4,
            "rob_index": 3,
        }
        operands = {"Vj": 99, "Vk": 200, "immediate": 0, "Qj": None, "Qk": None}
        rs_id, rob_index = self.tomasulo.add_rs_entry(instruction, operands)
        instruction["rob_index"] = rob_index
        
        # execute 6 cycles
        for cycle in range(1, 8):
            self.exec_manager.execute_cycle(cycle)
        
        # check memory was written
        self.assertEqual(self.memory.read_memory(200), 99)
        
        # STORE shouldn't forward a register value
        store_forwards = [v for v in self.tomasulo.forwarded_values if v[0] == rob_index]
        self.assertEqual(len(store_forwards), 0)
    
    def test_beq_instruction_execution(self):
        """test BEQ instruction execution and branch notification"""
        instruction = {
            "op": "BEQ",
            "instr_id": 5,
            "rob_index": 4,
        }
        operands = {"Vj": 10, "Vk": 10, "immediate": 5, "pc": 100, "Qj": None, "Qk": None}
        rs_id, rob_index = self.tomasulo.add_rs_entry(instruction, operands)
        instruction["rob_index"] = rob_index
        
        # execute 1 cycle (BEQ takes 1 cycle)
        self.exec_manager.execute_cycle(1)
        self.exec_manager.execute_cycle(2)  # write-back
        
        # check branch notification
        self.assertEqual(len(self.tomasulo.branch_notifications), 1)
        notification = self.tomasulo.branch_notifications[0]
        self.assertEqual(notification["rob_index"], rob_index)
        self.assertTrue(notification["taken"])
        self.assertEqual(notification["target"], 106)  # PC + 1 + offset
    
    def test_cdb_single_writeback(self):
        """test that CDB only allows one write-back per cycle"""
        # add two instructions that finish at the same time
        instruction1 = {
            "op": "ADD",
            "instr_id": 6,
            "rob_index": 5,
        }
        operands1 = {"Vj": 1, "Vk": 1, "Qj": None, "Qk": None}
        rs_id1, rob_index1 = self.tomasulo.add_rs_entry(instruction1, operands1)
        instruction1["rob_index"] = rob_index1
        
        instruction2 = {
            "op": "ADD",
            "instr_id": 7,
            "rob_index": 6,
        }
        operands2 = {"Vj": 2, "Vk": 2, "Qj": None, "Qk": None}
        rs_id2, rob_index2 = self.tomasulo.add_rs_entry(instruction2, operands2)
        instruction2["rob_index"] = rob_index2
        
        # start both
        self.exec_manager.execute_cycle(1)
        
        # both should finish at cycle 3
        self.exec_manager.execute_cycle(2)
        self.exec_manager.execute_cycle(3)  # first one writes back
        
        # check that only one wrote back
        forwarded_count = len(self.tomasulo.forwarded_values)
        self.assertEqual(forwarded_count, 1)
        
        # next cycle should write back the second
        self.exec_manager.execute_cycle(4)
        forwarded_count = len(self.tomasulo.forwarded_values)
        self.assertEqual(forwarded_count, 2)
    
    def test_operand_forwarding(self):
        """test that results are forwarded to waiting instructions"""
        # first instruction produces a value
        instruction1 = {
            "op": "ADD",
            "instr_id": 8,
        }
        operands1 = {"Vj": 10, "Vk": 5, "Qj": None, "Qk": None}
        rs_id1, rob_index1 = self.tomasulo.add_rs_entry(instruction1, operands1)
        instruction1["rob_index"] = rob_index1
        
        # second instruction waits for first
        instruction2 = {
            "op": "ADD",
            "instr_id": 9,
        }
        operands2 = {"Vj": None, "Vk": 3, "Qj": rob_index1, "Qk": None}
        rs_id2, rob_index2 = self.tomasulo.add_rs_entry(instruction2, operands2, ready=False)
        instruction2["rob_index"] = rob_index2
        
        # mark second instruction as ready after forwarding (simulate Part 2 behavior)
        # in real implementation, Part 2 would check if operands are ready after forwarding
        
        # execute first instruction
        self.exec_manager.execute_cycle(1)
        self.exec_manager.execute_cycle(2)
        self.exec_manager.execute_cycle(3)  # first finishes and writes back
        
        # check that second instruction's operand was updated
        updated_operands = self.tomasulo.rs_entries[rs_id2]["operands"]
        self.assertEqual(updated_operands["Vj"], 15)
        self.assertIsNone(updated_operands["Qj"])
        
        # mark as ready now that operand is available
        self.tomasulo.rs_entries[rs_id2]["ready"] = True
        
        # now second instruction should be ready
        self.exec_manager.execute_cycle(4)  # should start second instruction
        self.assertIn(rs_id2, self.tomasulo.executing_rs)
    
    def test_fu_availability(self):
        """test FU availability checking"""
        # check availability
        self.assertTrue(self.exec_manager.is_fu_available("ADD"))
        self.assertTrue(self.exec_manager.is_fu_available("MUL"))
        
        # use all ADD/SUB units
        for i in range(4):
            instruction = {
                "op": "ADD",
                "instr_id": 10 + i,
                "rob_index": 9 + i,
            }
            operands = {"Vj": 1, "Vk": 1, "Qj": None, "Qk": None}
            rs_id, rob_index = self.tomasulo.add_rs_entry(instruction, operands)
            instruction["rob_index"] = rob_index
        
        # start all 4
        self.exec_manager.execute_cycle(1)
        
        # should be unavailable now
        self.assertFalse(self.exec_manager.is_fu_available("ADD"))
    
    def test_execution_state(self):
        """test getting execution state for GUI"""
        state = self.exec_manager.get_execution_state()
        
        self.assertIn("current_cycle", state)
        self.assertIn("fu_status", state)
        self.assertIn("cdb_state", state)
        self.assertIn("writeback_queue_length", state)
        
        # check FU status structure
        fu_status = state["fu_status"]
        self.assertIn("ADD", fu_status)
        self.assertIn("MUL", fu_status)
    
    def test_call_instruction(self):
        """test CALL instruction execution"""
        instruction = {
            "op": "CALL",
            "instr_id": 11,
            "rob_index": 13,
        }
        operands = {"immediate": 10, "pc": 100, "Qj": None, "Qk": None}
        rs_id, rob_index = self.tomasulo.add_rs_entry(instruction, operands)
        instruction["rob_index"] = rob_index
        
        # execute
        self.exec_manager.execute_cycle(1)
        self.exec_manager.execute_cycle(2)  # write-back
        
        # check branch notification
        self.assertEqual(len(self.tomasulo.branch_notifications), 1)
        notification = self.tomasulo.branch_notifications[0]
        self.assertTrue(notification["taken"])
        self.assertEqual(notification["target"], 111)  # PC + 1 + offset


if __name__ == "__main__":
    unittest.main()

