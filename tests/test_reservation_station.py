"""Reservation station tests"""
from src.execution.reservation_station import ReservationStation, LoadRS, StoreRS, ALURS, CALLRS, BEQRS
import unittest

class TestReservationStation(unittest.TestCase):
    """Test Reservation Station functionality"""

    def test_load_rs(self):
        """Test Load Reservation Station"""
        from src.interfaces.instruction import Instruction
        load_rs = LoadRS()
        instr = Instruction(name="LOAD", rA=1, rB=2, immediate=0)
        load_rs.push(instruction=instr, A=100, dest=0, Vj=5)
        self.assertTrue(load_rs.is_ready())
        self.assertTrue(load_rs.is_busy())
        self.assertEqual(load_rs.A, 100)
        self.assertEqual(load_rs.Vj, 5)
        load_rs.pop()
        self.assertFalse(load_rs.is_busy())

    def test_store_rs(self):
        """Test Store Reservation Station"""
        from src.interfaces.instruction import Instruction
        store_rs = StoreRS()
        instr = Instruction(name="STORE", rA=1, rB=2, immediate=0)
        store_rs.push(instruction=instr, A=200, dest=0, Vj=10, Qk=42)
        self.assertFalse(store_rs.is_ready())
        self.assertTrue(store_rs.is_busy())
        self.assertEqual(store_rs.A, 200)
        self.assertEqual(store_rs.Vj, 10)
        self.assertEqual(store_rs.Qk, 42)
        store_rs.pop()
        self.assertFalse(store_rs.is_busy())

    def test_alurs(self):
        """Test ALU Reservation Station"""
        from src.interfaces.instruction import Instruction
        alu_rs = ALURS()
        instr = Instruction(name="ADD", rA=1, rB=2, rC=3)
        alu_rs.push(instruction=instr, Op="ADD", dest=0, Qj=5, Qk=3)
        self.assertTrue(alu_rs.is_busy())
        self.assertEqual(alu_rs.Vj, None)
        self.assertEqual(alu_rs.Vk, None)
        self.assertEqual(alu_rs.Qj, 5)
        self.assertEqual(alu_rs.Qk, 3)
        self.assertFalse(alu_rs.is_ready())
        alu_rs.pop()
        self.assertFalse(alu_rs.is_busy())

    def test_callrs(self):
        """Test Call/Return Reservation Station"""
        from src.interfaces.instruction import Instruction
        call_rs = CALLRS()
        instr = Instruction(name="CALL", label="func", immediate=20)
        call_rs.push(instruction=instr, Op="CALL", dest=0, A=20)
        self.assertTrue(call_rs.is_busy())
        self.assertEqual(call_rs.A, 20)
        call_rs.pop()
        self.assertFalse(call_rs.is_busy())