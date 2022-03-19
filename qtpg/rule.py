class Rule:
    def __init__(self, id, region, action_set, fitness):
        self.id = id
        self.region = region
        self.action_set = action_set
        self.fitness = fitness

    def region(self):
        return self.region
