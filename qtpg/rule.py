import random


class Rule:
    def __init__(self, id, region, action_set, fitness):
        self.id = id
        self.region_qs = 0
        self.region = region
        self.action_set = action_set
        self.value_set = [0, 0]
        self.fitness = fitness

    def region(self):
        return self.region

    def e_greedy(self):
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
