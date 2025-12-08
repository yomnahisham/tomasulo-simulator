import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.interfaces.parser import Parser
from src.interfaces.instruction import Instruction

class TestParser(unittest.TestCase):
    """Verify Parser correctly converts assembly into Instruction objects."""

    def setUp(self):
        # path to the test assembly file
        self.asm_file = os.path.join(os.path.dirname(__file__), "../testcases/test1.s")
        self.parser = Parser()
    
    def test_parse_returns_list_of_instructions(self):
        instructions = self.parser.parse(self.asm_file)
        self.assertIsInstance(instructions, list, "Parser should return a list")
        self.assertTrue(all(isinstance(instr, Instruction) for instr in instructions),
                        "All elements should be Instruction objects")
    
    def test_instruction_fields(self):
        instructions = self.parser.parse(self.asm_file)

        # Check first instruction (LOAD R1, 0(R0))
        load_instr = instructions[0]
        self.assertEqual(load_instr.get_name(), "LOAD")
        self.assertEqual(load_instr.get_rA(), 1)
        self.assertEqual(load_instr.get_rB(), 0)
        self.assertEqual(load_instr.get_immediate(), 0)
        self.assertEqual(load_instr.get_instr_id(), 1)

        # Check second instruction (ADD R2, R1, R1)
        add_instr = instructions[1]
        self.assertEqual(add_instr.get_name(), "ADD")
        self.assertEqual(add_instr.get_rA(), 2)
        self.assertEqual(add_instr.get_rB(), 1)
        self.assertEqual(add_instr.get_rC(), 1)
        self.assertEqual(add_instr.get_instr_id(), 2)

        # Check a branch instruction (BEQ R1, R2, LABEL1)
        beq_instr = instructions[4]
        self.assertEqual(beq_instr.get_name(), "BEQ")
        self.assertEqual(beq_instr.get_rA(), 1)
        self.assertEqual(beq_instr.get_rB(), 2)
        self.assertEqual(beq_instr.get_label(), "LABEL1")
        self.assertEqual(beq_instr.get_instr_id(), 5)

        # Check CALL
        call_instr = instructions[5]
        self.assertEqual(call_instr.get_name(), "CALL")
        self.assertEqual(call_instr.get_label(), "FUNC")
        self.assertEqual(call_instr.get_instr_id(), 6)

        # Check RET
        ret_instr = instructions[6]
        self.assertEqual(ret_instr.get_name(), "RET")
        self.assertEqual(ret_instr.get_instr_id(), 7)

if __name__ == "__main__":
    unittest.main(verbosity=2)
