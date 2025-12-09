# Tomasulo Simulator

A comprehensive educational simulator for the Tomasulo algorithm, implementing out-of-order execution with register renaming, reservation stations, and a reorder buffer. This simulator provides both a command-line interface and a web-based GUI for visualizing processor internals in real-time.

## Features

- **Complete Tomasulo Algorithm Implementation**
  - Register renaming via Register Alias Table (RAT)
  - Reservation Stations (RS) for instruction scheduling
  - Reorder Buffer (ROB) for in-order commit
  - Common Data Bus (CDB) for result forwarding
  - Functional unit pipeline with realistic latencies

- **Instruction Set Support**
  - Arithmetic: ADD, SUB, NAND, MUL
  - Memory: LOAD, STORE
  - Control Flow: BEQ (branch if equal), CALL, RET
  - All instructions with proper operand forwarding and dependency handling

- **Advanced Features**
  - Branch prediction and misprediction recovery (ROB flushing)
  - Functional unit flushing on branch misprediction
  - CALL/RET support with return address management
  - Instruction re-issuing after flush
  - Complete timing tracking (issue, execute, write-back, commit)

- **Visualization & Debugging**
  - Web-based GUI with real-time state visualization
  - Step-by-step execution mode
  - Timing tables and performance metrics
  - Color-coded status indicators

## Project Structure

```
tomasulo-simulator/
├── src/
│   ├── execution/              # Execution engine implementation
│   │   ├── functional_units.py    # FU classes and pool (7 types)
│   │   ├── execution_manager.py   # Main execution coordinator
│   │   ├── cdb.py                 # Common Data Bus
│   │   ├── writeback.py           # Write-back stage
│   │   ├── branch_evaluator.py    # Branch evaluation logic
│   │   ├── timing_tracker.py      # Execution timing tracking
│   │   ├── reservation_station.py # RS implementations (12 stations)
│   │   └── rob.py                 # Reorder Buffer implementation
│   ├── interfaces/             # Core interfaces
│   │   ├── memory_interface.py    # Memory API
│   │   ├── register_interface.py  # Register file API
│   │   ├── tomasulo_interface.py  # RS/ROB/RAT management
│   │   ├── parser.py              # Assembly file parser
│   │   ├── instruction.py         # Instruction representation
│   │   └── issue_unit.py          # Instruction issue logic
│   ├── gui/                    # Web-based GUI
│   │   ├── app.py                 # FastAPI application
│   │   ├── templates/             # HTML templates
│   │   └── static/                # CSS and JavaScript
│   └── integration.py          # Complete integrated simulator
├── tests/                      # Unit tests
│   ├── test_functional_units.py
│   ├── test_execution_integration.py
│   ├── test_tomasulo_core.py
│   └── ...
└── testcases/                  # Assembly test files
    ├── example.s               # Comprehensive example
    ├── test1.s                 # Basic operations
    ├── test2.s                 # Branch flushing
    ├── test3.s                 # CALL instruction
    └── test_call_ret.s         # CALL/RET function calls
```

## Components

### Functional Units
- **AddSubFU**: ADD/SUB instructions (2 cycles) - 4 units
- **NandFU**: NAND instructions (1 cycle) - 2 units
- **MulFU**: MUL instructions (12 cycles) - 1 unit
- **LoadFU**: LOAD instructions (6 cycles: 2 address + 4 memory) - 2 units
- **StoreFU**: STORE instructions (6 cycles: 2 address + 4 memory) - 1 unit
- **BeqFU**: BEQ instructions (1 cycle) - 2 units
- **CallRetFU**: CALL/RET instructions (1 cycle) - 1 unit

### Reservation Stations (12 total)
- **LOAD1, LOAD2**: Load operations
- **STORE**: Store operations
- **BEQ1, BEQ2**: Branch operations
- **CALL/RET**: Function call/return
- **ADD/SUB1-4**: Arithmetic operations (4 stations)
- **NAND**: NAND operations
- **MUL**: Multiply operations

### Reorder Buffer
- 8-entry circular buffer
- Tracks instruction state (ready/not ready)
- Manages in-order commit
- Supports flushing on branch misprediction

### Register Alias Table (RAT)
- Maps 8 architectural registers to ROB indices
- Enables register renaming for out-of-order execution
- Cleared on instruction commit


## Usage

### Command Line Interface

Run a complete simulation:

```bash
python -m src.integration testcases/test1.s
```

With verbose output:

```bash
python -m src.integration testcases/test1.s --verbose
```

### Programmatic Usage

```python
from src.integration import IntegratedSimulator

# Create simulator with assembly file
simulator = IntegratedSimulator("testcases/test1.s")

# Run complete simulation
timing_info = simulator.run(verbose=True)

# Or step through cycle by cycle
state = simulator.step_cycle()
print(state["cycle"], state["instructions"])

# Get timing table
simulator.print_timing_table()

# Get final state
simulator.print_final_state()
```

