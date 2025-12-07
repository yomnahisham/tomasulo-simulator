from instruction import Instruction

class Parser:
    """
    Parser that reads an assembly file and converts it to Instruction objects.
    """
    def __init__(self):
        self._filepath = None
        self._instructions = []

    def parse(self, filepath):
        """
        Parse an assembly file into a list of Instruction objects.

        Args:
            filepath (str): path to the assembly file to parse.

        Returns:
            list[Instruction]: parsed instructions

        Raises:
            ValueError: if an invalid instruction name is found.
        """

        self._filepath = filepath

        with open(self._filepath, 'r') as file:
            lines = file.readlines()

        for line in lines:
            line = line.strip()

            if not line or line.startswith("#"): # skip empty or comment lines
                continue

            instruction = self._parse_line(line)
            self._instructions.append(instruction)

        return self._instructions

    def _parse_line(self, line):
        """
        Convert a single line of assembly into an Instruction object.

        Args:
            line (str): a single line of assembly code.

        Returns:
            Instruction: the corresponding Instruction object.

        Raises:
            ValueError: if the instruction is unknown.
        """

        # example lets say we have ADD R1, R2, R3
        parts = line.replace(',', '').split() # remove commas and split line into parts 
        # --> so we have [ADD, R1, R2, R3]

        name = parts[0].upper() # to handle case sensitivity

        if name in ["ADD", "SUB", "NAND", "MUL"]:
            rA = int(parts[1][1]) # parts[1] -> R1 ... parts[1][1] -> 1
            rB = int(parts[2][1])
            rC = int(parts[3][1])

            return Instruction(name, rA, rB, rC)
        
        elif name == "LOAD":
            rA = int(parts[1][1])
            offset, rB = parts[2].split('(')
            offset = int(offset)
            rB = int(rB[1])

            return Instruction(name, rA, rB, immediate = offset)
        
        elif name == "STORE":
            rA = int(parts[1][1])
            offset, rB = parts[2].split('(')
            offset = int(offset)
            rB = int(rB[1])

            return Instruction(name, rA, rB, immediate = offset)
        
        elif name == "BEQ":
            rA = int(parts[1][1])
            rB = int(parts[2][1])
            label = parts[3]

            return Instruction(name, rA, rB, label = label)
        
        elif name == "CALL":
            label = parts[1]

            return Instruction(name, label = label)
        
        elif name == "RET":
            return Instruction(name)
        
        else:
            raise ValueError(f"Invalid instruction: {name}")
        
    
