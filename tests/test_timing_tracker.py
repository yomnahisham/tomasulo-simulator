"""unit tests for timing tracker"""

import unittest
from src.execution.timing_tracker import TimingTracker


class TestTimingTracker(unittest.TestCase):
    """test timing tracker"""
    
    def setUp(self):
        self.tracker = TimingTracker()
    
    def test_record_timing(self):
        """test recording timing for an instruction"""
        instr_id = 1
        
        self.tracker.record_issue(instr_id, 1)
        self.tracker.record_start_exec(instr_id, 2)
        self.tracker.record_finish_exec(instr_id, 4)
        self.tracker.record_write(instr_id, 5)
        self.tracker.record_commit(instr_id, 6)
        
        timing = self.tracker.get_timing(instr_id)
        self.assertIsNotNone(timing)
        self.assertEqual(timing["issue"], 1)
        self.assertEqual(timing["start_exec"], 2)
        self.assertEqual(timing["finish_exec"], 4)
        self.assertEqual(timing["write"], 5)
        self.assertEqual(timing["commit"], 6)
    
    def test_get_all_timing(self):
        """test getting all timing information"""
        self.tracker.record_issue(1, 1)
        self.tracker.record_issue(2, 2)
        
        all_timing = self.tracker.get_all_timing()
        self.assertEqual(len(all_timing), 2)
        self.assertIn(1, all_timing)
        self.assertIn(2, all_timing)
    
    def test_clear(self):
        """test clearing timing data"""
        self.tracker.record_issue(1, 1)
        self.tracker.clear()
        
        timing = self.tracker.get_timing(1)
        self.assertIsNone(timing)


if __name__ == "__main__":
    unittest.main()


