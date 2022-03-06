import uuid
import random
import numpy as np
from .rule import Rule
from .agent import Agent
from .team import Team
from .learner import Learner


class Trainer:

    def __init__(self, gap, numLearners, numAgents, alpha, discount, epsilon):
        self.learnerPopulationSize = 20
        self.learnerPopulation = []
        self.agents = []
        self.rules = []
        self.gap = gap  # percentage of teams we'll select to evolve
        self.numLearners = numLearners
        self.numAgents = numAgents
        self.alpha = alpha
        self.discount = discount
        self.epsilon = epsilon

    def createInitAgents(self) -> None:
        self.generateLearnerPopulation()
        print(len(self.learnerPopulation))
        for i in range(self.numAgents):
            team = Team(uuid.uuid4(), self.numLearners, self.alpha, self.discount, self.epsilon)
            # team.createInitLearners()
            team.sampleLearners(self.learnerPopulation)
            team.createInitQTable()
            agent = Agent(uuid.uuid4(), team)
            self.agents.append(agent)
        print('start!')
        for rule in self.rules:
            # print(rule.id)
            print(rule.region)
        print('end!')

    def generateLearnerPopulation(self) -> None:
        # for i in range(self.learnerPopulationSize):
        #     # give the learner a rule
        #     rule = self.rules[random.randint(0, len(self.rules) - 1)]
        #     # print(rule.region)
        #     learner = Learner(uuid.uuid4(), rule)
        #     self.learnerPopulation.append(learner)
        print((len(self.rules)))
        for i in range(len(self.rules)):
            # give the learner a rule
            rule = self.rules[i]
            # print(rule.region)
            learner = Learner(uuid.uuid4(), rule)
            self.learnerPopulation.append(learner)

    # search
    def generateRules(self, search_space) -> None:
        # init vars
        rules, region = [], [0, 0, 0, 0]
        # init prev_rule, set it all to 0 so nothing gets accidentally hit... but should test this
        prev_rule = Rule(-1, [1, -1, -1, -1], (-1, -1))
        prev_action = 0
        prev_opposite = 0
        # init action selection
        action, prev_action, opposite = random.randint(0, 3), 0, 0
        if action == 0:
            opposite = 1
        elif action == 2:
            opposite = 3
        elif action == 3:
            opposite = 2
        hard_code_count = 0
        action = 2  # remove!
        opposite = 3
        # find "locked coord"
        # if it is going north or south (0, 1), the "locked" coord is x, so 0
        # else, it will be x, as the x won't change with east or west
        region[0] = 0
        if action == 0 or action == 1:
            region[0] = 1

        state, reward, terminate = search_space.step(action)
        index = 0
        while not terminate:
            # print(state)
            # print(action)
            # print(reward)
            # print(region)
            # print(prev_rule.id)
            # print(prev_rule.region)
            if index != 0:
                state, reward, terminate = search_space.step(action)
            index += 1
            if reward > 0:
                # prune any overlap, by removing the contested cell from the prev
                # check if there is overlap. If there is, erase it from the prev
                if region[0] == 0:
                    lower, upper = (region[1], region[2]), (region[1], region[3])
                    prev_lower, prev_upper = (prev_rule.region[2], prev_rule.region[1]), (prev_rule.region[3], prev_rule.region[1])
                    if prev_lower == lower or prev_lower == upper:
                        prev_rule.region[2] = prev_rule.region[2] + 1
                    elif prev_upper == lower or prev_upper == upper:
                        prev_rule.region[3] = prev_rule.region[3] - 1

                if region[0] == 1:
                    lower, upper = (region[2], region[1]), (region[3], region[1])
                    prev_lower, prev_upper = (prev_rule.region[1], prev_rule.region[2]), (prev_rule.region[1], prev_rule.region[3])
                    if prev_lower == lower or prev_lower == upper:
                        prev_rule.region[2] = prev_rule.region[2] + 1
                    elif prev_upper == lower or prev_upper == upper:
                        prev_rule.region[3] = prev_rule.region[3] - 1

                # rule update
                # the constant axis is the x or y which the searcher successfully starts moving
                region[1] = search_space.current_state[region[0]]
                # check if the new step is setting an upper or lower bound
                # if not, it must be upper bound
                if search_space.current_state[not region[0]] < region[2]:
                    # region[3] = region[2] # bug here, we don't always want this to happen....
                    region[2] = search_space.current_state[not region[0]]
                else:
                    region[3] = search_space.current_state[not region[0]]
            else:
                # if the team is within the region of the previous rule, we need to backtrack (and not set a region)
                if (search_space.current_state[prev_rule.region[0]] == prev_rule.region[1]) and (
                        search_space.current_state[not prev_rule.region[0]] >= prev_rule.region[2] or
                        search_space.current_state[not prev_rule.region[0]] <= prev_rule.region[3]):
                    # print('reward was negative, in bounds of previous learner')
                    # if the state where backtracking is required is the lower bound
                    if search_space.current_state[not prev_rule.region[0]] == prev_rule.region[2]:
                        # backtrack the region bound, we add here as it is always a lower bound
                        if prev_rule.region[2] < 4:
                            prev_rule.region[2] = prev_rule.region[2] + 1
                        # correct the position of the agent, tuples are immutable...
                        if prev_rule.region[0] == 1:
                            # search_space.current_state = (search_space.current_state[1], prev_rule.region[2])
                            new_state = (prev_rule.region[2], search_space.current_state[1])
                            if (new_state != (2, 0)) and (new_state != (2, 1)) and (new_state != (3, 1)) and (
                                    new_state != (1, 3)) and (new_state != (2, 3)) and (new_state != (3, 3)) and (
                                    new_state != (1, 4)):
                                search_space.current_state = new_state
                            # search_space.current_state = (prev_rule.region[2], search_space.current_state[1])
                        else:
                            # search_space.current_state = (prev_rule.region[2], search_space.current_state[0])
                            new_state = (search_space.current_state[0], prev_rule.region[2])
                            if (new_state != (2, 0)) and (new_state != (2, 1)) and (new_state != (3, 1)) and (
                                    new_state != (1, 3)) and (new_state != (2, 3)) and (new_state != (3, 3)) and (
                                    new_state != (1, 4)):
                                search_space.current_state = new_state
                            # search_space.current_state = (search_space.current_state[0], prev_rule.region[2])
                    # OR the backtracking is at the upper bound (region[3])
                    # coord that we're not keeping constant must equal the upper bound
                    else:
                        # backtrack the region bound, we subtract here as it is always an upper bound
                        if prev_rule.region[3] > 0:
                            prev_rule.region[3] = prev_rule.region[3] - 1
                        # correct the position of the agent, tuples are immutable...
                        if prev_rule.region[0] == 1:
                            # search_space.current_state = (search_space.current_state[1], prev_rule.region[3])
                            # soon, this will be replaced by just having the searcher step into the env
                            # that way, we don't have to call these checks...
                            new_state = (prev_rule.region[3], search_space.current_state[1])
                            if (new_state != (2, 0)) and (new_state != (2, 1)) and (new_state != (3, 1)) and (
                                    new_state != (1, 3)) and (new_state != (2, 3)) and (new_state != (3, 3)) and (
                                    new_state != (1, 4)):
                                search_space.current_state = new_state
                            # search_space.current_state = (prev_rule.region[3], search_space.current_state[1])
                            # print('curr: ' + str(search_space.current_state))
                        else:
                            # search_space.current_state = (prev_rule.region[3], search_space.current_state[0])
                            new_state = (search_space.current_state[0], prev_rule.region[3])
                            if (new_state != (2, 0)) and (new_state != (2, 1)) and (new_state != (3, 1)) and (
                                    new_state != (1, 3)) and (new_state != (2, 3)) and (new_state != (3, 3)) and (
                                    new_state != (1, 4)):
                                search_space.current_state = new_state
                            # search_space.current_state = (search_space.current_state[0], prev_rule.region[3])
                            # print('curr: ' + str(search_space.current_state))
                    # simulate
                    state, reward, terminate = search_space.step(action)
                else:
                    # if the agent is out of the region of the previous rule, we are done with it and can save it
                    prev_action = action
                    prev_opposite = opposite
                    action_set = (prev_action, prev_opposite)
                    prev_rule = Rule(uuid.uuid4(), region, action_set)
                    self.rules.append(prev_rule)
                    # region = [0, 0, 10, 0]
                    region = [0, 0, 0, 0]
                    if action == 0 or action == 1:
                        action = random.randint(2, 3)
                        region[0] = 0  # 0 is y
                        region[1] = search_space.current_state[0]
                        region[2] = search_space.current_state[1]
                        region[3] = search_space.current_state[1]
                        # region[1] = prev_rule.region[1]
                    else:
                        action = random.randint(0, 1)
                        region[0] = 1  # 1 is x
                        region[1] = search_space.current_state[1]
                        region[2] = search_space.current_state[0]
                        region[3] = search_space.current_state[0]
                        # region[1] = prev_rule.region[1]
                    hard_code_count += 1
                    if hard_code_count == 1:
                        action = 0
                        opposite = 1
                    elif hard_code_count == 2:
                        action = 2
                        opposite = 3
                    elif hard_code_count == 3:
                        action = 1
                        opposite = 0
            # print('\n\n')
        action_set = (action, opposite)
        prev_rule = Rule(uuid.uuid4(), region, action_set)
        self.rules.append(prev_rule)
        search_space.reset()
        for i in range(len(self.rules)):
            print(self.rules[i].id)
            print(self.rules[i].region)
            print(self.rules[i].action_set)
        # for rule in self.rules:
        #     print(rule.id)
        #     print(rule.region)

    def evolve(self) -> None:
        self.generate(self.select())

    def select(self):
        # thank you Ryan...
        rankedAgents = sorted(self.agents, key=lambda ag: ag.fitness, reverse=True)
        numKeep = len(self.agents) - int(len(self.agents) * self.gap)

        # wheel = rankedAgents[numKeep:]
        wheel = rankedAgents[:numKeep]  # verify which is right...
        return wheel

    # perform roulette wheel, not really a wheel for now...
    def generate(self, wheel):
        children = []

        while (len(wheel) + len(children)) < int(self.numAgents):
            parent = random.choice(wheel)
            child = Agent(uuid.uuid4(), parent.team)
            # child.team.mutate...
            children.append(child)

        # replace old population with new
        wheel.extend(children)
        self.agents = wheel
