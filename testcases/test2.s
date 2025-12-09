# Test Case: Branch Taken with Speculative Instruction Flushing
# This tests ROB flushing when branch prediction is wrong

# Initialize registers
LOAD R1, 0(R0)      # R1 = memory[0] = 5
LOAD R2, 4(R0)      # R2 = memory[4] = 5

# Branch that will be taken (R1 == R2)
BEQ R1, R2, TARGET  # Predict NOT taken, but actually TAKEN

# Speculative instructions (should be FLUSHED)
ADD R3, R1, R2      # R3 = R1 + R2 (SHOULD BE FLUSHED)
MUL R4, R3, R1      # R4 = R3 * R1 (SHOULD BE FLUSHED)
SUB R5, R4, R2      # R5 = R4 - R2 (SHOULD BE FLUSHED)
STORE R5, 8(R0)     # memory[8] = R5 (SHOULD BE FLUSHED)

TARGET:
# Correct path after branch taken
ADD R6, R1, R2      # R6 = R1 + R2 = 10 (SHOULD EXECUTE)
MUL R7, R6, R1      # R7 = R6 * R1 = 50 (SHOULD EXECUTE)
STORE R7, 12(R0)    # memory[12] = R7 (SHOULD EXECUTE)
