from .program import Program
import uuid


class Learner:
    def __init__(self, id, rule):
        self.id = id
        # self.action = action
        # self.program = Program(uuid.uuid4(), 5)
        self.program = Program(uuid.uuid4(), rule)

    def bid(self, state):
        # self.program.reroll()
        return self.program.execute(state)
