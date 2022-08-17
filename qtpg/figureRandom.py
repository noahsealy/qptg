import random
import uuid
import csv

# will use Downing fig 13 for testing on this
class FigureRandom:
    def __init__(self, rows, cols, memory_size,
                 legal_move, illegal_move, out_of_bounds, memory_repeat, goal_reached):
        self.memory = []
        self.memory_position = 0
        self.memory_limit = memory_size  # 20
        self.rows = rows
        self.cols = cols
        self.start_state = (0, 0)
        self.win_state = (0, 0)
        self.current_state = self.start_state
        self.legal_move = legal_move
        self.illegal_move = illegal_move
        self.out_of_bounds = out_of_bounds
        self.memory_repeat = memory_repeat
        self.goal_reached = goal_reached
        self.illegal_states = []

    def shake(self, percent_cells_flipped):
        self.start_state = (random.randint(0, self.rows-1), random.randint(0, self.cols-1))
        self.win_state = self.start_state
        while self.start_state == self.win_state:
            self.win_state = (random.randint(0, self.rows-1), random.randint(0, self.cols-1))
        states = []
        for i in range(self.rows):
            for q in range(self.cols):
                states.append((i, q))

        for i in range(round(percent_cells_flipped * (self.rows * self.cols))):
            new_sample = 0
            while new_sample == 0:
                sample_state = (random.randint(0, self.rows-1), random.randint(0, self.cols-1))
                if sample_state not in self.illegal_states and sample_state != self.start_state and sample_state != self.win_state:
                    new_sample = 1
                    self.illegal_states.append(sample_state)

        self.display()

        # # display
        # for n in reversed(range(self.rows)):
        #     for m in range(self.cols):
        #         if (n, m) == self.start_state:
        #             action = 'S'
        #         elif (n, m) == self.win_state:
        #             action = 'W'
        #         elif (n, m) in self.illegal_states:
        #             action = 'X'
        #         else:
        #             action = '_'
        #         print(f'{action} ', end='')
        #     print('\n')

    def save(self):
        print('Saving env...')
        env_id = uuid.uuid4()
        # fields = ['id', 'row_size', 'column_size', 'start_state', 'win_state', 'illegal_states']
        row = [env_id, self.rows, self.cols, self.start_state, self.win_state, self.illegal_states]

        file_name = f'qtpg/saved_environments/{env_id}.csv'
        with open(file_name, 'w') as csv_file:
            csv_writer = csv.writer(csv_file)
            # csv_writer.writerow(fields)
            csv_writer.writerow(row)

        print('Env saved successfully!')
        print(env_id)

    def load(self, id):
        print('Loading env...')
        file_name = f'qtpg/saved_environments/{id}.csv'
        with open(file_name, 'r') as csv_file:
            env = csv.reader(csv_file)

            for row in env:
                self.rows = int(row[1])
                self.cols = int(row[2])
                self.start_state = eval(row[3])
                self.win_state = eval(row[4])
                self.illegal_states = eval(row[5])

        print('Env loaded successfully!')
        self.display()

    def display(self):
        print(f'Rows: {self.rows}')
        print(f'Columns: {self.cols}')
        print(f'Start State: {self.start_state}')
        print(f'Win State: {self.win_state}')
        print(f'Illegal States: {self.illegal_states}')

        print('matlab code, converted so plus one to everything')
        print(f'GW.CurrentState = \'[{(self.rows-1)-self.start_state[0]+1},{self.start_state[1]+1}]\';')
        print(f'GW.TerminalStates = \'[{(self.rows-1)-self.win_state[0]+1},{self.win_state[1]+1}]\';')
        print('GW.ObstacleStates = [', end='')
        for illegal in self.illegal_states:
            print(f'\"[{(self.rows-1)-illegal[0]+1},{illegal[1]+1}]\";', end='')
        print('];')

        print(self.win_state)
        for n in reversed(range(self.rows)):
            for m in range(self.cols):
                if (n, m) == self.start_state:
                    action = 'S'
                elif (n, m) == self.win_state:
                    action = 'W'
                elif (n, m) in self.illegal_states:
                    action = 'X'
                else:
                    action = '_'
                print(f'{action} ', end='')
            print('\n')

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
        if state not in self.illegal_states:
        # if (state != (2, 0)) and (state != (2, 1)) and (state != (3, 1)) and (
        #         state != (1, 3)) and (state != (2, 3)) and (state != (3, 3)) and (
        #         state != (1, 4)):
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
            if next in self.illegal_states:
            # if (next == (2, 0)) or (next == (2, 1)) or (next == (3, 1)) or (next == (1, 3)) or (next == (2, 3)) or (
            #         next == (3, 3)) or (next == (1, 4)):
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
