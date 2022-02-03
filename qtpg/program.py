import random


class Program:

    def __init__(self, id, state_size):
        self.id = id
        self.state_size = state_size
        self.regs = [0, 0]

    def execute(self, state):
        # first instruction
        i = random.randint(0, 1)
        # a = state[random.randint(0, 1)]
        a = state[0] # make first instruction always for X
        first_op = random.randint(0, 2)
        const = random.randint(0, self.state_size)

        if first_op == 0:
            self.regs[i] = a < const
        elif first_op == 1:
            self.regs[i] = a == const
        elif first_op == 2:
            self.regs[i] = a > const

        # second instruction

        if i == 0:
            i = 1
        else:
            i = 0
        # a = state[random.randint(0, 1)]
        a = state[1] # make second instruction always for Y
        first_op = random.randint(0, 2)
        const = random.randint(0, self.state_size)

        if first_op == 0:
            self.regs[i] = a < const
        elif first_op == 1:
            self.regs[i] = a == const
        elif first_op == 2:
            self.regs[i] = a > const

        # third instruction
        second_op = random.randint(0, 1)
        if second_op == 0:
            self.regs[0] = self.regs[0] and self.regs[1]
        elif second_op == 1:
            self.regs[0] = self.regs[0] or self.regs[1]

        # fourth instruction
        if self.regs[0] > 0:
            return 10
        else:
            return -10
