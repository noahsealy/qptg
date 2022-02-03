from .program import Program
import uuid


class Learner:
    def __init__(self, id):
        self.id = id
        # self.action = action
        self.program = Program(uuid.uuid4(), 5)

    def bid(self, state):
        return self.program.execute(state)
