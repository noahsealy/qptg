import random
import uuid
import copy

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

        #### team competition variables start ####
        self.mostRecent = 0  # TODO this isn't being set anywhere
        self.fitness = 0  # TODO this isn't being set anywhere
        self.start_state = (0, 0)  # TODO this isn't being set anywhere
        #### team competition variables end ####

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

    def search(self, env):
        selected_rule = self.mostRecent.program.rule
        # print('new search:--------------------------------')
        action = 0
        if selected_rule.action_set == 0 or selected_rule.action_set == 1:
            action = random.randint(2, 3)
            # action = 2
        elif selected_rule.action_set == 2 or selected_rule.action_set == 3:
            action = random.randint(0, 1)
        # print(f'parent action :{selected_rule.action_set}')
        # print(f'child action :{action}')
        # sample start within the region
        # we use current state instead of the max region because the max gets clipped from orthogonal backtracking
        sample_start = [0, 0]

        # assign the non-moving space to the non-moving coord
        sample_start[selected_rule.region[0]] = selected_rule.region[1]

        illegal = True
        # reject all illegal cells with this while loop
        # print(f'Selected region: {selected_rule.region}')
        while illegal:
            # north and east start sampling
            if (action == 0 or action == 2) and selected_rule.region[3] < 4:
                # sample_start[not selected_rule.region[0]] = random.randint(selected_rule.region[2],
                #                                                            selected_rule.region[3] + 1)
                sample_start[not selected_rule.region[0]] = selected_rule.region[3] + 1
            # south and west start sampling
            elif (action == 1 or action == 3) and selected_rule.region[2] > 0:
                # sample_start[not selected_rule.region[0]] = random.randint(selected_rule.region[2] - 1,
                #                                                            selected_rule.region[3])
                sample_start[not selected_rule.region[0]] = selected_rule.region[2]-1
            # covers sampling for outskirt cells, as we can not add or subtract from those
            else:
                sample_start[not selected_rule.region[0]] = random.randint(selected_rule.region[2],
                                                                           selected_rule.region[3])

            env.current_state = self.start_state # TODO oop
            # print(sample_start)
            if sample_start != [2, 0] and sample_start != [2, 1] and sample_start != [3, 1] \
                    and sample_start != [1, 3] and sample_start != [2, 3] and sample_start != [3, 3] \
                    and sample_start != [1, 4]:
                illegal = False
            else:
                # action = random.randint(0, 3)
                # known bug, for now just throw out the results...
                print('dud' )
                return False

        # print(f'Sample start: {sample_start}')

        env.current_state = (sample_start[0], sample_start[1])

        env.current_state = self.start_state # TODO will I replace this for the stuff above?... depends if we want sampling or not
        # print(f'Start: {env.current_state}')
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
            # the action is south, so the current state will always be decreasing
            # thus, set the upper region bound to the current state
            # region[2] = env.current_state[0]
            region[3] = env.current_state[0]
        elif action == 2:
            region[0] = 0
            region[1] = env.current_state[0]
            region[2] = env.current_state[1]
            # region[3] = env.current_state[1]
        elif action == 3:
            region[0] = 0
            region[1] = env.current_state[0]
            # the action is west, so the current state will always be decreasing
            # thus, set the upper region bound to the current state
            # region[2] = env.current_state[1]
            region[3] = env.current_state[1]

        fitness = 0
        # search region
        terminate = False
        backTrack = False
        # updated_parent = Rule(uuid.uuid4(), selected_rule.region, selected_rule.action_set, selected_rule.fitness)
        updated_parent = copy.deepcopy(selected_rule)

        # for backtracking, we need to ensure it is out of the zone when it gets a negative reward
        backTrackLimit = 0
        while (reward >= 0 or (reward < 0 and self.in_parent_region(updated_parent.region, env.current_state, action))) \
                and backTrackLimit < 10:
            backTrackLimit += 1
            # while reward >= 0:
            # if the team is within the region of the previous rule, we need to backtrack (and not set a region)
            if reward < 0 and self.in_parent_region(updated_parent.region, env.current_state, action):
                backTrack = True
                backTrackedLowerBound = 0
                backTrackedUpperBound = 0
                # print('backtracked')
                # print(env.current_state)
                # if the state where backtracking is required is the lower bound
                # if env.current_state[not updated_parent.region[0]] == updated_parent.region[2]:
                if action == 1 or action == 3:
                    # backtrack the region bound, we add here as it is always a lower bound
                    if updated_parent.region[2] < 4:
                        backTrackedLowerBound = updated_parent.region[2] + 1
                        # updated_parent.region[2] = updated_parent.region[2] + 1
                    if updated_parent.region[0] == 1:
                        # update the env state
                        # new_state = (updated_parent.region[2], env.current_state[1])
                        new_state = (backTrackedLowerBound, env.current_state[1])
                        # print(f'new state --> {new_state}')
                        if (new_state != (2, 0)) and (new_state != (2, 1)) and (new_state != (3, 1)) and (
                                new_state != (1, 3)) and (new_state != (2, 3)) and (new_state != (3, 3)) and (
                                new_state != (1, 4)):
                            updated_parent.region[2] = backTrackedLowerBound
                            env.current_state = new_state
                            region[1] = env.current_state[0]
                    else:
                        # new_state = (env.current_state[0], updated_parent.region[2])
                        new_state = (env.current_state[0], backTrackedLowerBound)
                        # print(f'new state --> {new_state}')
                        if (new_state != (2, 0)) and (new_state != (2, 1)) and (new_state != (3, 1)) and (
                                new_state != (1, 3)) and (new_state != (2, 3)) and (new_state != (3, 3)) and (
                                new_state != (1, 4)):
                            updated_parent.region[2] = backTrackedLowerBound
                            env.current_state = new_state
                            region[1] = env.current_state[1]

                # coord that we're not keeping constant must equal the upper bound
                else:
                    # backtrack the region bound, we subtract here as it is always an upper bound
                    if updated_parent.region[3] > 0:
                        # updated_parent.region[3] = updated_parent.region[3] - 1
                        backTrackedUpperBound = updated_parent.region[3] - 1
                    # correct the position of the agent, tuples are immutable...
                    if updated_parent.region[0] == 1:
                        # soon, this will be replaced by just having the searcher step into the env
                        # that way, we don't have to call these checks...
                        # new_state = (updated_parent.region[3], env.current_state[1])
                        new_state = (backTrackedUpperBound, env.current_state[1])
                        # print(f'new state --> {new_state}')
                        if (new_state != (2, 0)) and (new_state != (2, 1)) and (new_state != (3, 1)) and (
                                new_state != (1, 3)) and (new_state != (2, 3)) and (new_state != (3, 3)) and (
                                new_state != (1, 4)):
                            updated_parent.region[3] = backTrackedUpperBound
                            env.current_state = new_state
                            region[1] = env.current_state[0]
                    else:
                        # search_space.current_state = (prev_rule.region[3], search_space.current_state[0])
                        # new_state = (env.current_state[0], updated_parent.region[3])
                        new_state = (env.current_state[0], backTrackedUpperBound)
                        # print(f'new state --> {new_state}')
                        if (new_state != (2, 0)) and (new_state != (2, 1)) and (new_state != (3, 1)) and (
                                new_state != (1, 3)) and (new_state != (2, 3)) and (new_state != (3, 3)) and (
                                new_state != (1, 4)):
                            updated_parent.region[3] = backTrackedUpperBound
                            env.current_state = new_state
                            region[1] = env.current_state[1]

                # print(env.current_state)

            # track region
            if action == 0:
                region[3] = env.current_state[0]
            elif action == 1:
                # region bound is decreasing, so set the lower bound to current state
                region[2] = env.current_state[0]
            elif action == 2:
                region[3] = env.current_state[1]
            elif action == 3:
                # region bound is decreasing
                region[2] = env.current_state[1]
            fitness += reward

            state, reward, terminate = env.step(action)

            if terminate:
                print('win!')
                if action == 0:
                    region[3] = env.current_state[0]
                # region[2] will take on the current state, because the region bound is decreasing here
                elif action == 1:
                    region[2] = env.current_state[0]
                elif action == 2:
                    region[3] = env.current_state[1]
                # also decreasing here...
                elif action == 3:
                    region[2] = env.current_state[1]
                fitness += reward
                break

        # set the start_state for the next rule to where the last rule left off
        # todo I think this needs to be before clipping
        self.start_state = env.current_state

        # clipping (to leave room for orthogonal action)
        if not terminate:
            if (action == 0 or action == 2) and region[3] > 0 and (region[2] - region[3] != 0):
                region[3] -= 1
            elif (action == 1 or action == 3) and region[2] < 4 and (region[2] - region[3] != 0):
                region[2] += 1

        # need to clip updated_parent if backtrack is true
        if backTrack:
            if (action == 0 or action == 2) and updated_parent.region[3] > 0 and \
                    (updated_parent.region[2] - updated_parent.region[3] != 0):
                updated_parent.region[3] -= 1
            elif (action == 1 or action == 3) and updated_parent.region[2] < 4 and \
                    (updated_parent.region[2] - updated_parent.region[3] != 0):
                updated_parent.region[2] += 1

        # update the parent's region in the team's learners if backtracking is true
        # need to do this before updating mostRecent
        if backTrack:
            for i in range(len(self.learners)):
                if self.learners[i].id == self.mostRecent.id:
                    self.learners[i].program.rule.region = updated_parent.region

        # construct the learner holding the new rule
        rule = Rule(uuid.uuid4(), region, action, fitness)
        learner = Learner(uuid.uuid4(), rule)
        # add that rule to the teams learners
        # todo will probably need to have some sort of learner competition function when we have limited learners per team
        # todo or add to a learner pool which new teams sample from...
        self.learners.append(learner)
        # add the rule's fitness to the team's overall fitness
        self.fitness += rule.fitness
        # set most recent to the rule that was just created
        self.mostRecent = learner

        #
        # if backTrack:
        #     print(f'resulting updated parent: {updated_parent.region}')
        # print(f'resulting region: {rule.region}')
        #
        # print(f'Terminate: {terminate}')

        return terminate

    def evaluate_rule(self, offspring):
        repeat = False
        for rule in self.rule_pool:
            if rule.region == offspring.region:
                repeat = True
        # repeat = False # turn off blocking repeats while figuring out backtracking...
        if not repeat:
            if len(self.rule_pool) == self.max_rules:
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

    # function to validate if the region is in the parent region, used in back-tracking
    # if the child's position is in the parent's region, return true, else false
    def in_parent_region(self, parent_region, child_position, action):
        # need to add in action checks to compensate for clipping
        # the action should be able to start in the clipped part (... that's the whole point of clipping)
        # it's safe here to assume the region is not out of bounds
        if (action == 0 or action == 2) and child_position[parent_region[0]] == parent_region[1] and \
                parent_region[2] <= child_position[not parent_region[0]] <= (parent_region[3]+1):
            return True
        if (action == 1 or action == 3) and child_position[parent_region[0]] == parent_region[1] and \
                (parent_region[2]-1) <= child_position[not parent_region[0]] <= parent_region[3]:
            return True
        return False
        # if child_position[parent_region[0]] == parent_region[1] and \
        #         (parent_region[2] <= child_position[not parent_region[0]] <= parent_region[3]):
        #     return True
        # return False

    ##############################
    # Region search stuff ends
    ##############################
