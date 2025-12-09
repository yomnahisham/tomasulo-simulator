class register:
    def __init__(self):
        self.valid = 0
        self.tag = 0
        self.value = 0

class RAT:
    def __init__(self, size: int = 8):
        self.table = {i: register() for i in range(size)}

    def update(self, index: int, tag: int, value: int):
        entry = self.table[index]
        entry.valid = 1
        entry.tag = tag
        entry.value = value
    
    def get(self, index: int):
        entry = self.table[index]
        if entry.valid:
            return (entry.tag, entry.value)
        else:
            return None
        
    
    
