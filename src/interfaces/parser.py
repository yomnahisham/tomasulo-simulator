from .instruction import Instruction

class Parser:
    """
    Parser that reads an assembly file and converts it to Instruction objects.
    """
    def __init__(self):
        self._filepath = None
        self._instructions = []
        self._label_map = {}  # Maps label name to instruction index

    def parse(self, filepath):
        """
        Parse an assembly file into a list of Instruction objects.

        Args:
            filepath (str): path to the assembly file to parse.

        Returns:
            list[Instruction]: parsed instructions

        Raises:
            ValueError: if an invalid instruction name is found, with line number in message.
        """

        self._filepath = filepath
        instr_id_counter = 1 

        with open(self._filepath, 'r') as file:
            lines = file.readlines()

        for line_num, line in enumerate(lines, start=1):
            original_line = line
            line = line.strip()

            if not line or line.startswith("#"): # skip empty or comment lines
                continue
            
            # Handle label definitions (lines ending with ':')
            if line.endswith(':'):
                label_name = line[:-1].strip()  # Remove the ':'
                # Map this label to the next instruction index (the instruction after this label)
                self._label_map[label_name] = len(self._instructions)
                continue

            try:
                instruction = self._parse_line(line, line_num)
            except ValueError as e:
                # Re-raise with line number information
                raise ValueError(f"Line {line_num}: {str(e)}")
            except Exception as e:
                raise ValueError(f"Line {line_num}: Error parsing instruction: {str(e)}")

            instruction.set_instr_id(instr_id_counter)
            instr_id_counter += 1

            self._instructions.append(instruction)

        print("\nParsed Instructions:")
        for instr in self._instructions:
            print(
                f"ID = {instr.get_instr_id()} | Name = {instr.get_name()} | "
                f"rA = {instr.get_rA()} | rB = {instr.get_rB()} | rC = {instr.get_rC()} | "
                f"imm = {instr.get_immediate()} | label = {instr.get_label()} | "
            )
        print(f"\nLabel Map: {self._label_map}")
        return self._instructions
    
    def get_label_map(self):
        """Get the label to instruction index mapping."""
        return self._label_map.copy()

    def _parse_line(self, line, line_num=None):
        """
        Convert a single line of assembly into an Instruction object.

        Args:
            line (str): a single line of assembly code.
            line_num (int): line number for error reporting.

        Returns:
            Instruction: the corresponding Instruction object.

        Raises:
            ValueError: if the instruction is unknown or malformed.
        """

        # example lets say we have ADD R1, R2, R3
        parts = line.replace(',', '').split() # remove commas and split line into parts 
        # --> so we have [ADD, R1, R2, R3]

        if len(parts) == 0:
            raise ValueError("Empty instruction line")

        name = parts[0].upper() # to handle case sensitivity

        try:
            if name in ["ADD", "SUB", "NAND", "MUL"]:
                if len(parts) < 4:
                    raise ValueError(f"{name} requires 3 operands (rA, rB, rC)")
                rA = int(parts[1][1]) # parts[1] -> R1 ... parts[1][1] -> 1
                rB = int(parts[2][1])
                rC = int(parts[3][1])

                return Instruction(name, rA, rB, rC)
            
            elif name == "LOAD":
                if len(parts) < 3:
                    raise ValueError("LOAD requires 2 operands (rA, offset(rB))")
                rA = int(parts[1][1])
                if '(' not in parts[2]:
                    raise ValueError("LOAD offset must be in format: offset(rB)")
                offset, rB = parts[2].split('(')
                offset = int(offset)
                rB = int(rB[1])

                return Instruction(name, rA, rB, immediate = offset)
            
            elif name == "STORE":
                if len(parts) < 3:
                    raise ValueError("STORE requires 2 operands (rA, offset(rB))")
                rA = int(parts[1][1])
                if '(' not in parts[2]:
                    raise ValueError("STORE offset must be in format: offset(rB)")
                offset, rB = parts[2].split('(')
                offset = int(offset)
                rB = int(rB[1])

                return Instruction(name, rA, rB, immediate = offset)
            
            elif name == "BEQ":
                if len(parts) < 4:
                    raise ValueError("BEQ requires 3 operands (rA, rB, label)")
                rA = int(parts[1][1])
                rB = int(parts[2][1])
                label = parts[3]

                return Instruction(name, rA, rB, label = label)
            
            elif name == "CALL":
                if len(parts) < 2:
                    raise ValueError("CALL requires 1 operand (label)")
                label = parts[1]

                return Instruction(name, label = label)
            
            elif name == "RET":
                return Instruction(name)
            
            else:
                raise ValueError(f"Invalid instruction: {name}")
        except (ValueError, IndexError) as e:
            if isinstance(e, ValueError) and "Invalid instruction" not in str(e):
                raise  # Re-raise our custom ValueError messages
            raise ValueError(f"Malformed {name} instruction: {str(e)}")
        
    
