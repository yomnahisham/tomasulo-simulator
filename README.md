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
│       ├── parser.py               
│       ├── instruction.py          
│       └── issue_unit.py          
├── tests/                  # Unit tests
└── testcases/ # Assembly files for testing
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

### Parser & Instruction Issuer
- Parser reads assembly files and converts lines into `Instruction` objects.
- IssueUnit issues instructions one per cycle, tracks issued instructions, and records issue timing.

### Common Data Bus (CDB)
enforces single write-back per cycle constraint and broadcasts results to ROB and waiting RS entries.

### Write-Back Stage
processes finished executions, broadcasts via CDB, and updates ROB/RAT/RS.

### Branch Evaluator
evaluates BEQ conditions and computes branch targets for CALL/RET instructions.

### Timing Tracker
records execution timing (issue, start_exec, finish_exec, write, commit) for all instructions.

## Usage

### Command Line Interface

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

### Educational GUI Application

The simulator includes a web-based educational GUI for visualizing processor internals.

#### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the GUI server:
```bash
uvicorn src.gui.app:app --reload
```

3. Open your browser and navigate to:
```
http://localhost:8000
```

#### GUI Features

- **Step-by-Step Execution**: Execute one cycle at a time and observe processor state changes
- **Full Simulation**: Run entire programs and view final results
- **Real-Time Visualization**:
  - Reservation Stations (all 12 RS with operands and status)
  - Reorder Buffer (ROB entries with ready status)
  - Register Alias Table (RAT mappings)
  - Register File (all 8 registers)
  - Memory (non-zero addresses)
  - Functional Units (status and cycles remaining)
  - Common Data Bus (CDB broadcasts)
- **Timing Table**: View issue, execution, write, and commit cycles for all instructions
- **Performance Metrics**: IPC, CPI, pipeline utilization
- **File Loading**: Load assembly files (.s format) for simulation

#### API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

#### Using the GUI

1. **Load a Program**: Click "Load Program" and select an assembly file
   - Try the example file: `testcases/example.s` (demonstrates various instruction types)
   - Or use: `testcases/test1.s` (simpler example)
2. **Step Through**: Click "Step Cycle" to execute one cycle at a time and observe state changes
3. **Run Full Simulation**: Click "Run Simulation" to execute the entire program automatically
4. **Reset**: Click "Reset" to return to the initial state

The GUI provides professional color-coded visualizations:
- 🟢 **Green**: Ready/Complete instructions and ROB entries
- 🟡 **Yellow/Amber**: Executing/Waiting instructions
- 🔵 **Blue**: Issued instructions
- ⚪ **Gray**: Empty/Free reservation stations

#### Example Program

An example assembly program is provided at `testcases/example.s` that demonstrates:
- Memory load operations
- Arithmetic operations (ADD, MUL, NAND)
- Data dependencies between instructions
- Memory store operations
- Branch instructions (BEQ)
- Function calls (CALL/RET)

Load this file to see a comprehensive demonstration of the Tomasulo algorithm in action.



