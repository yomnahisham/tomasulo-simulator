# Example Assembly Program for Tomasulo Simulator
# This program demonstrates various instruction types and data dependencies

# Load value from memory
LOAD R1, 0(R0)      # R1 = memory[0]

# Arithmetic operations with dependencies
ADD R2, R1, R1      # R2 = R1 + R1 (depends on R1)
MUL R3, R2, R1      # R3 = R2 * R1 (depends on R2 and R1)

# More operations
ADD R4, R2, R3      # R4 = R2 + R3 (depends on R2 and R3)
NAND R5, R4, R1    # R5 = NAND(R4, R1) (depends on R4 and R1)

# Store result back to memory
STORE R4, 4(R0)    # memory[4] = R4

# Conditional branch
BEQ R1, R2, LABEL1 # Branch if R1 == R2

# Function call
CALL FUNCTION       # Call a function

# Return from function
RET                 # Return from function

LABEL1:
# Target of branch (if taken)
ADD R6, R1, R2      # R6 = R1 + R2


