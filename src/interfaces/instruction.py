"""
Docstring for interfaces.instruction
"""

class Instruction:
    def __init__(self, name, rA = None, rB = None, rC = None, immediate = None, label = None):
        """
        Represents a single instruction.
        """
        self._name = name
        self._rA = rA
        self._rB = rB
        self._rC = rC
        self._immediate = immediate
        self._label = label
        self._issue_cycle = None

    def get_name(self):
        return self._name

    def get_rA(self):
        return self._rA

    def get_rB(self):
        return self._rB

    def get_rC(self):
        return self._rC

    def get_immediate(self):
        return self._immediate

    def get_label(self):
        return self._label

    def get_issue_cycle(self):
        return self._issue_cycle

    def set_issue_cycle(self, cycle):
        self._issue_cycle = cycle