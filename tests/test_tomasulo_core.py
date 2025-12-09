"""Tomasulo core tests"""
from src.execution.tomasulo_core import TomasuloCore
from src.interfaces.instruction import Instruction
import unittest

class TestTomasuloCore(unittest.TestCase):
    """Test Tomasulo Core functionality"""

    def test_get_ready_rs_entries(self):
        """Test getting ready RS entries"""
        core = TomasuloCore()
        # Add test RS entries
        rs1 = core.reservation_stations['ADD/SUB1']
        instr1 = Instruction(name="ADD", rA=1, rB=2, rC=3)
        rs1.push(instruction=instr1, Op="ADD", dest=0, Vj=5, Vk=10)
        rs2 = core.reservation_stations['ADD/SUB2']
        instr2 = Instruction(name="SUB", rA=4, rB=5, rC=6)
        rs2.push(instruction=instr2, Op="SUB", dest=1, Qj=2, Vk=15)
        ready_rs = core.get_ready_rs_entries()
        self.assertEqual(len(ready_rs), 1)
        self.assertEqual(ready_rs[0]['id'], 'ADD/SUB1')
        self.assertIn('instruction', ready_rs[0])
        self.assertEqual(ready_rs[0]['instruction'].get_name(), "ADD")
        self.assertEqual(ready_rs[0]['Vj'], 5)
        self.assertEqual(ready_rs[0]['Vk'], 10)
        self.assertEqual(ready_rs[0]['Qj'], None)
        self.assertEqual(ready_rs[0]['Qk'], None)

    def test_get_rs_operands(self):
        """Test getting RS operands"""
        core = TomasuloCore()
        rs = core.reservation_stations['MUL']
        instr = Instruction(name="MUL", rA=1, rB=2, rC=3)
        rs.push(instruction=instr, Op="MUL", dest=0, Vj=7, Qk=3)
        operands = core.get_rs_operands(rs)
        self.assertEqual(operands['Vj'], 7)
        self.assertNotIn('Vk', operands)
        self.assertNotIn('Qj', operands)
        self.assertEqual(operands['Qk'], 3)

    def test_update_rob_value(self):
        """Test updating ROB value"""
        core = TomasuloCore()
        core.rob.push(type="ALU", dest=1)
        core.rob.update(0, value=55)
        entry = core.rob.buffer.at(0)
        self.assertTrue(entry.ready)
        self.assertEqual(entry.value, 55)

    def test_forward_to_rs(self):
        """Test forwarding to RS entries"""
        core = TomasuloCore()

        core.rob.push(type="ALU", dest=0)
        core.rob.push(type="ALU", dest=1)
        core.rob.push(type="LOAD", dest=2)
        core.rob.push(type="STORE", dest=3)
        core.rob.push(type="BRANCH", dest=4)
        
        rs = core.reservation_stations['NAND']
        instr = Instruction(name="NAND", rA=1, rB=2, rC=3)
        rs.push(instruction=instr, Op="NAND", dest=5, Qj=0, Qk=1)
        core.forward_to_rs(0, 20)
        self.assertEqual(rs.Vj, 20)
        self.assertEqual(rs.Qj, None)
        self.assertIsNone(rs.Vk)
        self.assertEqual(rs.Qk, 1)
        core.forward_to_rs(1, 30)
        self.assertEqual(rs.Vk, 30)
        self.assertEqual(rs.Qk, None)

        rs_load = core.reservation_stations['LOAD1']
        instr_load = Instruction(name="LOAD", rA=4, rB=5, immediate=0)
        rs_load.push(instruction=instr_load, A=0, dest=2, Qj=2)
        core.forward_to_rs(2, 100)
        self.assertEqual(rs_load.Vj, 100)
        self.assertEqual(rs_load.Qj, None)

        rs_store = core.reservation_stations['STORE']
        instr_store = Instruction(name="STORE", rA=6, rB=7, immediate=0)
        rs_store.push(instruction=instr_store, A=0, dest=3, Qj=3, Qk=3)
        core.forward_to_rs(3, 200)
        self.assertEqual(rs_store.Vj, 200)
        self.assertEqual(rs_store.Qj, None)
        self.assertEqual(rs_store.Vk, 200)
        self.assertEqual(rs_store.Qk, None)

    def test_mark_rs_executing(self):
        """Test marking RS as executing"""
        core = TomasuloCore()
        rs = core.reservation_stations['ADD/SUB1']
        instr = Instruction(name="ADD", rA=1, rB=2, rC=3)
        rs.push(instruction=instr, Op="ADD", dest=0, Vj=5, Vk=10)
        core.mark_rs_executing('ADD/SUB1')
        self.assertEqual(rs.state, "EXECUTING")

    def test_get_oldest_ready_rob_index(self):
        """Test getting oldest ready ROB index"""
        core = TomasuloCore()
        core.rob.push(type="ALU", dest=1)
        core.rob.push(type="LOAD", dest=2)
        core.rob.update(0, value=42)
        core.rob.update(1, value=84)
        oldest_index = core.get_oldest_ready_rob_index()
        self.assertEqual(oldest_index, 0)
    def test_flush_with_multiple_instructions(self):
        """Test flushing ROB with multiple instruction types"""
        from src.interfaces.instruction import Instruction
        core = TomasuloCore()

        # Initialize register file
        core.reg_file.write(0, 0)  # R0 is always 0
        core.reg_file.write(1, 10)
        core.reg_file.write(2, 20)
        core.reg_file.write(3, 30)
        core.reg_file.write(4, 40)
        core.reg_file.write(5, 50)
        core.reg_file.write(6, 60)
        core.reg_file.write(7, 70)

        # Create instructions
        instruction2 = Instruction(name="ADD", rA=1, rB=2, rC=3, instr_id=1)
        instruction3 = Instruction(name="STORE", rA=4, rB=5, immediate=200, instr_id=2)
        instruction4 = Instruction(name="BEQ", rA=6, rB=7, label="LABEL", instr_id=3)
        instruction5 = Instruction(name="CALL", rA=1, immediate=300, instr_id=4)
        instruction6 = Instruction(name="MUL", rA=2, rB=3, rC=4, instr_id=5)
        instruction7 = Instruction(name="NAND", rA=5, rB=6, rC=7, instr_id=6)
        
        # Issue all instructions
        core.issue(instruction2)
        core.issue(instruction3)
        core.issue(instruction4)
        core.issue(instruction5)
        core.issue(instruction6)
        core.issue(instruction7)
        
        # Get initial ROB state
        initial_head = core.rob.buffer.head
        initial_tail = core.rob.buffer.tail
        initial_count = (initial_tail - initial_head) % core.rob.max_size
        
        # Verify 6 instructions were issued
        self.assertEqual(initial_count, 6)
        
        # Flush from index 2 onwards
        core.flush(2)
        
        # Get ROB state after flush
        after_head = core.rob.buffer.head
        after_tail = core.rob.buffer.tail
        after_count = (after_tail - after_head) % core.rob.max_size
        
        # Verify entries from index 2 onwards were flushed (3 entries remain)
        self.assertEqual(after_count, 3, "ROB should have 3 entries after flush")
        self.assertLess(after_count, initial_count, "ROB count should decrease after flush")
        
        # Verify first three entries still exist
        entry0 = core.rob.buffer.at(0)
        entry1 = core.rob.buffer.at(1)
        entry2 = core.rob.buffer.at(2)
        
        self.assertIsNotNone(entry0, "Entry 0 should still exist")
        self.assertIsNotNone(entry1, "Entry 1 should still exist")
        self.assertIsNotNone(entry2, "Entry 2 should still exist")
        self.assertEqual(entry0.name, "ADD")
        self.assertEqual(entry1.name, "STORE")
        self.assertEqual(entry2.name, "BEQ")
