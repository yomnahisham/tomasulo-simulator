#!/usr/bin/env python3
"""
Test script to run all test cases and verify they pass
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.integration import IntegratedSimulator

def test_test1():
    """Test case 1: Basic operations"""
    print("\n" + "="*80)
    print("Running test1.s")
    print("="*80)
    sim = IntegratedSimulator('testcases/test1.s')
    # Initialize memory as needed
    sim.memory.write_memory(0, 5)  # For LOAD R1, 0(R0)
    sim.run(verbose=False)
    
    # Check results - test1 doesn't have clear expected values, just check it completes
    print(f"✓ test1.s completed in {sim.current_cycle} cycles")
    return True

def test_test2():
    """Test case 2: Branch taken with flushing"""
    print("\n" + "="*80)
    print("Running test2.s")
    print("="*80)
    sim = IntegratedSimulator('testcases/test2.s')
    # Initialize memory: memory[0] = 5, memory[4] = 5
    sim.memory.write_memory(0, 5)
    sim.memory.write_memory(4, 5)
    sim.run(verbose=False)
    
    # Expected: memory[12] = 50 (R7 = 10 * 5 = 50)
    # memory[8] should NOT be set (flushed instructions)
    mem12 = sim.memory.read_memory(12)
    mem8 = sim.memory.read_memory(8)
    r6 = sim.register_file.read(6)
    r7 = sim.register_file.read(7)
    
    print(f"  R6: {r6} (expected: 10)")
    print(f"  R7: {r7} (expected: 50)")
    print(f"  memory[8]: {mem8} (expected: 0, should be flushed)")
    print(f"  memory[12]: {mem12} (expected: 50)")
    
    success = (r6 == 10 and r7 == 50 and mem12 == 50 and mem8 == 0)
    if success:
        print(f"✓ test2.s passed in {sim.current_cycle} cycles")
    else:
        print(f"✗ test2.s failed in {sim.current_cycle} cycles")
    return success

def test_test3():
    """Test case 3: CALL with flushing"""
    print("\n" + "="*80)
    print("Running test3.s")
    print("="*80)
    sim = IntegratedSimulator('testcases/test3.s')
    # Initialize memory: memory[0] = 5, memory[4] = 5
    sim.memory.write_memory(0, 5)
    sim.memory.write_memory(4, 5)
    sim.run(verbose=False)
    
    # Expected: memory[12] = 50 (R7 = 10 * 5 = 50)
    # memory[8] should NOT be set (flushed instructions)
    mem12 = sim.memory.read_memory(12)
    mem8 = sim.memory.read_memory(8)
    r6 = sim.register_file.read(6)
    r7 = sim.register_file.read(7)
    
    print(f"  R6: {r6} (expected: 10)")
    print(f"  R7: {r7} (expected: 50)")
    print(f"  memory[8]: {mem8} (expected: 0, should be flushed)")
    print(f"  memory[12]: {mem12} (expected: 50)")
    
    success = (r6 == 10 and r7 == 50 and mem12 == 50 and mem8 == 0)
    if success:
        print(f"✓ test3.s passed in {sim.current_cycle} cycles")
    else:
        print(f"✗ test3.s failed in {sim.current_cycle} cycles")
    return success

def test_test4():
    """Test case 4: CALL/RET"""
    print("\n" + "="*80)
    print("Running test4.s")
    print("="*80)
    sim = IntegratedSimulator('testcases/test4.s')
    # Initialize memory: memory[0] = 10, memory[4] = 20
    sim.memory.write_memory(0, 10)
    sim.memory.write_memory(4, 20)
    sim.run(verbose=False)
    
    # Expected: memory[8] = 580 (R7 = 570 + 10 = 580)
    mem8 = sim.memory.read_memory(8)
    r4 = sim.register_file.read(4)
    r5 = sim.register_file.read(5)
    r6 = sim.register_file.read(6)
    r7 = sim.register_file.read(7)
    
    print(f"  R4: {r4} (expected: 30)")
    print(f"  R5: {r5} (expected: 600)")
    print(f"  R6: {r6} (expected: 570)")
    print(f"  R7: {r7} (expected: 580)")
    print(f"  memory[8]: {mem8} (expected: 580)")
    
    success = (r4 == 30 and r5 == 600 and r6 == 570 and r7 == 580 and mem8 == 580)
    if success:
        print(f"✓ test4.s passed in {sim.current_cycle} cycles")
    else:
        print(f"✗ test4.s failed in {sim.current_cycle} cycles")
    return success

def test_example():
    """Example test case"""
    print("\n" + "="*80)
    print("Running example.s")
    print("="*80)
    sim = IntegratedSimulator('testcases/example.s')
    # Initialize memory as needed
    sim.memory.write_memory(0, 5)  # For LOAD R1, 0(R0)
    sim.run(verbose=False)
    
    # Check results - example doesn't have clear expected values, just check it completes
    print(f"✓ example.s completed in {sim.current_cycle} cycles")
    return True

def test_test_loop():
    """Test loop case"""
    print("\n" + "="*80)
    print("Running test_loop.s")
    print("="*80)
    sim = IntegratedSimulator('testcases/test_loop.s')
    # Initialize memory: memory[0] = 5, memory[4] = 1, memory[8] = 10
    sim.memory.write_memory(0, 5)
    sim.memory.write_memory(4, 1)
    sim.memory.write_memory(8, 10)
    sim.run(verbose=False)
    
    # Expected: R4 = 50, memory[12] = 50
    r4 = sim.register_file.read(4)
    mem12 = sim.memory.read_memory(12)
    
    print(f"  R4: {r4} (expected: 50)")
    print(f"  memory[12]: {mem12} (expected: 50)")
    
    success = (r4 == 50 and mem12 == 50)
    if success:
        print(f"✓ test_loop.s passed in {sim.current_cycle} cycles")
    else:
        print(f"✗ test_loop.s failed in {sim.current_cycle} cycles")
    return success

def main():
    """Run all test cases"""
    print("\n" + "="*80)
    print("Running All Test Cases")
    print("="*80)
    
    results = []
    results.append(("test1.s", test_test1()))
    results.append(("test2.s", test_test2()))
    results.append(("test3.s", test_test3()))
    results.append(("test4.s", test_test4()))
    results.append(("example.s", test_example()))
    results.append(("test_loop.s", test_test_loop()))
    
    print("\n" + "="*80)
    print("Test Results Summary")
    print("="*80)
    
    passed = 0
    failed = 0
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
