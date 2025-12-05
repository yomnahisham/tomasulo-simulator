"""unit tests for common data bus"""

import unittest
from src.execution.cdb import CDB


class TestCDB(unittest.TestCase):
    """test CDB implementation"""
    
    def test_single_broadcast(self):
        """test single broadcast per cycle"""
        cdb = CDB()
        
        # first broadcast should succeed
        success = cdb.broadcast(0, 42, "ADD")
        self.assertTrue(success)
        self.assertTrue(cdb.is_busy)
        
        # second broadcast should fail (CDB busy)
        success = cdb.broadcast(1, 43, "SUB")
        self.assertFalse(success)
        
        # get current broadcast
        broadcast = cdb.get_broadcast()
        self.assertIsNotNone(broadcast)
        rob_index, value, inst_type = broadcast
        self.assertEqual(rob_index, 0)
        self.assertEqual(value, 42)
        self.assertEqual(inst_type, "ADD")
    
    def test_clear_and_pending(self):
        """test clearing CDB - pending broadcasts remain in queue"""
        cdb = CDB()
        
        # first broadcast
        cdb.broadcast(0, 42, "ADD")
        
        # second broadcast (should be queued)
        cdb.broadcast(1, 43, "SUB")
        
        # clear CDB - pending broadcasts stay in queue (processed in next write-back)
        cdb.clear()
        
        # CDB should be clear, but pending broadcasts remain
        broadcast = cdb.get_broadcast()
        self.assertIsNone(broadcast)  # CDB is clear
        self.assertFalse(cdb.is_busy)
        
        # check that pending broadcasts are still queued
        state = cdb.get_state()
        self.assertEqual(state["pending_count"], 1)
        
        # manually process pending (simulating next write-back stage)
        if cdb.pending_broadcasts:
            rob_index, value, inst_type = cdb.pending_broadcasts[0]
            cdb.broadcast(rob_index, value, inst_type)
            broadcast = cdb.get_broadcast()
            self.assertIsNotNone(broadcast)
            self.assertEqual(broadcast[0], 1)
            self.assertEqual(broadcast[1], 43)
    
    def test_get_state(self):
        """test getting CDB state for GUI"""
        cdb = CDB()
        
        # empty state
        state = cdb.get_state()
        self.assertFalse(state["busy"])
        self.assertIsNone(state["rob_index"])
        
        # busy state
        cdb.broadcast(5, 100, "MUL")
        state = cdb.get_state()
        self.assertTrue(state["busy"])
        self.assertEqual(state["rob_index"], 5)
        self.assertEqual(state["value"], 100)
        self.assertEqual(state["instruction_type"], "MUL")


if __name__ == "__main__":
    unittest.main()

