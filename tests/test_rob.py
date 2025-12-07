"""ROB tests"""
from src.execution.rob import ReorderBuffer
import unittest

class TestReorderBuffer(unittest.TestCase):
    """Test Reorder Buffer functionality"""

    def test_push_and_pop(self):
        """Test pushing and popping ROB entries"""
        rob = ReorderBuffer(size=4)
        rob.push(type='ALU', dest=1)
        rob.push(type='LOAD', dest=2)
        self.assertFalse(rob.is_full())
        rob.push(type='STORE', dest=3)
        rob.push(type='BEQ', dest=4)
        self.assertTrue(rob.is_full())
        
        entry = rob.pop()
        self.assertEqual(entry.type, 'ALU')
        self.assertEqual(entry.dest, 1)
        self.assertFalse(rob.is_full())
        rob.push(type='CALL', dest=5)
        entry = rob.pop()
        self.assertEqual(entry.type, 'LOAD')

    def test_update_entry(self):
        """Test updating ROB entry"""
        rob = ReorderBuffer(size=2)
        rob.push(type='ALU', dest=1)
        rob.push(type='LOAD', dest=2)
        
        rob.update(0, value=42)
        entry = rob.buffer.at(0)
        self.assertTrue(entry.ready)
        self.assertEqual(entry.value, 42)
        
        rob.update(1, value=84)
        entry = rob.buffer.at(1)
        self.assertTrue(entry.ready)
        self.assertEqual(entry.value, 84)