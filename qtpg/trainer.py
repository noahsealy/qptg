import uuid
import random
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
        for i in range(self.numAgents):
            team = Team(uuid.uuid4(), self.numLearners, self.alpha, self.discount, self.epsilon)
            team.createInitLearners()
            # team.sampleLearners(self.learnerPopulation)
            team.createInitQTable()
            agent = Agent(uuid.uuid4(), team)
            self.agents.append(agent)

    def generateLearnerPopulation(self) -> None:
        for i in range(self.learnerPopulationSize):
            # give the learner a rule
            rule = self.rules[random.randint(0, len(self.rules))]
            learner = Learner(uuid.uuid4(), rule)
            self.learnerPopulation.append(learner)

    # search
    def generateRules(self, search_space) -> None:
        # init vars
        rules, prev_rule, region = [], [], []

        # init action selection
        action, prev_action, opposite = random.randint(0, 3), 0, 0
        if action == 0:
            opposite = 1
        elif action == 2:
            opposite = 3
        elif action == 3:
            opposite = 2

        # find "locked coord"
        # if it is going north or south (0, 1), the "locked" coord is x, so 0
        # else, it will be x, as the x won't change with east or west
        region[0] = 1
        if action == 0 or action == 1:
            region[0] = 0

        state, reward, terminate = search_space.step(action)
        while not terminate:
            if reward > 0:
                # simulate
                search_space.step(action)
                # rule update
                # check if the new step is setting an upper or lower bound
                # if not, it must be upper bound
                if state[not region[0]] < region[2]:
                    region[3] = region[2]
                    region[2] = state[not region[0]]
                else:
                    region[3] = state[not region[0]]
            else:
                # if the team is within the region of the previous rule, we need to backtrack (and not set a region)
                if (search_space.current_state[prev_rule.region[0]] == prev_rule.region[1]) and (
                        search_space.current_state[not prev_rule.region[0]] < prev_rule.region[2] or search_space.current_state[not prev_rule.region[0]] > prev_rule.region[3]):
                    # if the state where backtracking is required is the lower bound
                    if search_space.current_state[not prev_rule.region[0]] == prev_rule.region[2]:
                        # backtrack the region bound, we add here as it is always a lower bound
                        prev_rule.region[2] = prev_rule.region[2] + 1
                        # correct the position of the agent
                        search_space.current_state[not prev_rule.region[0]] = prev_rule.region[2]
                    # OR the backtracking is at the upper bound (region[3])
                    else:
                        # backtrack the region bound, we subtract here as it is always an upper bound
                        prev_rule.region[3] = prev_rule.region[3] - 1
                        # correct the position of the agent
                        search_space.current_state[not prev_rule.region[0]] = prev_rule.region[3]
                else:
                    # if the agent is out of the region of the previous rule, we are done with it and can save it
                    self.rules.append(prev_rule)
                    if action == 0 or action == 1:
                        action = random.randint(2, 3)
                    else:
                        action = random.randint(0, 1)
                    prev_rule = Rule(uuid.uuid4(), region)
                    region = []
        search_space.reset()

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
