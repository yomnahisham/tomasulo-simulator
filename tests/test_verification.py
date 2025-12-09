"""detailed verification tests to check correctness of execution engine"""

import unittest
from src.execution.execution_manager import ExecutionManager
from src.execution.timing_tracker import TimingTracker


class MockMemoryInterface:
    """mock memory interface for testing"""
    
    def __init__(self):
        self.memory = {}
        self.read_count = 0
        self.write_count = 0
    
    def read_memory(self, address: int) -> int:
        """read from memory"""
        self.read_count += 1
        return self.memory.get(address, 0)
    
    def write_memory(self, address: int, value: int) -> None:
        """write to memory"""
        self.write_count += 1
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
        self.ready_checks = []
    
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


class TestExecutionVerification(unittest.TestCase):
    """verify correctness of execution engine behavior"""
    
    def setUp(self):
        self.memory = MockMemoryInterface()
        self.tomasulo = MockTomasuloInterface()
        self.exec_manager = ExecutionManager(self.memory, self.tomasulo)
    
    def test_add_timing_correctness(self):
        """verify ADD instruction timing is correct (2 cycles)"""
        instruction = {"op": "ADD", "instr_id": 1}
        operands = {"Vj": 10, "Vk": 5, "Qj": None, "Qk": None}
        rs_id, rob_index = self.tomasulo.add_rs_entry(instruction, operands)
        instruction["rob_index"] = rob_index
        
        # cycle 1: start execution
        self.exec_manager.execute_cycle(1)
        timing = self.exec_manager.get_timing_info()
        self.assertEqual(timing[1]["start_exec"], 1, "ADD should start execution at cycle 1")
        self.assertIsNone(timing[1]["finish_exec"], "ADD should not finish at cycle 1")
        
        # cycle 2: still executing (2 cycles total)
        self.exec_manager.execute_cycle(2)
        timing = self.exec_manager.get_timing_info()
        self.assertEqual(timing[1]["start_exec"], 1)
        self.assertIsNone(timing[1]["finish_exec"], "ADD should not finish at cycle 2 (needs 2 cycles)")
        
        # cycle 3: finishes and writes back
        self.exec_manager.execute_cycle(3)
        timing = self.exec_manager.get_timing_info()
        self.assertEqual(timing[1]["start_exec"], 1, "Start exec should be cycle 1")
        self.assertEqual(timing[1]["finish_exec"], 3, "Finish exec should be cycle 3 (after 2 cycles)")
        self.assertEqual(timing[1]["write"], 3, "Write should be cycle 3 (same cycle as finish)")
        
        # verify result
        self.assertEqual(self.tomasulo.rob_values[rob_index], 15, "ADD 10+5 should equal 15")
        print(f"✓ ADD timing: start={timing[1]['start_exec']}, finish={timing[1]['finish_exec']}, write={timing[1]['write']}, result={self.tomasulo.rob_values[rob_index]}")
    
    def test_mul_timing_correctness(self):
        """verify MUL instruction timing is correct (12 cycles)"""
        instruction = {"op": "MUL", "instr_id": 2}
        operands = {"Vj": 5, "Vk": 4, "Qj": None, "Qk": None}
        rs_id, rob_index = self.tomasulo.add_rs_entry(instruction, operands)
        instruction["rob_index"] = rob_index
        
        # start execution
        self.exec_manager.execute_cycle(1)
        timing = self.exec_manager.get_timing_info()
        self.assertEqual(timing[2]["start_exec"], 1)
        
        # should finish at cycle 13 (1 + 12 cycles)
        for cycle in range(2, 14):
            self.exec_manager.execute_cycle(cycle)
        
        timing = self.exec_manager.get_timing_info()
        self.assertEqual(timing[2]["start_exec"], 1, "Start exec should be cycle 1")
        self.assertEqual(timing[2]["finish_exec"], 13, "Finish exec should be cycle 13 (after 12 cycles)")
        self.assertEqual(timing[2]["write"], 13, "Write should be cycle 13")
        
        # verify result (5 * 4 = 20, but 16-bit so 20)
        result = self.tomasulo.rob_values[rob_index]
        self.assertEqual(result, 20, "MUL 5*4 should equal 20")
        print(f"✓ MUL timing: start={timing[2]['start_exec']}, finish={timing[2]['finish_exec']}, write={timing[2]['write']}, result={result}")
    
    def test_load_timing_and_memory_access(self):
        """verify LOAD instruction timing and memory access"""
        # set up memory
        self.memory.write_memory(100, 42)
        
        instruction = {"op": "LOAD", "instr_id": 3}
        operands = {"Vj": 100, "immediate": 0, "Qj": None}
        rs_id, rob_index = self.tomasulo.add_rs_entry(instruction, operands)
        instruction["rob_index"] = rob_index
        
        # LOAD takes 6 cycles: 2 for address calc + 4 for memory read
        for cycle in range(1, 8):
            self.exec_manager.execute_cycle(cycle)
        
        timing = self.exec_manager.get_timing_info()
        self.assertEqual(timing[3]["start_exec"], 1)
        self.assertEqual(timing[3]["finish_exec"], 7, "LOAD should finish at cycle 7 (6 cycles)")
        self.assertEqual(timing[3]["write"], 7)
        
        # verify memory was read and value is correct
        self.assertEqual(self.tomasulo.rob_values[rob_index], 42, "LOAD should read value 42 from address 100")
        self.assertEqual(self.memory.read_count, 1, "Memory should be read once")
        print(f"✓ LOAD timing: start={timing[3]['start_exec']}, finish={timing[3]['finish_exec']}, write={timing[3]['write']}, loaded_value={self.tomasulo.rob_values[rob_index]}")
    
    def test_store_timing_and_memory_write(self):
        """verify STORE instruction timing and memory write"""
        instruction = {"op": "STORE", "instr_id": 4}
        operands = {"Vj": 99, "Vk": 200, "immediate": 0, "Qj": None, "Qk": None}
        rs_id, rob_index = self.tomasulo.add_rs_entry(instruction, operands)
        instruction["rob_index"] = rob_index
        
        # STORE takes 6 cycles: 2 for address calc + 4 for memory write
        for cycle in range(1, 8):
            self.exec_manager.execute_cycle(cycle)
        
        timing = self.exec_manager.get_timing_info()
        self.assertEqual(timing[4]["start_exec"], 1)
        self.assertEqual(timing[4]["finish_exec"], 7, "STORE should finish at cycle 7")
        self.assertEqual(timing[4]["write"], 7)
        
        # verify memory was written
        self.assertEqual(self.memory.read_memory(200), 99, "STORE should write 99 to address 200")
        self.assertEqual(self.memory.write_count, 1, "Memory should be written once")
        
        # STORE shouldn't forward a register value
        store_forwards = [v for v in self.tomasulo.forwarded_values if v[0] == rob_index]
        self.assertEqual(len(store_forwards), 0, "STORE should not forward register value")
        print(f"✓ STORE timing: start={timing[4]['start_exec']}, finish={timing[4]['finish_exec']}, write={timing[4]['write']}, memory[200]={self.memory.read_memory(200)}")
    
    def test_beq_branch_evaluation(self):
        """verify BEQ branch evaluation correctness"""
        # test taken branch
        instruction = {"op": "BEQ", "instr_id": 5}
        operands = {"Vj": 10, "Vk": 10, "immediate": 5, "pc": 100, "Qj": None, "Qk": None}
        rs_id, rob_index = self.tomasulo.add_rs_entry(instruction, operands)
        instruction["rob_index"] = rob_index
        
        self.exec_manager.execute_cycle(1)
        self.exec_manager.execute_cycle(2)  # write-back
        
        # verify branch notification
        self.assertEqual(len(self.tomasulo.branch_notifications), 1)
        notification = self.tomasulo.branch_notifications[0]
        self.assertTrue(notification["taken"], "BEQ with equal operands should be taken")
        self.assertEqual(notification["target"], 106, "Target should be PC+1+offset = 100+1+5 = 106")
        print(f"✓ BEQ (taken): target={notification['target']}, taken={notification['taken']}")
        
        # test not taken branch
        self.tomasulo.branch_notifications = []
        instruction2 = {"op": "BEQ", "instr_id": 6}
        operands2 = {"Vj": 10, "Vk": 20, "immediate": 5, "pc": 100, "Qj": None, "Qk": None}
        rs_id2, rob_index2 = self.tomasulo.add_rs_entry(instruction2, operands2)
        instruction2["rob_index"] = rob_index2
        
        self.exec_manager.execute_cycle(3)
        self.exec_manager.execute_cycle(4)
        
        notification2 = self.tomasulo.branch_notifications[-1]
        self.assertFalse(notification2["taken"], "BEQ with unequal operands should not be taken")
        self.assertEqual(notification2["target"], 101, "Target should be PC+1 = 100+1 = 101")
        print(f"✓ BEQ (not taken): target={notification2['target']}, taken={notification2['taken']}")
    
    def test_cdb_single_writeback_enforcement(self):
        """verify CDB enforces single write-back per cycle"""
        # add two instructions that finish at the same time
        instruction1 = {"op": "ADD", "instr_id": 7}
        operands1 = {"Vj": 1, "Vk": 1, "Qj": None, "Qk": None}
        rs_id1, rob_index1 = self.tomasulo.add_rs_entry(instruction1, operands1)
        instruction1["rob_index"] = rob_index1
        
        instruction2 = {"op": "ADD", "instr_id": 8}
        operands2 = {"Vj": 2, "Vk": 2, "Qj": None, "Qk": None}
        rs_id2, rob_index2 = self.tomasulo.add_rs_entry(instruction2, operands2)
        instruction2["rob_index"] = rob_index2
        
        # start both
        self.exec_manager.execute_cycle(1)
        
        # both should finish at cycle 3
        self.exec_manager.execute_cycle(2)
        self.exec_manager.execute_cycle(3)  # first one writes back
        
        # verify only one wrote back in cycle 3
        forwarded_count_cycle3 = len(self.tomasulo.forwarded_values)
        self.assertEqual(forwarded_count_cycle3, 1, "Only one instruction should write-back in cycle 3")
        
        # next cycle should write back the second
        self.exec_manager.execute_cycle(4)
        forwarded_count_cycle4 = len(self.tomasulo.forwarded_values)
        self.assertEqual(forwarded_count_cycle4, 2, "Second instruction should write-back in cycle 4")
        
        # verify results are correct
        self.assertEqual(self.tomasulo.rob_values[rob_index1], 2)
        self.assertEqual(self.tomasulo.rob_values[rob_index2], 4)
        print(f"✓ CDB single write-back: cycle 3 forwards={forwarded_count_cycle3}, cycle 4 forwards={forwarded_count_cycle4}")
    
    def test_operand_forwarding_correctness(self):
        """verify operand forwarding works correctly"""
        # first instruction produces a value
        instruction1 = {"op": "ADD", "instr_id": 9}
        operands1 = {"Vj": 10, "Vk": 5, "Qj": None, "Qk": None}
        rs_id1, rob_index1 = self.tomasulo.add_rs_entry(instruction1, operands1)
        instruction1["rob_index"] = rob_index1
        
        # second instruction waits for first (Qj = rob_index1)
        instruction2 = {"op": "ADD", "instr_id": 10}
        operands2 = {"Vj": None, "Vk": 3, "Qj": rob_index1, "Qk": None}
        rs_id2, rob_index2 = self.tomasulo.add_rs_entry(instruction2, operands2, ready=False)
        instruction2["rob_index"] = rob_index2
        
        # execute first instruction
        self.exec_manager.execute_cycle(1)
        self.exec_manager.execute_cycle(2)
        self.exec_manager.execute_cycle(3)  # first finishes and writes back
        
        # verify forwarding happened
        self.assertEqual(len(self.tomasulo.forwarded_values), 1)
        forwarded_rob, forwarded_value = self.tomasulo.forwarded_values[0]
        self.assertEqual(forwarded_rob, rob_index1)
        self.assertEqual(forwarded_value, 15)
        
        # verify second instruction's operand was updated
        updated_operands = self.tomasulo.rs_entries[rs_id2]["operands"]
        self.assertEqual(updated_operands["Vj"], 15, "Vj should be updated with forwarded value")
        self.assertIsNone(updated_operands["Qj"], "Qj should be cleared after forwarding")
        
        # mark as ready and execute
        self.tomasulo.rs_entries[rs_id2]["ready"] = True
        self.exec_manager.execute_cycle(4)  # should start second instruction
        
        # verify second instruction executes and produces correct result
        self.exec_manager.execute_cycle(5)
        self.exec_manager.execute_cycle(6)  # second finishes
        
        timing2 = self.exec_manager.get_timing_info()
        self.assertEqual(timing2[10]["start_exec"], 4)
        self.assertEqual(timing2[10]["finish_exec"], 6)
        self.assertEqual(self.tomasulo.rob_values[rob_index2], 18, "15 + 3 = 18")
        print(f"✓ Operand forwarding: forwarded value={forwarded_value}, final result={self.tomasulo.rob_values[rob_index2]}")
    
    def test_nand_correctness(self):
        """verify NAND instruction produces correct result"""
        instruction = {"op": "NAND", "instr_id": 11}
        operands = {"Vj": 0xFFFF, "Vk": 0xFFFF, "Qj": None, "Qk": None}
        rs_id, rob_index = self.tomasulo.add_rs_entry(instruction, operands)
        instruction["rob_index"] = rob_index
        
        # NAND takes 1 cycle
        self.exec_manager.execute_cycle(1)
        self.exec_manager.execute_cycle(2)  # write-back
        
        # NAND(0xFFFF, 0xFFFF) = ~(0xFFFF & 0xFFFF) = ~0xFFFF = 0
        result = self.tomasulo.rob_values[rob_index]
        self.assertEqual(result, 0, "NAND(0xFFFF, 0xFFFF) should equal 0")
        print(f"✓ NAND: NAND(0xFFFF, 0xFFFF) = {result}")
    
    def test_call_ret_correctness(self):
        """verify CALL and RET instructions work correctly"""
        # test CALL
        instruction = {"op": "CALL", "instr_id": 12}
        operands = {"immediate": 10, "pc": 100, "Qj": None, "Qk": None}
        rs_id, rob_index = self.tomasulo.add_rs_entry(instruction, operands)
        instruction["rob_index"] = rob_index
        
        self.exec_manager.execute_cycle(1)
        self.exec_manager.execute_cycle(2)
        
        notification = self.tomasulo.branch_notifications[0]
        self.assertTrue(notification["taken"])
        self.assertEqual(notification["target"], 111, "CALL target = PC+1+offset = 100+1+10 = 111")
        print(f"✓ CALL: target={notification['target']}")
        
        # test RET
        self.tomasulo.branch_notifications = []
        instruction2 = {"op": "RET", "instr_id": 13}
        operands2 = {"Vj": 200, "Qj": None, "Qk": None}  # R1 = 200
        rs_id2, rob_index2 = self.tomasulo.add_rs_entry(instruction2, operands2)
        instruction2["rob_index"] = rob_index2
        
        self.exec_manager.execute_cycle(3)
        self.exec_manager.execute_cycle(4)
        
        notification2 = self.tomasulo.branch_notifications[-1]
        self.assertTrue(notification2["taken"])
        self.assertEqual(notification2["target"], 200, "RET target = R1 = 200")
        print(f"✓ RET: target={notification2['target']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)


