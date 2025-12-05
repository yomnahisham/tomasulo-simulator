"""unit tests for functional units"""

import unittest
from src.execution.functional_units import (
    AddSubFU,
    NandFU,
    MulFU,
    BeqFU,
    CallRetFU,
    FUPool,
)


class MockMemoryInterface:
    """mock memory interface for testing"""
    
    def read_memory(self, address: int) -> int:
        return 42
    
    def write_memory(self, address: int, value: int) -> None:
        pass


class TestFunctionalUnits(unittest.TestCase):
    """test functional unit implementations"""
    
    def test_add_fu(self):
        """test ADD functional unit"""
        fu = AddSubFU()
        instruction = {"op": "ADD", "instr_id": 1}
        operands = {"Vj": 10, "Vk": 5}
        
        fu.start_execution(instruction, 0, operands)
        self.assertTrue(fu.is_busy())
        self.assertEqual(fu.cycles_remaining, 2)
        
        # first cycle
        finished = fu.tick()
        self.assertFalse(finished)
        self.assertEqual(fu.cycles_remaining, 1)
        
        # second cycle - should finish
        finished = fu.tick()
        self.assertTrue(finished)
        self.assertEqual(fu.get_result(), 15)
        self.assertEqual(fu.state.value, "finished")
    
    def test_sub_fu(self):
        """test SUB functional unit"""
        fu = AddSubFU()
        instruction = {"op": "SUB", "instr_id": 1}
        operands = {"Vj": 10, "Vk": 3}
        
        fu.start_execution(instruction, 0, operands)
        fu.tick()
        finished = fu.tick()
        
        self.assertTrue(finished)
        self.assertEqual(fu.get_result(), 7)
    
    def test_nand_fu(self):
        """test NAND functional unit (1 cycle)"""
        fu = NandFU()
        instruction = {"op": "NAND", "instr_id": 1}
        operands = {"Vj": 0xFFFF, "Vk": 0xFFFF}
        
        fu.start_execution(instruction, 0, operands)
        finished = fu.tick()
        
        self.assertTrue(finished)
        self.assertEqual(fu.get_result(), 0)
    
    def test_mul_fu(self):
        """test MUL functional unit (12 cycles)"""
        fu = MulFU()
        instruction = {"op": "MUL", "instr_id": 1}
        operands = {"Vj": 5, "Vk": 4}
        
        fu.start_execution(instruction, 0, operands)
        self.assertEqual(fu.cycles_remaining, 12)
        
        # tick 12 times
        for _ in range(11):
            finished = fu.tick()
            self.assertFalse(finished)
        
        finished = fu.tick()
        self.assertTrue(finished)
        self.assertEqual(fu.get_result(), 20)
    
    def test_beq_fu(self):
        """test BEQ functional unit"""
        fu = BeqFU()
        instruction = {"op": "BEQ", "instr_id": 1}
        operands = {"Vj": 10, "Vk": 10, "immediate": 5, "pc": 100}
        
        fu.start_execution(instruction, 0, operands)
        finished = fu.tick()
        
        self.assertTrue(finished)
        result = fu.get_result()
        self.assertTrue(result["taken"])
        self.assertEqual(result["target"], 106)  # PC + 1 + offset
    
    def test_fu_pool_availability(self):
        """test FU pool availability checking"""
        memory = MockMemoryInterface()
        pool = FUPool(memory)
        
        # check availability
        self.assertTrue(pool.is_available("ADD"))
        self.assertTrue(pool.is_available("MUL"))
        
        # get and use all ADD/SUB units, marking each as busy immediately
        fu1 = pool.get_available_fu("ADD")
        self.assertIsNotNone(fu1)
        fu1.start_execution({"op": "ADD"}, 0, {"Vj": 1, "Vk": 1})
        
        # should still have 3 more ADD/SUB units
        self.assertTrue(pool.is_available("ADD"))
        
        # get and mark remaining ADD/SUB units as busy
        fu2 = pool.get_available_fu("ADD")
        self.assertIsNotNone(fu2)
        fu2.start_execution({"op": "ADD"}, 1, {"Vj": 1, "Vk": 1})
        
        fu3 = pool.get_available_fu("ADD")
        self.assertIsNotNone(fu3)
        fu3.start_execution({"op": "ADD"}, 2, {"Vj": 1, "Vk": 1})
        
        fu4 = pool.get_available_fu("ADD")
        self.assertIsNotNone(fu4)
        fu4.start_execution({"op": "ADD"}, 3, {"Vj": 1, "Vk": 1})
        
        # now should be unavailable
        self.assertFalse(pool.is_available("ADD"))
        self.assertIsNone(pool.get_available_fu("ADD"))


if __name__ == "__main__":
    unittest.main()

