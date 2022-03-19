import random
import uuid

from .learner import Learner
from .rule import Rule


class Team:
    def __init__(self, id, numLearners, max_rules, alpha, discount, epsilon):
        self.id = id
        self.learners = []
        self.q_table = []
        self.numLearners = numLearners
        self.alpha = alpha
        self.discount = discount
        self.epsilon = epsilon
        self.rule_pool = []  # holds a Rule and a fitness associated with the rule
        self.rule_pool.append(Rule(-1, [0, 0, 0, 0], 0, 0))
        self.max_rules = max_rules

    def createInitLearners(self):
        for i in range(self.numLearners):
            learner = Learner(uuid.uuid4())
            self.learners.append(learner)

    def sampleLearners(self, learners):
        for i in range(self.numLearners):
            sample = random.randint(0, len(learners) - 1)
            # sample = i
            self.learners.append(learners[sample])

    # create q table, assign random actions
    def createInitQTable(self):
        for learner in self.learners:
            # old action selection
            # action = random.randint(0, 3)
            # opposite = 0
            # if action == 0:
            #     opposite = 1
            # elif action == 2:
            #     opposite = 3
            # elif action == 3:
            #     opposite = 2
            #
            # action_list = [action, opposite]
            # actions = len(action_list)
            action_list = []
            # new action selection, based on region search
            for action in learner.program.rule.action_set:
                action_list.append(action)
            actions = len(action_list)
            for i in range(actions):
                self.q_table.append({'learner': str(learner.id), 'action': action_list[i], 'q': 0})

    # learner bid and action selection
    def evaluate(self, state):
        top_bid = max(self.learners, key=lambda learner: learner.bid(state))
        actions = []
        top_q = -100
        top_action = None
        for entry in self.q_table:
            if entry['learner'] == str(top_bid.id):
                actions.append(entry['action'])
                if entry['q'] > top_q:
                    top_q = entry['q']
                    top_action = entry['action']

        e_prob = random.uniform(0, 1)
        if e_prob < self.epsilon:
            rand_action = random.randint(0, len(actions) - 1)
            action = actions[rand_action]
        else:
            action = top_action
        return top_bid, action

    def update(self, learner, next_learner, action, reward) -> None:
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

    def final_update(self, learner, action, reward) -> None:
        # find the current learner and q update
        for first_learner in self.q_table:
            if first_learner['learner'] == str(learner.id) and first_learner['action'] == action:
                # equation 2 from qtpg pdf
                first_learner['q'] += self.alpha * (reward - first_learner['q'])

    # get the agent to replay a win a few times in order to properly back prop its q values
    def victory_lap(self, env, winning_sequence) -> None:
        for i in range(len(winning_sequence)):
            _, reward, _ = env.step(winning_sequence[i]['action'])
            if i != len(winning_sequence) - 1:
                self.update(winning_sequence[i]['learner'], winning_sequence[i + 1]['learner'],
                            winning_sequence[i]['action'], reward)
            else:
                self.final_update(winning_sequence[i]['learner'], winning_sequence[i]['action'], reward)

    ##############################
    # Region search stuff begins
    ##############################
