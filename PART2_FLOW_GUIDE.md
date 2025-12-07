# Part 2 (Tomasulo Core) - Sequential Flow Guide

## 🎯 Your Role (Part 2)

You implement: **RAT, RS, ROB, Register Renaming, Commit Stage, and Flush Logic**

Your teammate (Part 3) has already implemented: **Execution Manager, FUs, CDB, Write-Back, Branch Evaluator**

---

## 📊 Complete Cycle-by-Cycle Flow

Here's what happens **every cycle** in the simulator, in order:

```
┌─────────────────────────────────────────────────────────────┐
│                    START OF CYCLE N                          │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: WRITE-BACK (Part 3 calls Part 2)                   │
│ ─────────────────────────────────────────────────────────── │
│ Part 3's WriteBackStage.process_write_back() executes:      │
│   • Pops oldest result from write_queue                     │
│   • Broadcasts on CDB (rob_index, value, inst_type)         │
│   • Calls Part 2 functions:                                 │
│     ├─ update_rob_value(rob_index, value)     ← YOU DO THIS │
│     ├─ forward_to_rs(rob_index, value)        ← YOU DO THIS │
│     └─ update_rat(rob_index, value)           ← YOU DO THIS │
│                                                              │
│ What YOU must do in Part 2:                                 │
│   ✓ Mark ROB[rob_index].ready = True                        │
│   ✓ Store ROB[rob_index].value = value                      │
│   ✓ Scan all RS entries:                                    │
│       - If RS[i].Qj == rob_index → RS[i].Vj = value         │
│       - If RS[i].Qk == rob_index → RS[i].Vk = value         │
│   ✓ If RAT[dest_reg] == rob_index → update RAT              │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: EXECUTION TICK (Part 3 internal)                   │
│ ─────────────────────────────────────────────────────────── │
│ Part 3's FUPool.tick_all() executes:                        │
│   • All executing FUs decrement cycles_remaining            │
│   • FUs that reach 0 cycles → compute result                │
│   • Returns list of finished_executions                     │
│                                                              │
│ (No interaction with Part 2 here)                           │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: HANDLE FINISHED (Part 3 internal)                  │
│ ─────────────────────────────────────────────────────────── │
│ For each finished FU:                                       │
│   • If BEQ → calls notify_branch_result() ← YOU HANDLE THIS │
│   • Else → adds to write_queue for next write-back          │
│                                                              │
│ What YOU must do if BEQ finishes:                           │
│   ✓ notify_branch_result(rob_index, taken, target):         │
│     - Check if misprediction occurred                       │
│     - If mispredicted:                                      │
│         * Flush all RS entries after this branch            │
│         * Flush all ROB entries after this branch           │
│         * Reset RAT mappings                                │
│         * Notify Part 1 to restart PC at correct target     │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: SECOND WRITE-BACK (Part 3 internal)                │
│ ─────────────────────────────────────────────────────────── │
│ Part 3 calls process_write_back() again                     │
│   • Allows same-cycle write-back for newly finished         │
│   • Same as PHASE 1 above                                   │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 5: START EXECUTION (Part 3 calls Part 2)              │
│ ─────────────────────────────────────────────────────────── │
│ Part 3's ExecutionManager._start_ready_instructions():      │
│   • Calls get_ready_rs_entries()              ← YOU DO THIS │
│   • For each ready RS entry:                                │
│     - Calls get_rs_operands(rs_entry)         ← YOU DO THIS │
│     - Assigns to a free FU                                  │
│     - Calls mark_rs_executing(rs_entry_id)    ← YOU DO THIS │
│     - Starts FU execution                                   │
│                                                              │
│ What YOU must do in Part 2:                                 │
│   ✓ get_ready_rs_entries():                                 │
│       - Return list of RS entries where:                    │
│         * Busy == True                                      │
│         * Qj == None AND Qk == None (operands ready)        │
│         * Not already executing                             │
│                                                              │
│   ✓ get_rs_operands(rs_entry):                              │
│       - Return dict with Vj, Vk, immediate, pc, etc.        │
│                                                              │
│   ✓ mark_rs_executing(rs_entry_id):                         │
│       - Mark RS entry as "executing"                        │
│       - Prevent it from being started again                 │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 6: CDB CLEAR (Part 3 internal)                        │
│ ─────────────────────────────────────────────────────────── │
│ Part 3's CDB.clear() executes:                              │
│   • Clears current broadcast                                │
│   • Keeps pending broadcasts for next cycle                 │
│                                                              │
│ (No interaction with Part 2 here)                           │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 7: COMMIT (Part 2 - YOU DO THIS)                      │
│ ─────────────────────────────────────────────────────────── │
│ Your Commit Stage should run here:                          │
│   • Check ROB head                                          │
│   • If ROB[head].ready == True:                             │
│     ├─ Update Register File (call Part 1)                   │
│     ├─ For STORE: write to memory (call Part 1)             │
│     ├─ Clear RAT mapping if RAT[dest] == ROB[head]          │
│     ├─ Free RS entry                                        │
│     └─ Remove ROB head                                      │
│                                                              │
│ What YOU must do:                                           │
│   ✓ Check if ROB head is ready                              │
│   ✓ Commit 1 instruction per cycle                          │
│   ✓ Update register file via Part 1 interface               │
│   ✓ Free RS and ROB entries                                 │
│   ✓ Clear RAT entries                                       │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 8: ISSUE (Part 1 calls Part 2)                        │
│ ─────────────────────────────────────────────────────────── │
│ Part 1's Issue Stage calls your functions:                  │
│   • allocate_rob_entry(instruction)           ← YOU DO THIS │
│   • allocate_rs_entry(instruction, rob_idx)   ← YOU DO THIS │
│   • rename_registers(instruction, rob_idx)    ← YOU DO THIS │
│                                                              │
│ What YOU must do:                                           │
│   ✓ allocate_rob_entry():                                   │
│       - Add new entry to ROB tail                           │
│       - Return rob_index                                    │
│                                                              │
│   ✓ allocate_rs_entry():                                    │
│       - Find free RS of correct type                        │
│       - Fill RS fields (Op, Vj/Qj, Vk/Qk, dest, etc.)       │
│       - Use RAT to check if source regs are ready           │
│       - If RAT[src] exists → Qj/Qk = RAT[src]               │
│       - Else → Vj/Vk = Register[src]                        │
│                                                              │
│   ✓ rename_registers():                                     │
│       - Update RAT[dest_reg] = rob_index                    │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                      END OF CYCLE N                          │
│                    → Go to CYCLE N+1                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Detailed Data Flow Between Parts

### When Part 3 Writes Back a Result:

```
Part 3 (Execution Manager)
    ↓