### Educational GUI Application

The simulator includes a web-based educational GUI for visualizing processor internals.

#### Starting the GUI

1. Start the GUI server:
```bash
uvicorn src.gui.app:app --reload
```

2. Open your browser and navigate to:
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
  - Instruction list with status tracking
- **Timing Table**: View issue, execution, write, and commit cycles for all instructions
- **Performance Metrics**: IPC, CPI, pipeline utilization
- **File Loading**: Load assembly files (.s format) for simulation
- **Reset & Reload**: Reset simulator state or load new programs

#### Using the GUI

1. **Load a Program**: Click "Load Program" and select an assembly file
   - `testcases/example.s` - Comprehensive example with all instruction types
   - `testcases/test1.s` - Basic operations
   - `testcases/test2.s` - Branch prediction and flushing
   - `testcases/test3.s` - CALL instruction
   - `testcases/test_call_ret.s` - Function calls with CALL/RET

2. **Step Through**: Click "Step Cycle" to execute one cycle at a time and observe state changes

3. **Run Full Simulation**: Click "Run Simulation" to execute the entire program automatically

4. **Reset**: Click "Reset" to return to the initial state

The GUI provides professional color-coded visualizations:
- 🟢 **Green**: Ready/Complete instructions and ROB entries
- 🟡 **Yellow/Amber**: Executing/Waiting instructions
- 🔵 **Blue**: Issued instructions
- ⚪ **Gray**: Empty/Free reservation stations
- 🔴 **Red**: Flushed instructions (strikethrough)

#### API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Assembly Language Format

The simulator supports a simple assembly language with the following instructions:

### Arithmetic Instructions
```
ADD R1, R2, R3    # R1 = R2 + R3
SUB R1, R2, R3    # R1 = R2 - R3
NAND R1, R2, R3   # R1 = ~(R2 & R3)
MUL R1, R2, R3    # R1 = R2 * R3 (16-bit result)
```

### Memory Instructions
```
LOAD R1, 4(R0)    # R1 = memory[R0 + 4]
STORE R1, 8(R0)   # memory[R0 + 8] = R1
```

### Control Flow Instructions
```
BEQ R1, R2, LABEL # if R1 == R2, branch to LABEL
CALL FUNC          # Call function FUNC, save return address in R1
RET                # Return: jump to address in R1
```

### Labels
```
LABEL:
# Instructions follow
```

### Comments
```
# This is a comment
```

## Test Cases

### test1.s
Basic operations demonstrating:
- Memory loads
- Arithmetic operations
- Data dependencies
- Memory stores

### test2.s
Branch prediction and flushing:
- BEQ instruction with misprediction
- ROB flushing on branch taken
- Functional unit flushing
- Instruction re-issuing

### test3.s
CALL instruction:
- Function call with return address
- Speculative instruction flushing
- Correct path execution

### test_call_ret.s
Complete function call/return:
- CALL saves return address in R1
- Function body execution
- RET returns to saved address
- Continuation after return

## Key Features Explained

### Branch Prediction & Flushing
- Instructions are speculatively executed assuming branches are not taken
- When a branch is taken, all instructions after the branch are flushed from:
  - Reorder Buffer (ROB)
  - Reservation Stations (RS)
  - Functional Units (FU)
- Flushed instructions can be re-issued and re-executed

### Register Renaming
- The Register Alias Table (RAT) maps architectural registers to ROB entries
- Enables multiple instructions to write to the same register out-of-order
- RAT entries are cleared when instructions commit

### Operand Forwarding
- Results are forwarded via the Common Data Bus (CDB)
- Waiting instructions receive operands as soon as they're available
- Eliminates unnecessary stalls

### CALL/RET Support
- CALL saves the return address (PC+1) in R1
- RET reads R1 and jumps to the return address
- Proper handling of function calls and returns

## Architecture Details

### Execution Pipeline
1. **Issue**: Instruction issued to appropriate RS (1 per cycle)
2. **Execute**: Instruction waits for operands, then executes on FU
3. **Write-back**: Result written to ROB and forwarded via CDB
4. **Commit**: Instruction commits in-order, updates register file

### Timing
- Each instruction tracks: issue, start_exec, finish_exec, write, commit cycles
- Functional units have realistic latencies (1-12 cycles)
- CDB enforces single write-back per cycle

### Branch Handling
- BEQ: Evaluates condition, flushes if mispredicted
- CALL: Always taken, saves return address, jumps to target
- RET: Always taken, jumps to address in R1

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Structure
- `src/execution/`: Core execution engine
- `src/interfaces/`: Processor component interfaces
- `src/gui/`: Web-based visualization
- `src/integration.py`: Complete integrated simulator


## Acknowledgments

This simulator is designed for educational purposes to help students understand the Tomasulo algorithm and out-of-order execution in modern processors.
