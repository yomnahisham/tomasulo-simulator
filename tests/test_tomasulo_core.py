"""Tomasulo core tests"""
from src.execution.tomasulo_core import ExecutionCore
import unittest

class TestTomasuloCore(unittest.TestCase):
    """Test Tomasulo Core functionality"""

    def test_get_ready_rs_entries(self):
        """Test getting ready RS entries"""
        core = ExecutionCore()
        # Add test RS entries
        rs1 = core.reservation_stations['ADD/SUB1']
        rs1.push(instruction="ADD R1, R2, R3", Op="ADD", Vj=5, Vk=10)
        rs2 = core.reservation_stations['ADD/SUB2']
        rs2.push(instruction="SUB R4, R5, R6", Op="SUB", Qj=2, Vk=15)
        ready_rs = core.get_ready_rs_entries()
        self.assertEqual(len(ready_rs), 1)
        self.assertEqual(ready_rs[0]['id'], 'ADD/SUB1')
        self.assertIn('instruction', ready_rs[0])
        self.assertEqual(ready_rs[0]['instruction'], "ADD R1, R2, R3")
        self.assertEqual(ready_rs[0]['Vj'], 5)
        self.assertEqual(ready_rs[0]['Vk'], 10)
        self.assertEqual(ready_rs[0]['Qj'], None)
        self.assertEqual(ready_rs[0]['Qk'], None)

    def test_get_rs_operands(self):
        """Test getting RS operands"""
        core = ExecutionCore()
        rs = core.reservation_stations['MUL']
        rs.push(instruction="MUL R1, R2, R3", Op="MUL", Vj=7, Qk=3)
        operands = core.get_rs_operands(rs)
        self.assertEqual(operands['Vj'], 7)
        self.assertNotIn('Vk', operands)
        self.assertNotIn('Qj', operands)
        self.assertEqual(operands['Qk'], 3)

    def test_update_rob_value(self):
        """Test updating ROB value"""
        core = ExecutionCore()
        core.rob.push(type="ALU", dest=1)
        core.rob.update(0, value=55)
        entry = core.rob.buffer.at(0)
        self.assertTrue(entry.ready)
        self.assertEqual(entry.value, 55)

    def test_forward_to_rs(self):
        """Test forwarding to RS entries"""
        core = ExecutionCore()

        core.rob.push(type="ALU", dest=0)
        core.rob.push(type="ALU", dest=1)
        core.rob.push(type="LOAD", dest=2)
        core.rob.push(type="STORE", dest=3)
        core.rob.push(type="BRANCH", dest=4)
        
        rs = core.reservation_stations['NAND']
        rs.push(instruction="NAND R1, R2, R3", Op="NAND", Qj=0, Qk=1)
        core.forward_to_rs(0, 20)
        self.assertEqual(rs.Vj, 20)
        self.assertEqual(rs.Qj, None)
        self.assertIsNone(rs.Vk)
        self.assertEqual(rs.Qk, 1)
        core.forward_to_rs(1, 30)
        self.assertEqual(rs.Vk, 30)
        self.assertEqual(rs.Qk, None)

        rs_load = core.reservation_stations['LOAD1']
        rs_load.push(instruction="LOAD R4, 0(R5)", A=0, Qj=2)
        core.forward_to_rs(2, 100)
        self.assertEqual(rs_load.Vj, 100)
        self.assertEqual(rs_load.Qj, None)

        rs_store = core.reservation_stations['STORE']
        rs_store.push(instruction="STORE R6, 0(R7)", A=0, Qj=3, Qk=3)
        core.forward_to_rs(3, 200)
        self.assertEqual(rs_store.Vj, 200)
        self.assertEqual(rs_store.Qj, None)
        self.assertEqual(rs_store.Vk, 200)
        self.assertEqual(rs_store.Qk, None)

    def test_mark_rs_executing(self):
        """Test marking RS as executing"""
        core = ExecutionCore()
        rs = core.reservation_stations['ADD/SUB1']
        rs.push(instruction="ADD R1, R2, R3", Op="ADD", Vj=5, Vk=10)
        core.mark_rs_executing('ADD/SUB1')
        self.assertEqual(rs.state, "EXECUTING")

    def test_get_oldest_ready_rob_index(self):
        """Test getting oldest ready ROB index"""
        core = ExecutionCore()
        core.rob.push(type="ALU", dest=1)
        core.rob.push(type="LOAD", dest=2)
        core.rob.update(0, value=42)
        core.rob.update(1, value=84)
        oldest_index = core.get_oldest_ready_rob_index()
        self.assertEqual(oldest_index, 0)