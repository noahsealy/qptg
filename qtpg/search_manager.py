class SearchManager:

    def __init__(self, maxTeamPoolSize):
        self.maxTeamPoolSize = maxTeamPoolSize
        self.teamPool = []
        self.winners = []

    def evaluate_team(self, child):
        # put this on agent... or team, or trainer...?
        for team in self.teamPool:
            if len(self.teamPool) == self.maxTeamPoolSize:
                lowest_fitness = 10000
                lowest_index = 0
                for i in range(len(self.teamPool)):
                    # find lowest fitness out of rule pool
                    if self.teamPool[i].fitness < lowest_fitness:
                        lowest_fitness = self.teamPool[i].fitness
                        lowest_index = i
                # see if offspring beats out the lowest fitness
                if team.fitness > lowest_fitness:
                    self.teamPool[lowest_index] = team
            else:
                self.teamPool.append(child)

    def start_state(self, child):
        if child.action == 0:
            start_state = [0, 0]
            start_state[child.latest_rule.region[0]] = child.latest_rule.region[1]
            start_state[not child.latest_rule.region[0]] = child.latest_rule.region[3] + 1
            return (start_state[0], start_state[1])


    def win(self, child):
        self.winners.append(child)
