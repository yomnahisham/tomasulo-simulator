import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from src.interfaces.instruction import Instruction
from src.interfaces.register_interface import RegisterFile
from src.interfaces.issue_unit import IssueUnit
from src.execution.timing_tracker import TimingTracker
from src.execution.reservation_station import LoadRS, StoreRS, BEQRS, CALLRS, ALURS
from src.execution.rob import ReorderBuffer

class TestIssueUnit(unittest.TestCase):
    """verify correctness of IssueUnit behavior"""

    def setUp(self):
        # create small set of instructions directly with proper parameters
        self.instructions = [
            Instruction(name="LOAD", rA=1, rB=0, immediate=0, instr_id=1),
            Instruction(name="ADD", rA=2, rB=1, rC=1, instr_id=2),
            Instruction(name="STORE", rA=2, rB=0, immediate=4, instr_id=3),
            Instruction(name="NAND", rA=3, rB=2, rC=1, instr_id=4),
        ]
        
        # create register file and timing tracker
        self.registers = RegisterFile()
        self.timing_tracker = TimingTracker()
        
        # create reservation stations, ROB, and RAT
        self.reservation_stations = {
            'LOAD1': LoadRS(),
            'LOAD2': LoadRS(),
            'STORE': StoreRS(),
            'BEQ1': BEQRS(),
            'BEQ2': BEQRS(),
            'CALL/RET': CALLRS(),
            'ADD/SUB1': ALURS(),
            'ADD/SUB2': ALURS(),
            'ADD/SUB3': ALURS(),
            'ADD/SUB4': ALURS(),
            'NAND': ALURS(),
            'MUL': ALURS()
        }
        self.rob = ReorderBuffer()
        self.rat = [None] * 8
        
        # create IssueUnit
        self.issue_unit = IssueUnit(
            self.instructions, 
            self.registers, 
            self.timing_tracker,
            self.reservation_stations,
            self.rob,
            self.rat
        )

    def test_issue_one_per_cycle(self):
        """verify only one instruction is issued per cycle"""
        cycle = 1
        issued_ids = []
        while self.issue_unit.has_instructions():
            instr = self.issue_unit.issue_next(cycle)
            self.assertIsNotNone(instr, "Instruction should be issued")
            issued_ids.append(instr.get_issue_cycle())
            cycle += 1
        
        # check that each instruction got a unique cycle
        self.assertEqual(issued_ids, [1, 2, 3, 4], "Instructions should be issued one per cycle in order")

    def test_timing_tracker_records_issue(self):
        """verify timing tracker records correct issue cycles"""
        cycle = 1
        while self.issue_unit.has_instructions():
            instr = self.issue_unit.issue_next(cycle)
            cycle += 1

        for instr in self.instructions:
            recorded = self.timing_tracker.get_timing(instr.get_instr_id())
            self.assertEqual(recorded["issue"], instr.get_issue_cycle(),
                             f"Issue cycle for {instr.get_name()} should match TimingTracker")

    def test_issued_instructions_list(self):
        """verify IssueUnit keeps track of issued instructions"""
        cycle = 1
        while self.issue_unit.has_instructions():
            self.issue_unit.issue_next(cycle)
            cycle += 1
        
        issued_instrs = self.issue_unit.get_issued_instructions()
        self.assertEqual(len(issued_instrs), len(self.instructions),
                         "All instructions should be in issued list")
        self.assertListEqual([i.get_instr_id() for i in issued_instrs],
                             [i.get_instr_id() for i in self.instructions],
                             "Issued instructions order should match input order")

if __name__ == "__main__":
    try:
        unittest.main(verbosity=2)
    except Exception as e:
        print(f"Error running issue unit test: {e}")
