"""Reservation station tests"""
from src.execution.reservation_station import ReservationStation, LoadRS, StoreRS, ALURS, CALLRS, BEQRS
import unittest

class TestReservationStation(unittest.TestCase):
    """Test Reservation Station functionality"""

    def test_load_rs(self):
        """Test Load Reservation Station"""
        load_rs = LoadRS()
        load_rs.push(instruction="LOAD R1, 0(R2)", A=100, Vj=5)
        self.assertTrue(load_rs.is_ready())
        self.assertTrue(load_rs.is_busy())
        self.assertEqual(load_rs.A, 100)
        self.assertEqual(load_rs.Vj, 5)
        load_rs.pop()
        self.assertFalse(load_rs.is_busy())

    def test_store_rs(self):
        """Test Store Reservation Station"""
        store_rs = StoreRS()
        store_rs.push(instruction="STORE R1, 0(R2)", A=200, Vj=10, Qk=42)
        self.assertFalse(store_rs.is_ready())
        self.assertTrue(store_rs.is_busy())
        self.assertEqual(store_rs.A, 200)
        self.assertEqual(store_rs.Vj, 10)
        self.assertEqual(store_rs.Qk, 42)
        store_rs.pop()
        self.assertFalse(store_rs.is_busy())

    def test_alurs(self):
        """Test ALU Reservation Station"""
        alu_rs = ALURS()
        alu_rs.push(instruction="ADD R1, R2, R3", Op="ADD", Qj=5, Qk=3)
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
        call_rs = CALLRS()
        call_rs.push(instruction="CALL func", Op="CALL", PC=400, A=20)
        self.assertTrue(call_rs.is_busy())
        self.assertEqual(call_rs.PC, 400)
        self.assertEqual(call_rs.A, 20)
        call_rs.pop()
        self.assertFalse(call_rs.is_busy())