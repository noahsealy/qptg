import uuid
import random
from .agent import Agent
from .team import Team


class Trainer:

    def __init__(self, gap, numLearners, numAgents, alpha, discount, epsilon):
        self.agents = []
        self.gap = gap # percentage of teams we'll select to evolve
        self.numLearners = numLearners
        self.numAgents = numAgents
        self.alpha = alpha
        self.discount = discount
        self.epsilon = epsilon

    def createInitAgents(self) -> None:
        for i in range(self.numAgents):
            team = Team(uuid.uuid4(), self.numLearners, self.alpha, self.discount, self.epsilon)
            team.createInitLearners()
            team.createInitQTable()
            agent = Agent(uuid.uuid4(), team)
            self.agents.append(agent)

    def evolve(self) -> None:
        self.generate(self.select())

    def select(self):
        # thank you Ryan...
        rankedAgents = sorted(self.agents, key=lambda ag: ag.fitness, reverse=True)
        numKeep = len(self.agents) - int(len(self.agents)*self.gap)

        wheel = rankedAgents[numKeep:]
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