[Instruction finishes execution]
    ↓
WriteBackStage.add_result(rob_idx, value, ...)
    ↓
WriteBackStage.process_write_back()
    ↓
CDB.broadcast(rob_idx, value, inst_type)
    ↓
┌─────────────────────────────────────────┐
│  YOUR PART 2 FUNCTIONS GET CALLED:     │
│                                         │
│  1. update_rob_value(rob_idx, value)   │
│     → Mark ROB[rob_idx] ready          │
│     → Store value in ROB               │
│                                         │
│  2. forward_to_rs(rob_idx, value)      │
│     → Scan all RS entries              │
│     → Update Qj/Qk → Vj/Vk             │
│                                         │
│  3. update_rat(rob_idx, value)         │
│     → If RAT still points here, update │
└─────────────────────────────────────────┘
```

### When Part 3 Wants to Start Execution:

```
Part 3 (Execution Manager)
    ↓
[Looking for ready instructions to execute]
    ↓
┌─────────────────────────────────────────┐
│  YOUR PART 2 FUNCTION GETS CALLED:     │
│                                         │
│  get_ready_rs_entries()                │
│     → Return list of RS where:         │
│        • Busy = True                   │
│        • Qj = None, Qk = None          │
│        • Not executing                 │
└─────────────────────────────────────────┘
    ↓
For each ready RS:
    ↓
┌─────────────────────────────────────────┐
│  YOUR PART 2 FUNCTIONS GET CALLED:     │
│                                         │
│  1. get_rs_operands(rs_entry)          │
│     → Return Vj, Vk, immediate, pc     │
│                                         │
│  2. mark_rs_executing(rs_entry_id)     │
│     → Mark RS as executing             │
└─────────────────────────────────────────┘
    ↓
Part 3 starts execution on FU
```

### When a Branch Finishes:

```
Part 3 (Branch Evaluator)
    ↓
[BEQ finishes execution]
    ↓
BranchEvaluator.evaluate_beq(...)
    ↓
┌─────────────────────────────────────────┐
│  YOUR PART 2 FUNCTION GETS CALLED:     │
│                                         │
│  notify_branch_result(rob_idx, taken,  │
│                       target)           │
│     → Check for misprediction          │
│     → If mispredicted:                 │
│         • Flush RS entries             │
│         • Flush ROB tail               │
│         • Reset RAT                    │
│         • Notify Part 1 to reset PC    │
└─────────────────────────────────────────┘
```

---

## 🛠️ Functions YOU Need to Implement

### 1. **get_ready_rs_entries() → List[Dict]**

**Called by:** Part 3 ExecutionManager (Phase 5)  
**Purpose:** Return RS entries ready to execute

```python
def get_ready_rs_entries() -> List[Dict[str, Any]]:
    ready_entries = []
    for rs_id, rs in enumerate(all_reservation_stations):
        if rs.busy and not rs.executing:
            # Check if operands ready
            if rs.Qj is None and rs.Qk is None:
                ready_entries.append({
                    "id": rs_id,
                    "instruction": rs.instruction,
                    "op": rs.Op,
                    # ... other fields
                })
    return ready_entries
