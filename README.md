# Tomasulo Simulator

## Project Structure

```
tomasulo-simulator/
├── src/
│   ├── execution/          # Execution engine implementation
│   │   ├── functional_units.py    # FU classes and pool
│   │   ├── execution_manager.py   # Main execution coordinator
│   │   ├── cdb.py                 # Common Data Bus
│   │   ├── writeback.py           # Write-back stage
│   │   ├── branch_evaluator.py    # Branch evaluation
│   │   └── timing_tracker.py      # Execution timing tracking
│   └── interfaces/         # Interface definitions (stubs)
│       ├── memory_interface.py    # Part 1 memory API
│       ├── register_interface.py  # Part 1 register API
│       └── tomasulo_interface.py  # Part 2 RS/ROB/RAT API
└── tests/                  # Unit tests
```

## Components

### Functional Units
- **AddSubFU**: ADD/SUB instructions (2 cycles)
- **NandFU**: NAND instructions (1 cycle)
- **MulFU**: MUL instructions (12 cycles)
- **LoadFU**: LOAD instructions (6 cycles: 2 address + 4 memory)
- **StoreFU**: STORE instructions (6 cycles: 2 address + 4 memory)
- **BeqFU**: BEQ instructions (1 cycle)
- **CallRetFU**: CALL/RET instructions (1 cycle)

### Execution Manager
coordinates all functional units, handles cycle-by-cycle execution, and manages the execution pipeline.

### Common Data Bus (CDB)
enforces single write-back per cycle constraint and broadcasts results to ROB and waiting RS entries.

### Write-Back Stage
processes finished executions, broadcasts via CDB, and updates ROB/RAT/RS.

### Branch Evaluator
evaluates BEQ conditions and computes branch targets for CALL/RET instructions.

### Timing Tracker
records execution timing (issue, start_exec, finish_exec, write, commit) for all instructions.

## Usage

```python
from src.execution.execution_manager import ExecutionManager

# create mock interfaces (to be implemented by Parts 1 and 2)
memory_interface = ...  # Part 1 implementation
tomasulo_interface = ...  # Part 2 implementation

# create execution manager
exec_manager = ExecutionManager(memory_interface, tomasulo_interface)

# each cycle, call execute_cycle
for cycle in range(1, max_cycles + 1):
    exec_manager.execute_cycle(cycle)
    
    # get execution state for GUI
    state = exec_manager.get_execution_state()
    
    # get timing information
    timing = exec_manager.get_timing_info()
```



