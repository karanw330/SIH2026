class ConversationMemory:
    def __init__(self, max_messages: int = 6):
        self.max_messages = max_messages
        self.history = []

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_messages:
            self.history = self.history[-self.max_messages:]

    def get_history(self):
        return self.history

    def clear(self):
        self.history = []
        