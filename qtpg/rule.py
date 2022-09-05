import random


class Rule:
    def __init__(self, id, region, action_set, fitness):
        self.id = id
        self.region_qs = 0
        self.region = region
        self.action_set = action_set
        self.value_set = [0, 0]
        self.fitness = fitness

    #     for region.step
        self.win = None


    #
    # def region(self):
    #     return self.region

    def e_greedy(self):
        if self.value_set == [0, 0]:
            selected_action = self.action_set[random.randint(0, 1)]
            # print(f'value set is 0, action selected --> {selected_action}')
        else:
            e_prob = random.uniform(0, 1)
            if e_prob < 0.1:
                selected_action = self.action_set[random.randint(0, len(self.action_set) - 1)]
            else:
                top_value = 0
                top_index = 0
                for i in range(len(self.value_set)):
                    if self.value_set[i] > top_value:
                        top_value = self.value_set[i]
                        top_index = i
                selected_action = self.action_set[top_index]
        return selected_action

    def step(self, action, current_state, illegal_states, dimensions):
        # north
        if action == 0:
            next = (current_state[0] + 1, current_state[1])
        # south
        elif action == 1:
            next = (current_state[0] - 1, current_state[1])
        # east
        elif action == 2:
            next = (current_state[0], current_state[1] + 1)
        # west
        else:
            next = (current_state[0], current_state[1] - 1)

        if -1 < next[0] < dimensions[0] and -1 < next[1] < dimensions[1] and next not in illegal_states:
            current_state = next

        # transition = False
        # if not self.within_region(next):
        #     transition = False

        win = False
        if self.win and self.win == current_state:
            win = True

        # return self.current_state, transition, win
        return current_state, win

    # def within_region(self, state):
    #     if state[self.region[0]] == self.region[1] and self.region[2] <= state[not self.region[0]] <= self.region[3]:
    #         return True
    #     return False
