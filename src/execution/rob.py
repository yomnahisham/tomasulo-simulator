"""Reorder Buffer class with ROB entry management."""

from typing import Any


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
    
    def enqueue(self, item: Any) -> None:
        if self.is_full():
            raise Exception("Queue is full")
        self.queue[self.tail] = item
        self.tail = (self.tail + 1) % self.size
        self.count += 1

    def dequeue(self) -> Any:
        if self.is_empty():
            raise Exception("Queue is empty")
        item = self.queue[self.head]
        self.queue[self.head] = None
        self.head = (self.head + 1) % self.size
        self.count -= 1
        return item


class ROB_Entry:
    def __init__(self, type: str, dest: int):
        self.type = type # e.g., 'LOAD', 'STORE', 'ALU', 'CALL', 'BEQ'
        self.dest = dest
        self.ready = False
        self.value = None

    def update(self, value: int) -> None:
        """
        Mark the ROB entry as ready with the computed value

        args:
            value: computed result value
        """
        self.ready = True
        self.value = value
    

class ReorderBuffer:
    def __init__(self, size: int = 8):
        self.buffer = circular_queue(size)

    def is_full(self) -> bool:
        """
        Check if the ROB is full.

        returns:
            True if ROB is full, False otherwise
        """
        return self.buffer.is_full()
    
    def push(self, type: str, dest: int) -> None:
        """
        Add a new ROB entry
        args:
            type: type of instruction (e.g., 'LOAD', 'STORE', 'ALU', 'CALL', 'BEQ')
            dest: destination register or memory address
        """
        entry = ROB_Entry(type, dest)
        self.buffer.enqueue(entry)
    
    def update(self, index: int, value: int) -> None:
        """
        Mark the ROB entry at index as ready with the computed value
        args:
            index: index of the ROB entry
            value: computed result value
        """
        self.buffer.at(index).update(value)

    def pop(self) -> ROB_Entry:
        """
        Remove the oldest ROB entry
        
        returns:
            the popped ROB entry
        """
        return self.buffer.dequeue()