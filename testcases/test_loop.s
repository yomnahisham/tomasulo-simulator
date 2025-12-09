LOAD R1, 0(R0)      # R1 = 5 (loop counter)
LOAD R2, 4(R0)      # R2 = 1 (decrement by 1)
LOAD R3, 8(R0)      # R3 = 10 (value to add)
ADD R4, R0, R0      # R4 = 0 (accumulator)
CALL LOOP          # Jump to LOOP

LOOP:
ADD R4, R4, R3      # R4 = R4 + 10 (accumulate)
SUB R1, R1, R2      # R1 = R1 - 1 (decrement counter)
BEQ R1, R0, DONE    # If R1 == 0, exit loop
BEQ R0, R0, LOOP    # Unconditional jump back to LOOP (branch back)

DONE:
STORE R4, 12(R0)    # memory[12] = 50
RET

