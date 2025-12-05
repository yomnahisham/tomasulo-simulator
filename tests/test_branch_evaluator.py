"""unit tests for branch evaluator"""

import unittest
from src.execution.branch_evaluator import BranchEvaluator


class TestBranchEvaluator(unittest.TestCase):
    """test branch evaluator"""
    
    def setUp(self):
        self.evaluator = BranchEvaluator()
    
    def test_beq_taken(self):
        """test BEQ when condition is met (taken)"""
        result = self.evaluator.evaluate_beq(10, 10, 5, 100)
        
        self.assertTrue(result["taken"])
        self.assertTrue(result["condition_met"])
        self.assertEqual(result["target"], 106)  # PC + 1 + offset
    
    def test_beq_not_taken(self):
        """test BEQ when condition is not met (not taken)"""
        result = self.evaluator.evaluate_beq(10, 20, 5, 100)
        
        self.assertFalse(result["taken"])
        self.assertFalse(result["condition_met"])
        self.assertEqual(result["target"], 101)  # PC + 1
    
    def test_call(self):
        """test CALL instruction evaluation"""
        result = self.evaluator.evaluate_call(10, 100)
        
        self.assertEqual(result["target"], 111)  # PC + 1 + label_offset
        self.assertEqual(result["return_address"], 101)  # PC + 1
    
    def test_ret(self):
        """test RET instruction evaluation"""
        result = self.evaluator.evaluate_ret(200)
        
        self.assertEqual(result["target"], 200)  # value from R1


if __name__ == "__main__":
    unittest.main()

