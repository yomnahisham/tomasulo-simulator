LOAD R2, 0(R0)      # R2 = 10
LOAD R3, 4(R0)      # R3 = 20

# Call function and save return address in R1
CALL FUNC           # R1 = PC+1 (return address), jump to FUNC

# Return point - should continue here after RET
ADD R7, R6, R2      # R7 = R6 + R2 = 570 + 10 = 580
STORE R7, 8(R0)     # memory[8] = 580
# End of program

FUNC:
# Function body
ADD R4, R2, R3      # R4 = R2 + R3 = 30
MUL R5, R4, R3      # R5 = R4 * R3 = 600
SUB R6, R5, R4      # R6 = R5 - R4 = 570
RET                 # Return: PC = R1 (return address)
