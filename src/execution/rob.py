"""Reorder Buffer class with ROB entry management."""

from typing import Any, List, Optional, Tuple


class circular_queue:
    def __init__(self, size: int):
        self.size = size
        self.queue = [None] * size
        self.head = 0
        self.tail = 0
        self.count = 0

    def is_full(self) -> bool:
        return self.count == self.size

    def is_empty(self) -> bool:
        return self.count == 0
    
    def at(self, index: int) -> Any:
        if index < 0 or index >= self.count:
            raise Exception("Index out of bounds")
        return self.queue[index]
    
    def enqueue(self, item: Any) -> bool:
        if self.is_full():
            return False
        self.queue[self.tail] = item
        self.tail = (self.tail + 1) % self.size
        self.count += 1
        return True

    def dequeue_front(self) -> Any:
        if self.is_empty():
            raise Exception("Queue is empty")
        item = self.queue[self.head]
        self.queue[self.head] = None
        self.head = (self.head + 1) % self.size
        self.count -= 1
        return item
    
    def dequeue_back(self) -> Any:
        if self.is_empty():
            raise Exception("Queue is empty")
        self.tail = (self.tail - 1 + self.size) % self.size
        item = self.queue[self.tail]
        self.queue[self.tail] = None
        self.count -= 1
        return item
    
    def peek_front(self) -> Any:
        if self.is_empty():
            raise Exception("Queue is empty")
        return self.queue[self.head]
    
    def peek_back(self) -> Any:
        if self.is_empty():
            raise Exception("Queue is empty")
        return self.queue[(self.tail - 1 + self.size) % self.size]
    
    def flush(self) -> None:
        self.queue = [None] * self.size
        self.head = 0
        self.tail = 0
        self.count = 0

    def traverse(self) -> List[Any]:
        items = []
        idx = self.head
        for _ in range(self.count):
            items.append(self.queue[idx])
            idx = (idx + 1) % self.size
        return items


class ROB_Entry:
    def __init__(self, type: str, dest: int, instr_id: int = None):
        self.name = type # e.g., 'LOAD', 'STORE', 'ADD', ...
        self.dest = dest
        self.ready = False
        self.value = None
        self.instr_id = instr_id  # Store instruction ID for commit timing

    def update(self, value: Optional[int]) -> None:
        """
        Mark the ROB entry as ready with the computed value

        args:
            value: computed result value
        """
        self.ready = True
        self.value = value
    

