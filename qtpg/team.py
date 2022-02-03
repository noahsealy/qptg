import random
import uuid
from .learner import Learner


class Team:
    def __init__(self, id, numLearners, alpha, discount, epsilon):
        self.id = id
        self.learners = []
        self.q_table = []
        self.numLeaners = numLearners
        self.alpha = alpha
        self.discount = discount
        self.epsilon = epsilon

    def createInitLearners(self):
        for i in range(self.numLeaners):
            learner = Learner(uuid.uuid4())
            self.learners.append(learner)

    # create q table, assign random actions
    def createInitQTable(self):
        for learner in self.learners:
            action = random.randint(0, 3)
            opposite = 0
            if action == 0:
                opposite = 1
            elif action == 2:
                opposite = 3
            elif action == 3:
                opposite = 2

            action_list = [action, opposite]
            actions = len(action_list)

            for i in range(actions):
                self.q_table.append({'learner': str(learner.id), 'action': action_list[i], 'q': 0})

    # learner bid and action selection
    def evaluate(self, state):
        top_bid = max(self.learners, key=lambda learner: learner.bid(state))
        actions = []
        top_q = 0
        top_action = None
        for entry in self.q_table:
            if entry['learner'] == str(top_bid.id):
                actions.append(entry['action'])
                if entry['q'] > top_q:
                    top_q = entry['q']
                    top_action = entry['action']

        e_prob = random.uniform(0, 1)
        if e_prob < self.epsilon:
            rand_action = random.randint(0, len(actions)-1)
            action = actions[rand_action]
        else:
            action = top_action
        return top_bid, action

    def update(self, learner, next_learner, action, reward) -> None:
        # print(self.q_table)
        # find the greatest q value out of possible actions for learner t+1
        second_max_q = 0
        for second_learner in self.q_table:
            if second_learner['learner'] == str(next_learner.id):
                if second_learner['q'] > second_max_q:
                    second_max_q = second_learner['q']

        # find the current learner and q update
        for first_learner in self.q_table:
            if first_learner['learner'] == str(learner.id) and first_learner['action'] == action:
                # equation 1 from qtpg pdf
                first_learner['q'] += self.alpha * (reward + (self.discount * second_max_q) - first_learner['q'])
        # print(self.q_table)

    def final_update(self, learner, action, reward) -> None:
        # find the current learner and q update
        for first_learner in self.q_table:
            if first_learner['learner'] == str(learner.id) and first_learner['action'] == action:
                # equation 2 from qtpg pdf
                first_learner['q'] += self.alpha * (reward - first_learner['q'])