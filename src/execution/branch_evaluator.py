"""branch evaluation logic"""

from typing import Dict, Any, Tuple


class BranchEvaluator:
    """evaluates branch conditions and computes targets"""
    
    def evaluate_beq(self, operand_a: int, operand_b: int, offset: int, pc: int) -> Dict[str, Any]:
        """
        evaluate BEQ condition and compute target address
        
        args:
            operand_a: value of rA
            operand_b: value of rB
            offset: branch offset (5-bit signed)
            pc: program counter value
            
        returns:
            dictionary with:
                - taken: bool (whether branch is taken)
                - target: int (target address)
                - condition_met: bool (whether condition was met)
        """
        # compare operands
        condition_met = (operand_a == operand_b)
        
        # compute target address
        if condition_met:
            # branch taken: PC + 1 + offset
            target = (pc + 1 + offset) & 0xFFFF
        else:
            # branch not taken: PC + 1
            target = (pc + 1) & 0xFFFF
        
        return {
            "taken": condition_met,
            "target": target,
            "condition_met": condition_met,
        }
    
    def evaluate_call(self, label_offset: int, pc: int) -> Dict[str, Any]:
        """
        evaluate CALL instruction
        
        args:
            label_offset: 7-bit signed constant (label encoding)
            pc: program counter value
            
        returns:
            dictionary with:
                - target: int (target address)
                - return_address: int (PC + 1 to store in R1)
        """
        target = (pc + 1 + label_offset) & 0xFFFF
        return_address = (pc + 1) & 0xFFFF
        
        return {
            "target": target,
            "return_address": return_address,
        }
    
    def evaluate_ret(self, r1_value: int) -> Dict[str, Any]:
        """
        evaluate RET instruction
        
        args:
            r1_value: value in R1 (return address)
            
        returns:
            dictionary with:
                - target: int (return address from R1)
        """
        target = r1_value & 0xFFFF
        
        return {
            "target": target,
        }