class ReorderBuffer:
    def __init__(self, max_size: int = 8):
        self.max_size = max_size
        self.buffer = circular_queue(max_size)

    def is_full(self) -> bool:
        """
        Check if the ROB is full.

        returns:
            True if ROB is full, False otherwise
        """
        return self.buffer.is_full()
    
    def push(self, type: str, dest: int, instr_id: int = None) -> bool:
        """
        Add a new ROB entry
        args:
            type: type of instruction (e.g., 'LOAD', 'STORE', 'ALU', 'CALL', 'BEQ')
            dest: destination register or memory address
            instr_id: instruction ID for commit timing tracking

        returns:
            True if successfully added, False if ROB is full
        """
        entry = ROB_Entry(type, dest, instr_id)
        success = self.buffer.enqueue(entry)
        return success
    
    def update(self, index: int, value: Optional[int]) -> None:
        """
        Mark the ROB entry at index as ready with the computed value
        args:
            index: index of the ROB entry (actual circular buffer index)
            value: computed result value
        """
        # Check if index is valid before accessing
        if 0 <= index < self.max_size and self.buffer.count > 0:
            try:
                # Find the entry by traversing and matching the actual index
                entries = self.buffer.traverse()
                for i, entry in enumerate(entries):
                    if entry is not None:
                        actual_index = (self.buffer.head + i) % self.max_size
                        if actual_index == index:
                            entry.update(value)
                            return
            except Exception:
                # Entry may have been committed, ignore
                pass

    def pop_front(self) -> ROB_Entry:
        """
        Remove the oldest ROB entry
        
        returns:
            the popped ROB entry
        """
        return self.buffer.dequeue_front()
    
    def pop_back(self) -> ROB_Entry:
        """
        Remove the newest ROB entry
        
        returns:
            the popped ROB entry
        """
        return self.buffer.dequeue_back()
    
    def peek_front(self) -> ROB_Entry:
        """
        Get the oldest ROB entry without removing it
        
        returns:
            the oldest ROB entry
        """
        return self.buffer.peek_front()
    
    def peek_back(self) -> ROB_Entry:
        """
        Get the newest ROB entry without removing it
        
        returns:
            the newest ROB entry
        """
        return self.buffer.peek_back()
    
    def flush_tail(self, index: int) -> Tuple[List[int], List[int], List[Optional[int]]]:
        """
        Flush the ROB from tail up to (but not including) the given index
        
        args:
            index: ROB index to flush up to (this entry is kept)
            
        returns:
            tuple of (list of flushed ROB indices, list of destination registers, list of instruction IDs)
        """
        rob_indices = []
        dest_regs = []
        instr_ids = []
        # Check if queue is empty before flushing
        if self.buffer.count == 0:
            return rob_indices, dest_regs, instr_ids
        
        # Calculate the actual tail index in the circular buffer
        actual_tail_index = (self.buffer.tail - 1 + self.max_size) % self.max_size
        
        # Flush entries from tail backwards until we reach the target index
        while actual_tail_index != index and self.buffer.count > 0:
            entry = self.peek_back()
            if entry is None:
                break
            
            # Get the actual index before popping
            current_index = (self.buffer.tail - 1 + self.max_size) % self.max_size
            print(f"Flushing ROB entry at index {current_index} with dest R{entry.dest if entry.dest is not None else 'None'}")
            rob_indices.append(current_index)
            dest_regs.append(entry.dest)
            instr_ids.append(entry.instr_id)
            self.pop_back()
            
            # Update actual_tail_index after popping
            if self.buffer.count > 0:
                actual_tail_index = (self.buffer.tail - 1 + self.max_size) % self.max_size
            else:
                break
                
        return rob_indices, dest_regs, instr_ids
    
    def find(self, dest: int) -> Tuple[Optional[ROB_Entry], int]: 
        """
        Find a register in the ROB by destination register

        args:
            dest: destination register to find

        returns:
            tuple of (ROB_Entry, actual_rob_index) if found, or (None, -1) if not found
        """
        for i, entry in enumerate(self.buffer.traverse()):
            if entry is not None and entry.dest == dest:
                # Calculate actual ROB index (head + relative position)
                actual_index = (self.buffer.head + i) % self.max_size
                return entry, actual_index
        return None, -1
    
    def print(self) -> None:
        """
        Print the current ROB entries (for debugging purposes)
        """
        print("\n" + "="*90)
        print("  REORDER BUFFER (ROB)")
        print("="*90)
        print(f"  Head: {self.buffer.head} | Tail: {self.buffer.tail} | Count: {self.buffer.count}/{self.max_size}")
        print("="*90)
        print(f"{'Index':<8} {'Type':<12} {'Dest':<8} {'Status':<12} {'Value':<20} {'Position'}")
        print("-"*90)
        
        entries = self.buffer.traverse()
        for i, entry in enumerate(entries):
            if entry is not None:
                actual_index = (self.buffer.head + i) % self.max_size
                status = "✓ Ready" if entry.ready else "⏳ Not Ready"
                value_str = str(entry.value) if entry.value is not None else "None"
                
                # Determine position
                if i == 0:
                    position = "← HEAD"
                elif i == len(entries) - 1:
                    position = "← TAIL"
                else:
                    position = ""
                
                dest_str = f"R{entry.dest}" if isinstance(entry.dest, int) else str(entry.dest)
                print(f"{actual_index:<8} {entry.name:<12} {dest_str:<8} {status:<12} {value_str:<20} {position}")
        
        if self.buffer.is_empty():
            print("  (Empty)")
        
        print("="*90 + "\n")