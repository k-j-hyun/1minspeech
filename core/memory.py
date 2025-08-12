from collections import deque

class BufferMemory:
    def __init__(self, max_turns=5):
        self.max_turns = max_turns
        self.history = deque(maxlen=max_turns)
    
    def append(self, user, assistant):
        self.history.append({"user": user, "assistant": assistant})
    
    def get_formatted_history(self):
        if not self.history:
            return ""
        return "\n".join([f"User: {h['user']}\nAssistant: {h['assistant']}" 
                         for h in self.history])
    
    def clear(self):
        self.history.clear()