#hey hey
    def select_rule(self):
        top_fitness = -100
        top_rule = None
        for rule in self.rule_pool:
            if rule.fitness > top_fitness:
                top_fitness = rule.fitness
                top_rule = rule

        e_prob = random.uniform(0, 1)
        if e_prob < 0.1:
            rand_rule = random.randint(0, len(self.rule_pool) - 1)
            top_rule = self.rule_pool[rand_rule]
            # top_fitness = self.rule_pool[rand_rule].fitness

        # return top_rule, top_fitness
        return top_rule

    def search(self, selected_rule, env):
        action = 0
        if selected_rule.action_set == 0 or selected_rule.action_set == 1:
            action = random.randint(2, 3)
        elif selected_rule.action_set == 2 or selected_rule.action_set == 3:
            action = random.randint(0, 1)

        # sample start within the region
        # we use current state instead of the max region because the max gets clipped from orthogonal backtracking
        sample_start = [0, 0]
        sample_start[selected_rule.region[0]] = selected_rule.region[1]  # assign the non-moving space to the non-moving coord
        if selected_rule.region[2] - selected_rule.region[3] == 0:
            sample_start[not selected_rule.region[0]] = selected_rule.region[2]  # in case region is the same
            # ^ this is no longer true when we add curr state to max sampled...
        else:
            # need to make sure the farther region is the larger number in the random
            if selected_rule.region[2] > selected_rule.region[3]:
                sample_start[not selected_rule.region[0]] = random.randint(selected_rule.region[3],
                                                                           selected_rule.region[2]-1)
                # sample_start[not selected_rule.region[0]] = random.randint(selected_rule.region[3],
                #                                                            env.current_state[not selected_rule.region[0]])
            else:
                sample_start[not selected_rule.region[0]] = random.randint(selected_rule.region[2],
                                                                           selected_rule.region[3]+1)
                # sample_start[not selected_rule.region[0]] = random.randint(selected_rule.region[2],
                #                                                            env.current_state[not selected_rule.region[0]])

        env.current_state = (sample_start[0], sample_start[1])

        # init region
        reward = 0
        region = [0, 0, 0, 0]
        if action == 0:
            region[0] = 1
            region[1] = env.current_state[1]
            region[2] = env.current_state[0]
            # region[3] = env.current_state[]
        elif action == 1:
            region[0] = 1
            region[1] = env.current_state[1]
            # region[2] = env.current_state[]
            region[3] = env.current_state[0]
        elif action == 2:
            region[0] = 0
            region[1] = env.current_state[0]
            region[2] = env.current_state[1]
            # region[3] = env.current_state[]
        elif action == 3:
            region[0] = 0
            region[1] = env.current_state[0]
            # region[2] = env.current_state[]
            region[3] = env.current_state[1]

        fitness = 0
        # search region
        terminate = False
        while reward >= 0:

            # track region
            if action == 0:
                region[3] = env.current_state[0]
            elif action == 1:
                region[2] = env.current_state[0]
            elif action == 2:
                region[3] = env.current_state[1]
            elif action == 3:
                region[2] = env.current_state[1]
            fitness += reward

            state, reward, terminate = env.step(action)
            # print(state)
            if terminate:
                print('win!')
                # track region TODO: clean this up
                if action == 0:
                    region[3] = env.current_state[0]
                elif action == 1:
                    region[2] = env.current_state[0]
                elif action == 2:
                    region[3] = env.current_state[1]
                elif action == 3:
                    region[2] = env.current_state[1]
                fitness += reward
                break
            # print(state)

        # backtrack (or front-track?), to leave room for orthogonal
        if not terminate:
            # track region
            if action == 0:
                region[3] -= 1
            elif action == 1:
                region[2] += 1
            elif action == 2:
                region[3] -= 1
            elif action == 3:
                region[2] += 1

        # construct the rule
        rule = Rule(uuid.uuid4(), region, action, fitness)
        print(rule.region)
        print(rule.fitness)
        return rule, terminate

    def evaluate_rule(self, offspring):
        if len(self.rule_pool) >= self.max_rules:
        #     for i in range(len(self.rule_pool)):
        #         if self.rule_pool[i].fitness < offspring.fitness:
        #             self.rule_pool[i] = offspring
        #             break
            lowest_fitness = 10000
            lowest_index = 0
            for i in range(len(self.rule_pool)):
                # find lowest fitness out of rule pool
                if self.rule_pool[i].fitness < lowest_fitness:
                    lowest_fitness = self.rule_pool[i].fitness
                    lowest_index = i
                # see if offspring beats out the lowest fitness
                if offspring.fitness > lowest_fitness:
                    self.rule_pool[lowest_index] = offspring
        else:
            self.rule_pool.append(offspring)

    ##############################
    # Region search stuff ends
    ##############################
