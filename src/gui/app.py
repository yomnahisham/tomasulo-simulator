"""
FastAPI application for Tomasulo Simulator GUI

Provides REST API endpoints for simulator control and state access.
Automatic OpenAPI documentation available at /docs
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.integration import IntegratedSimulator

app = FastAPI(
    title="Tomasulo Simulator API",
    description="Educational GUI API for Tomasulo processor simulation",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global simulator instance
simulator: Optional[IntegratedSimulator] = None
# Track temp file for cleanup
current_temp_file: Optional[Path] = None
# State history for undo/redo
state_history: list = []
history_index: int = -1
max_history_size: int = 100
# Breakpoints (instruction IDs)
breakpoints: set = set()

# Mount static files
static_path = Path(__file__).parent / "static"
templates_path = Path(__file__).parent / "templates"

# Create Jinja2Templates for HTML rendering
templates = Jinja2Templates(directory=str(templates_path))

if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main GUI page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/state")
async def get_state():
    """
    Get current simulator state
    
    Returns complete processor state including:
    - Current cycle
    - Instructions with status
    - Reservation stations
    - ROB entries
    - RAT mappings
    - Register file
    - Memory
    - Functional units
    - CDB state
    - Timing information
    """
    if simulator is None:
        # Return empty state instead of error
        return {
            "cycle": 0,
            "instructions": [],
            "reservation_stations": {},
            "rob": [],
            "rat": [None] * 8,
            "registers": [0] * 8,
            "memory": {},
            "functional_units": {},
            "cdb": {"busy": False, "rob_index": None, "value": None, "instruction_type": None, "pending_count": 0},
            "timing": {},
            "is_complete": True,
            "has_instructions": False
        }
    return simulator.get_current_state()


@app.post("/api/step")
async def step_cycle():
    """
    Execute one cycle and return new state
    
    Performs:
    1. Issue next instruction (if available)
    2. Execute one cycle
    3. Commit if possible
    
    Returns updated processor state
    """
    global state_history, history_index
    
    if simulator is None:
        raise HTTPException(status_code=400, detail="No program loaded. Please load an assembly file first.")
    
    # Check for breakpoints before stepping
    current_state = simulator.get_current_state()
    next_instr_id = None
    if simulator.issue_unit._next_index < len(simulator.instructions):
        next_instr = simulator.instructions[simulator.issue_unit._next_index]
        next_instr_id = next_instr.get_instr_id()
    
    # Step the cycle
    new_state = simulator.step_cycle()
    
    # Check if we hit a breakpoint
    hit_breakpoint = False
    if next_instr_id and next_instr_id in breakpoints:
        hit_breakpoint = True
    
    # Also check if any instruction being executed/committed is at a breakpoint
    for instr in new_state.get("instructions", []):
        if instr.get("id") in breakpoints and instr.get("status") in ["executing", "completed", "committed"]:
            hit_breakpoint = True
            break
    
    # Save to history
    if history_index < len(state_history) - 1:
        # If we're not at the end, truncate history
        state_history = state_history[:history_index + 1]
    
    state_history.append(new_state)
    if len(state_history) > max_history_size:
        state_history.pop(0)
    else:
        history_index += 1
    
    new_state["hit_breakpoint"] = hit_breakpoint
    return new_state


@app.post("/api/run")
async def run_simulation():
    """
    Run full simulation to completion
    
    Executes cycles until program completes.
    Returns final processor state.
    """
    if simulator is None:
        raise HTTPException(status_code=400, detail="No program loaded. Please load an assembly file first.")
    
    max_cycles = 1000
    while simulator.current_cycle < max_cycles:
        simulator.step_cycle()
        if simulator._is_complete():
            break
    
    return simulator.get_current_state()


@app.post("/api/reset")
async def reset_simulator():
    """
    Reset simulator to initial state
    
    Clears all state and returns to beginning of program.
    """
    global simulator, current_temp_file, state_history, history_index, breakpoints
    
    if simulator is None:
        raise HTTPException(status_code=400, detail="No program loaded. Please load an assembly file first.")
    
    try:
        # Check if the original file still exists
        if current_temp_file is None or not current_temp_file.exists():
            raise HTTPException(
                status_code=400, 
                detail="Original program file no longer available. Please reload the program."
            )
        
        logger.info("Resetting simulator to initial state")
        state = simulator.reset()
        logger.info("Simulator reset successfully")
        
        # Reset history
        state_history = [state]
        history_index = 0
        breakpoints.clear()
        
        return state
    except FileNotFoundError as e:
        error_msg = f"Program file not found: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        error_msg = f"Error resetting simulator: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/api/load")
async def load_program(file: UploadFile = File(...)):
    """
    Load assembly file and initialize simulator
    
    Args:
        file: Assembly file (.s format)
    
    Returns initial processor state
    """
    global simulator, current_temp_file
    
    # Clean up previous temp file if it exists
    if current_temp_file is not None and current_temp_file.exists():
        try:
            current_temp_file.unlink()
            logger.info(f"Cleaned up previous temp file: {current_temp_file}")
        except Exception as e:
            logger.warning(f"Could not clean up previous temp file {current_temp_file}: {e}")
    
    # Save uploaded file temporarily
    import tempfile
    import uuid
    temp_dir = Path(tempfile.gettempdir()) / "tomasulo_simulator"
    temp_dir.mkdir(exist_ok=True, parents=True)
    
    # Use a unique filename to avoid conflicts
    temp_file = temp_dir / f"{uuid.uuid4()}_{file.filename}"
    
    try:
        logger.info(f"Loading program: {file.filename}")
        
        # Validate file extension (case insensitive)
        if not file.filename.lower().endswith('.s'):
            error_msg = f"File must have .s extension, got: {file.filename}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Read file content
        try:
            content = await file.read()
            logger.info(f"Read {len(content)} bytes from file")
        except Exception as e:
            error_msg = f"Error reading uploaded file: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Validate file content is not empty
        if len(content) == 0:
            error_msg = "Uploaded file is empty"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Validate file size (reasonable limit: 1MB)
        max_size = 1024 * 1024  # 1MB
        if len(content) > max_size:
            error_msg = f"File too large: {len(content)} bytes (max {max_size} bytes)"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Write uploaded file to temp location
        try:
            with open(temp_file, "wb") as f:
                f.write(content)
            logger.info(f"Wrote file to temporary location: {temp_file}")
        except Exception as e:
            error_msg = f"Error writing temporary file: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Initialize simulator
        try:
            logger.info(f"Initializing simulator with file: {temp_file}")
            simulator = IntegratedSimulator(str(temp_file))
            logger.info(f"Simulator initialized successfully with {len(simulator.instructions)} instructions")
        except FileNotFoundError as e:
            error_msg = f"Assembly file not found: {str(e)}"
            logger.error(error_msg, exc_info=True)
            # Clean up temp file on error
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except:
                pass
            raise HTTPException(status_code=400, detail=error_msg)
        except ValueError as e:
            # Extract line number if present
            error_msg = str(e)
            line_num = None
            if error_msg.startswith("Line "):
                try:
                    line_num = int(error_msg.split(":")[0].split()[-1])
                except:
                    pass
            
            error_detail = {
                "message": error_msg,
                "line_number": line_num
            }
            logger.error(f"Invalid assembly syntax: {error_msg}", exc_info=True)
            # Clean up temp file on error
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except:
                pass
            raise HTTPException(status_code=400, detail=error_detail)
        except Exception as e:
            error_msg = f"Error initializing simulator: {type(e).__name__}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            # Clean up temp file on error
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except:
                pass
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Get initial state
        try:
            logger.info("Retrieving initial simulator state")
            state = simulator.get_current_state()
            logger.info("Successfully loaded program and retrieved initial state")
        except Exception as e:
            error_msg = f"Error retrieving initial state: {type(e).__name__}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            # Don't delete temp file here - simulator might need it for reset
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Store temp file reference for cleanup on next load
        # We keep it for now since simulator might need it for reset functionality
        current_temp_file = temp_file
        logger.info(f"Program loaded successfully. Temp file kept at: {temp_file}")
        
        # Initialize history with initial state
        global state_history, history_index, breakpoints
        state_history = [state]
        history_index = 0
        breakpoints.clear()
        
        return state
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any unexpected exceptions
        error_msg = f"Unexpected error loading program: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        # Clean up temp file on error
        try:
            if temp_file.exists():
                temp_file.unlink()
        except:
            pass
        raise HTTPException(status_code=400, detail=error_msg)


@app.post("/api/validate")
async def validate_assembly(file: UploadFile = File(...)):
    """
    Validate assembly file syntax without loading it
    
    Returns validation result with line numbers for any errors
    """
    try:
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Save to temp file for parsing
        import tempfile
        import uuid
        temp_dir = Path(tempfile.gettempdir()) / "tomasulo_simulator"
        temp_dir.mkdir(exist_ok=True, parents=True)
        temp_file = temp_dir / f"{uuid.uuid4()}_validate_{file.filename}"
        
        with open(temp_file, "wb") as f:
            f.write(content)
        
        try:
            # Try to parse
            from ..interfaces.parser import Parser
            parser = Parser()
            instructions = parser.parse(str(temp_file))
            
            return {
                "valid": True,
                "instruction_count": len(instructions),
                "errors": []
            }
        except ValueError as e:
            error_msg = str(e)
            line_num = None
            if error_msg.startswith("Line "):
                try:
                    line_num = int(error_msg.split(":")[0].split()[-1])
                    error_msg = ":".join(error_msg.split(":")[1:]).strip()
                except:
                    pass
            
            return {
                "valid": False,
                "instruction_count": 0,
                "errors": [{
                    "line": line_num,
                    "message": error_msg
                }]
            }
        except Exception as e:
            return {
                "valid": False,
                "instruction_count": 0,
                "errors": [{
                    "line": None,
                    "message": f"Parse error: {str(e)}"
                }]
            }
        finally:
            # Clean up temp file
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except:
                pass
    except Exception as e:
        return {
            "valid": False,
            "instruction_count": 0,
            "errors": [{
                "line": None,
                "message": f"Error reading file: {str(e)}"
            }]
        }


@app.get("/api/timing")
async def get_timing():
    """
    Get timing table data for all instructions
    
    Returns timing information (issue, start_exec, finish_exec, write, commit)
    for all instructions.
    """
    if simulator is None:
        raise HTTPException(status_code=400, detail="No program loaded. Please load an assembly file first.")
    
    timing_info = simulator.timing_tracker.get_all_timing()
    timing_table = []
    
    for instr in simulator.instructions:
        instr_id = instr.get_instr_id()
        timing = timing_info.get(instr_id, {})
        timing_table.append({
            "id": instr_id,
            "name": instr.get_name(),
            "issue": timing.get("issue"),
            "start_exec": timing.get("start_exec"),
            "finish_exec": timing.get("finish_exec"),
            "write": timing.get("write"),
            "commit": timing.get("commit")
        })
    
    return {"timing_table": timing_table}


@app.get("/api/metrics")
async def get_metrics():
    """
    Get performance metrics
    
    Returns:
    - Total cycles
    - Instructions per cycle (IPC)
    - Cycles per instruction (CPI)
    - Pipeline utilization
    """
    if simulator is None:
        # Return empty metrics instead of error
        return {
            "total_cycles": 0,
            "total_instructions": 0,
            "committed_instructions": 0,
            "instructions_per_cycle": 0.0,
            "cycles_per_instruction": 0.0,
            "instructions_in_flight": 0,
            "pipeline_utilization": 0.0
        }
    
    timing_info = simulator.timing_tracker.get_all_timing()
    total_instructions = len(simulator.instructions)
    current_cycle = simulator.current_cycle
    
    # Calculate metrics
    if total_instructions > 0 and current_cycle > 0:
        ipc = total_instructions / current_cycle
        cpi = current_cycle / total_instructions
    else:
        ipc = 0.0
        cpi = 0.0
    
    # Count committed instructions
    committed_count = sum(1 for t in timing_info.values() if t.get("commit") is not None)
    
    # Calculate pipeline utilization (instructions in flight)
    instructions_in_flight = sum(1 for instr in simulator.instructions 
                                 if any(timing_info.get(instr.get_instr_id(), {}).get(stage) is not None 
                                        for stage in ["issue", "start_exec", "finish_exec", "write"]) 
                                 and timing_info.get(instr.get_instr_id(), {}).get("commit") is None)
    
    return {
        "total_cycles": current_cycle,
        "total_instructions": total_instructions,
        "committed_instructions": committed_count,
        "instructions_per_cycle": ipc,
        "cycles_per_instruction": cpi,
        "instructions_in_flight": instructions_in_flight,
        "pipeline_utilization": instructions_in_flight / max(total_instructions, 1)
    }


@app.post("/api/breakpoints")
async def set_breakpoints(instruction_ids: list[int]):
    """
    Set breakpoints on instruction IDs
    
    Args:
        instruction_ids: List of instruction IDs to set breakpoints on
    """
    global breakpoints
    breakpoints = set(instruction_ids)
    return {"breakpoints": list(breakpoints)}


@app.get("/api/breakpoints")
async def get_breakpoints():
    """Get current breakpoints"""
    return {"breakpoints": list(breakpoints)}


@app.post("/api/undo")
async def undo():
    """Undo to previous state"""
    global history_index
    
    if history_index <= 0:
        raise HTTPException(status_code=400, detail="No previous state to undo to")
    
    history_index -= 1
    return state_history[history_index]


@app.post("/api/redo")
async def redo():
    """Redo to next state"""
    global history_index
    
    if history_index >= len(state_history) - 1:
        raise HTTPException(status_code=400, detail="No next state to redo to")
    
    history_index += 1
    return state_history[history_index]


@app.get("/api/history")
async def get_history_info():
    """Get history information"""
    return {
        "current_index": history_index,
        "total_states": len(state_history),
        "can_undo": history_index > 0,
        "can_redo": history_index < len(state_history) - 1
    }


@app.get("/api/compare")
async def compare_states(index1: int, index2: int):
    """
    Compare two states from history
    
    Args:
        index1: First state index
        index2: Second state index
    """
    if index1 < 0 or index1 >= len(state_history):
        raise HTTPException(status_code=400, detail=f"Invalid state index: {index1}")
    if index2 < 0 or index2 >= len(state_history):
        raise HTTPException(status_code=400, detail=f"Invalid state index: {index2}")
    
    return {
        "state1": state_history[index1],
        "state2": state_history[index2],
        "index1": index1,
        "index2": index2
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


