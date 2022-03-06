class Rule:
    def __init__(self, id, region, action_set):
        self.id = id
        self.region = region
        self.action_set = action_set

    def region(self):
        return self.region
