# will use Downing fig 9 for testing on this
class Figure9:
    def __init__(self, rows, cols, win_state, start_state, memory_size,
                 legal_move, illegal_move, out_of_bounds, memory_repeat, goal_reached):
        self.memory = []
        self.memory_position = 0
        self.memory_limit = memory_size  # 20
        self.rows = rows
        self.cols = cols
        self.start_state = start_state
        self.win_state = win_state
        self.current_state = self.start_state
        self.legal_move = legal_move
        self.illegal_move = illegal_move
        self.out_of_bounds = out_of_bounds
        self.memory_repeat = memory_repeat
        self.goal_reached = goal_reached
        self.illegal_states = [(4, 2), (4, 3), (4, 4), (4, 5), (3, 5), (2, 5), (1, 5), (0, 5), (6, 6), (7, 6), (8, 6), (3, 8), (4, 8), (5, 8), (5, 9)]

    def reset(self):
        self.current_state = self.start_state
        self.memory = []
        self.memory_position = 0
        return self.current_state

    # just reset for now...
    def close(self):
        self.current_state = self.start_state
        return 1

    def check_win(self):
        if self.current_state == self.win_state:
            return True
        return False

    def check_legal(self, state):
        if (state != (4, 2)) and (state != (4, 3)) and (state != (4, 4)) and (state != (4, 5)) and (state != (3, 5)) and \
                (state != (2, 5)) and (state != (1, 5)) and (state != (0, 5)) and (state != (6, 6)) and (state != (7, 6)) and\
                (state != (8, 6)) and (state != (3, 8)) and (state != (4, 8)) and (state != (5, 8)) and (state != (5, 9)):
            return True
        return False

    def step(self, action):
        # north
        if action == 0:
            next = (self.current_state[0] + 1, self.current_state[1])
        # south
        elif action == 1:
            next = (self.current_state[0] - 1, self.current_state[1])
        # east
        elif action == 2:
            next = (self.current_state[0], self.current_state[1] + 1)
        # west
        else:
            next = (self.current_state[0], self.current_state[1] - 1)

        terminate = False
        reward = 0
        # check if move is legal
        if (next[0] >= 0 and next[0] <= (self.rows - 1)) and (next[1] >= 0 and next[1] <= (self.cols - 1)):
            illegal = 0

            if (next == (4, 2)) or (next == (4, 3)) or (next == (4, 4)) or (next == (4, 5)) or (next == (3, 5)) or \
                    (next == (2, 5)) or (next == (1, 5)) or (next == (0, 5)) or (next == (6, 6)) or (next == (7, 6)) or\
                    (next == (8, 6)) or (next == (3, 8)) or (next == (4, 8)) or (next == (5, 8)) or (next == (5, 9)):
                illegal = 1

            if illegal == 0:
                self.current_state = next
                reward += self.legal_move
            else:
                reward += self.illegal_move
        else:
            reward += self.out_of_bounds

        # punish repeat states within last 20 states
        if self.current_state in self.memory:
            reward += self.memory_repeat

        if self.check_win():
            reward += self.goal_reached
            terminate = True

        # add new state to memory
        if len(self.memory) <= self.memory_limit:
            self.memory.append(self.current_state)
        # after memory is full, begin overriding it
        else:
            if self.memory_position < self.memory_limit:
                self.memory[self.memory_position] = self.current_state
                self.memory_position += 1
            else:
                self.memory_position = 0
                self.memory[self.memory_position] = self.current_state

        return self.current_state, reward, terminate
