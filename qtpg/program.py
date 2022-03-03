# import random
from .rule import Rule


class Program:

    def __init__(self, id, rule: Rule):
        self.id = id
        self.rule = rule

    def execute(self, state):
        # if state is within program's rule region, bid high
        # if state[self.rule.region[0]] == self.rule.region[1] and \
        #         ((state[not self.rule.region[0]] >= self.rule.region[2]) or
        #          (state[not self.rule.region[0]] <= self.rule.region[3])):
        if state[self.rule.region[0]] == self.rule.region[1] and \
                self.rule.region[2] <= state[not self.rule.region[0]] <= self.rule.region[3]:
            return 10
        return -10

    # def __init__(self, id, state_size):
    #     self.id = id
    #     self.state_size = state_size
    #     self.regs = [0, 0]
    #     self.i = random.randint(0, 1)
    #     self.in1_op = random.randint(0, 2)
    #     self.in1_const = random.randint(0, self.state_size-1)
    #     self.in2_op = random.randint(0, 2)
    #     self.in2_const = random.randint(0, self.state_size-1)
    #     self.in3_op = random.randint(0, 1)
    #
    # def reroll(self):
    #     self.i = random.randint(0, 1)
    #     self.in1_op = random.randint(0, 2)
    #     self.in1_const = random.randint(0, self.state_size-1)
    #     self.in2_op = random.randint(0, 2)
    #     self.in2_const = random.randint(0, self.state_size-1)
    #     self.in3_op = random.randint(0, 1)
    #
    # def display(self):
    #     print('hey!')
    #     print(f'i: {self.i}')
    #     print(f'in1_op: {self.in1_op}')
    #     print(f'in1_const: {self.in1_const}')
    #     print(f'in2_op: {self.in2_op}')
    #     print(f'in2_const: {self.in2_const}')
    #     print(f'in3_op: {self.in3_op}')
    #
    # def execute(self, state):
    #     self.regs = [0, 0]  # zero the registers...
    #
    #     # first instruction
    #     a = state[0]  # make first instruction always for X
    #     if self.in1_op == 0:
    #         self.regs[self.i] = a < self.in1_const
    #     elif self.in1_op == 1:
    #         self.regs[self.i] = a == self.in1_const
    #     elif self.in1_op == 2:
    #         self.regs[self.i] = a > self.in1_const
    #
    #     # second instruction
    #     flipped_i = 0
    #     if self.i == 0:
    #         flipped_i = 1
    #     a = state[1]  # make second instruction always for Y
    #     if self.in2_op == 0:
    #         self.regs[flipped_i] = a < self.in2_const
    #     elif self.in2_op == 1:
    #         self.regs[flipped_i] = a == self.in2_const
    #     elif self.in2_op == 2:
    #         self.regs[flipped_i] = a > self.in2_const
    #
    #     # third instruction
    #     if self.in3_op == 0:
    #         self.regs[0] = self.regs[0] and self.regs[1]
    #     elif self.in3_op == 1:
    #         self.regs[0] = self.regs[0] or self.regs[1]
    #
    #     # fourth instruction
    #     if self.regs[0] > 0:
    #         return 10
    #     else:
    #         return -10