```

---

### 2. **get_rs_operands(rs_entry) → Dict**

**Called by:** Part 3 ExecutionManager (Phase 5)  
**Purpose:** Extract operand values for FU

```python
def get_rs_operands(rs_entry: Dict[str, Any]) -> Dict[str, Any]:
    rs_id = rs_entry["id"]
    rs = reservation_stations[rs_id]

    return {
        "Vj": rs.Vj,
        "Vk": rs.Vk,
        "immediate": rs.immediate,
        "pc": rs.pc,
        # ... etc
    }
```

---

### 3. **update_rob_value(rob_index, value) → None**

**Called by:** Part 3 WriteBackStage (Phase 1)  
**Purpose:** Mark ROB entry as ready with value

```python
def update_rob_value(rob_index: int, value: Any) -> None:
    rob_entry = ROB[rob_index]
    rob_entry.ready = True
    rob_entry.value = value
```

---

### 4. **forward_to_rs(rob_index, value) → None**

**Called by:** Part 3 WriteBackStage (Phase 1)  
**Purpose:** Forward value to waiting RS entries

```python
def forward_to_rs(rob_index: int, value: Any) -> None:
    for rs in all_reservation_stations:
        if rs.Qj == rob_index:
            rs.Vj = value
            rs.Qj = None
        if rs.Qk == rob_index:
            rs.Vk = value
            rs.Qk = None
```

---

### 5. **update_rat(rob_index, value) → None**

**Called by:** Part 3 WriteBackStage (Phase 1)  
**Purpose:** Update RAT if mapping still active

```python
def update_rat(rob_index: int, value: Any) -> None:
    for reg_idx, rat_entry in enumerate(RAT.table):
        if rat_entry.valid and rat_entry.tag == rob_index:
            # Mapping still active, can update
            rat_entry.value = value
```

---

### 6. **notify_branch_result(rob_index, taken, target) → None**

**Called by:** Part 3 ExecutionManager (Phase 3)  
**Purpose:** Handle branch misprediction

```python
def notify_branch_result(rob_index: int, taken: bool, target: int) -> None:
    # Check if mispredicted (always predict not-taken)
    predicted_taken = False
    if taken != predicted_taken:
        # MISPREDICTION! FLUSH!
        flush_rs_after_rob(rob_index)
        flush_rob_after(rob_index)
        reset_rat()
        # Notify Part 1 to restart PC
        part1_interface.set_pc(target)
```

---

### 7. **mark_rs_executing(rs_entry_id) → None**

**Called by:** Part 3 ExecutionManager (Phase 5)  
**Purpose:** Mark RS as executing to prevent double-start

```python
def mark_rs_executing(rs_entry_id: int) -> None:
    rs = reservation_stations[rs_entry_id]
    rs.executing = True
```

---

### 8. **get_oldest_ready_rob_index() → Optional[int]**

**Called by:** Part 3 WriteBackStage (Phase 1)  
**Purpose:** CDB arbitration (oldest first)

```python
def get_oldest_ready_rob_index() -> Optional[int]:
    # Scan from ROB head
    for i in range(len(ROB)):
        idx = (ROB.head + i) % ROB.size
        if ROB[idx].ready:
            return idx
    return None
```

---

## 📝 Summary: Your Responsibilities

| Phase                  | What Part 3 Does             | What YOU (Part 2) Do                  |
| ---------------------- | ---------------------------- | ------------------------------------- |
| **1. Write-Back**      | Broadcasts result on CDB     | Update ROB, forward to RS, update RAT |
| **2. Execution Tick**  | FUs execute                  | Nothing (Part 3 internal)             |
| **3. Branch Handling** | Calls you with branch result | Check misprediction, flush if needed  |
| **4. Start Execution** | Asks for ready instructions  | Return ready RS, provide operands     |
| **5. Commit**          | Nothing                      | Commit ROB head, update registers     |
| **6. Issue**           | Nothing (Part 1 does this)   | Allocate ROB/RS, rename registers     |

---

## ✅ Key Design Principles

1. **Part 3 drives execution timing** → You maintain correctness
2. **CDB is the only way results propagate** → You listen to CDB broadcasts
3. **RS entries become ready when Qj/Qk are cleared** → You clear them on forwarding
4. **Commit happens in-order** → You manage ROB head advancement
5. **Branch flush is YOUR responsibility** → Part 3 just tells you the outcome

---

## 🧪 Testing Strategy

Your functions will be called like this:

```python
# Cycle N execution
execution_manager.execute_cycle(N)
    # Internally calls:
    # → update_rob_value()
    # → forward_to_rs()
    # → update_rat()
    # → get_ready_rs_entries()
    # → get_rs_operands()
    # → mark_rs_executing()
    # → notify_branch_result() (if branch finishes)

# Then you run commit
commit_stage.commit_cycle(N)

# Then Part 1 runs issue
issue_stage.issue_cycle(N)
```

---

## 🚀 Next Steps

1. Implement the 8 interface functions in `tomasulo_interface.py`
2. Create your commit stage logic
3. Test with Part 3's execution manager
4. Integrate with Part 1's issue stage

Need help with any specific function? Just ask!
