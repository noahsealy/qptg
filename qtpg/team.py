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
        self.mostRecent = 0
        self.fitness = 0
        self.start_state = (0, 0)
        #### team competition variables end ####

        self.gp_query_env = 0

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

    # allows us to seed learners
    def init_search(self, env, action_set):

        action = action_set[random.randint(0, 1)]

        fitness = 0
        reward = 0
        region = [0, 0, 0, 0]
        flip = 0
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

        while reward >= 0 or (reward < 0 and flip < len(action_set)):
            # print('new step-------')
            # print(action)
            # print(env.current_state)
            if reward < 0:
                flip += 1
                if flip == len(action_set):  # don't love this, but need a way to pull it out of the loop...
                    break
                else:
                    # flip the action
                    new_action = 0
                    for i in range(len(action_set)):
                        if action != action_set[i]:
                            new_action = action_set[i]
                    action = new_action
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
        # print(region)
        rule = Rule(uuid.uuid4(), region, action_set, fitness)
        learner = Learner(uuid.uuid4(), rule)
        self.learners.append(learner)
        self.fitness += rule.fitness
        self.mostRecent = learner
        self.start_state = env.current_state

    def search(self, env):
        selected_rule = self.mostRecent.program.rule

        # try starting from a random region...? replacing ^...
        # random_region = random.randint(0, len(self.learners)-1)
        # selected_rule = self.learners[random_region].program.rule
        # print(selected_rule.region)

        # print('new search:--------------------------------')
        # action = 0
        # if selected_rule.action_set == 0 or selected_rule.action_set == 1:
        #     action = random.randint(2, 3)
        # elif selected_rule.action_set == 2 or selected_rule.action_set == 3:
        #     action = random.randint(0, 1)

        action_set = []
        if selected_rule.action_set[0] == 0 and selected_rule.action_set[1] == 1:  # if north south, set to east west
            action_set = [2, 3]
        else:  # if it was east and west, set to north and south
            action_set = [0, 1]

        # sample which action goes first
        action = action_set[random.randint(0, 1)]

        # sample start within the region
        # we use current state instead of the max region because the max gets clipped from orthogonal backtracking
        sample_start = [0, 0]

        # assign the non-moving space to the non-moving coord
        sample_start[selected_rule.region[0]] = selected_rule.region[1]

        illegal = True
        # reject all illegal cells with this while loop
        # print(f'Selected region: {selected_rule.region}')

        # sample a legal starting state
        while illegal:
            if (selected_rule.region[3] - selected_rule.region[2]) == 0:
                sample_start[not selected_rule.region[0]] = selected_rule.region[2]
            else:
                sample_start[not selected_rule.region[0]] = random.randint(selected_rule.region[2], selected_rule.region[3])
            if env.check_legal(sample_start):
                illegal = False

        # # clipping is not needed if region[2] == region[3], there's no space for clipping to occur
        # if selected_rule.region[3] > selected_rule.region[2]:
        #     # now insert the child region by clipping the parent region
        #     if sample_start[not selected_rule.region[0]] == env.rows-1:
        #         selected_rule.region[2] = sample_start[not selected_rule.region[0]] - 1
        #         selected_rule.region[3] = sample_start[not selected_rule.region[0]] - 1
        #         if selected_rule.region[3] < selected_rule.region[2]:
        #             print(f'first HEYYYYY --> {sample_start}, {selected_rule.region}')
        #     elif sample_start[not selected_rule.region[0]] == 0:
        #         selected_rule.region[2] = sample_start[not selected_rule.region[0]] + 1
        #         selected_rule.region[3] = sample_start[not selected_rule.region[0]] + 1
        #         if selected_rule.region[3] < selected_rule.region[2]:
        #             print(f'second HEYYYYY --> {sample_start}, {selected_rule.region}')
        #     else:
        #         print(f'sample start --> {sample_start}')
        #         print(f'to be clipped --> {selected_rule.region}')
        #         after_clip = copy.deepcopy(selected_rule)
        #         # bit of a hacky solution
        #         if selected_rule.region[2] < sample_start[not selected_rule.region[0]] - 1:
        #             selected_rule.region[3] = sample_start[not selected_rule.region[0]] - 1
        #         # we need this in the case of the sample start being region[2] of the original rule
        #         # if that would happen without this case, region[3] would be one less than region[2]
        #         else:
        #             selected_rule.region[3] = sample_start[not selected_rule.region[0]]
        #
        #         if selected_rule.region[3] > sample_start[not selected_rule.region[0]] + 1:
        #             after_clip.region[2] = sample_start[not selected_rule.region[0]] + 1
        #         # we need this in the case of the sample start being region[3] of the original rule
        #         # if that would happen without this case, region[2] would be one greater than region[3]
        #         else:
        #             after_clip.region[2] = sample_start[not selected_rule.region[0]]
        #
        #         after_clip_learner = Learner(uuid.uuid4(), after_clip)
        #         self.learners.append(after_clip_learner)
        #         print(f'clipping produced --> {selected_rule.region} and {after_clip.region}')
        # else:
        #     print('HEYYYYYYYYYY')
        #     print(selected_rule.region)
        #

        # if selected_rule.region[3] >= selected_rule.region[2]:
        #     # now insert the child region by clipping the parent region
        #     if sample_start[not selected_rule.region[0]] == env.rows-1: #4:
        #         selected_rule.region[3] = sample_start[not selected_rule.region[0]] - 1
        #         if selected_rule.region[3] < selected_rule.region[2]:
        #         #     selected_rule.region[2] = sample_start[not selected_rule.region[0]] - 1
        #             print(f'first HEYYYYY --> {sample_start}, {selected_rule.region}')
        #     elif sample_start[not selected_rule.region[0]] == 0:
        #         selected_rule.region[2] = sample_start[not selected_rule.region[0]] + 1
        #         if selected_rule.region[3] < selected_rule.region[2]:
        #             # selected_rule.region[3] = sample_start[not selected_rule.region[0]] + 1
        #             print(f'second HEYYYYY --> {sample_start}, {selected_rule.region}')
        #     else:
        #         print(selected_rule.region)
        #         after_clip = copy.deepcopy(selected_rule)
        #         # if sample_start[not selected_rule.region[0]] - 1 >= selected_rule.region[2]:
        #         selected_rule.region[3] = sample_start[not selected_rule.region[0]] - 1
        #         # else:
        #         #     selected_rule.region[3] = sample_start[not selected_rule.region[0]] - 1
        #         #     selected_rule.region[2] = selected_rule.region[2]-1
        #
        #         # if sample_start[not selected_rule.region[0]] + 1 <= after_clip.region[3]:
        #         after_clip.region[2] = sample_start[not selected_rule.region[0]] + 1
        #         # else:
        #         #     after_clip.region[2] = sample_start[not selected_rule.region[0]] + 1
        #         #     after_clip.region[3] = after_clip.region[3]+1
        #
        #         after_clip_learner = Learner(uuid.uuid4(), after_clip)
        #         self.learners.append(after_clip_learner)
        #         print(f'clipping produced --> {selected_rule.region} and {after_clip.region}')
        # else:
        #     print('eek!')

        if selected_rule.region[2] != selected_rule.region[3]:
            if sample_start[not selected_rule.region[0]] == env.rows-1:
                selected_rule.region[3] = sample_start[not selected_rule.region[0]] - 1
                print(f'clipping produced --> {selected_rule.region}')
            elif sample_start[not selected_rule.region[0]] == 0:
                selected_rule.region[2] = sample_start[not selected_rule.region[0]] + 1
                print(f'clipping produced --> {selected_rule.region}')
            else:
                if sample_start[not selected_rule.region[0]] == selected_rule.region[3]:
                    selected_rule.region[3] = selected_rule.region[3] - 1
                    print(f'clipping produced --> {selected_rule.region}')
                elif sample_start[not selected_rule.region[0]] == selected_rule.region[2]:
                    selected_rule.region[2] = selected_rule.region[2] + 1
                    print(f'clipping produced --> {selected_rule.region}')
                else:
                    after_clip = copy.deepcopy(selected_rule)
                    selected_rule.region[3] = sample_start[not selected_rule.region[0]] - 1
                    after_clip.region[2] = sample_start[not selected_rule.region[0]] + 1
                    after_clip_learner = Learner(uuid.uuid4(), after_clip)
                    self.learners.append(after_clip_learner)
                    print(f'clipping produced --> {selected_rule.region} and {after_clip.region}')




        # todo everything in this while illegal: loop is old clipping
        # while illegal:
        #     # north and east start sampling
        #     if (action == 0 or action == 2) and selected_rule.region[3] < 4:
        #         sample_start[not selected_rule.region[0]] = random.randint(selected_rule.region[2],
        #                                                                    selected_rule.region[3] + 1)
        #         # sample_start[not selected_rule.region[0]] = selected_rule.region[3] + 1
        #         # clip the parent region to end right where the sample picks up
        #         # if sample_start[not selected_rule.region[0]] > 0: #TODO find a way to handle these bounds
        #         selected_rule.region[3] = sample_start[not selected_rule.region[0]]-1
        #
        #         if sample_start[not selected_rule.region[0]] < 4:
        #             # second learner produced by this needs to be actually written in
        #             clipped_after = copy.deepcopy(selected_rule)
        #             clipped_after.region[2] = sample_start[not selected_rule.region[0]]+1
        #             clipped_rule = Rule(uuid.uuid4(), clipped_after.region, clipped_after.action_set, clipped_after.fitness)
        #             clipped = Learner(uuid.uuid4(), clipped_rule)
        #             self.learners.append(clipped)
        #     # south and west start sampling
        #     elif (action == 1 or action == 3) and selected_rule.region[2] > 0:
        #         sample_start[not selected_rule.region[0]] = random.randint(selected_rule.region[2] - 1,
        #                                                                    selected_rule.region[3])
        #         # sample_start[not selected_rule.region[0]] = selected_rule.region[2] - 1
        #         # clip the parent region to end right where the sample picks up
        #         if sample_start[not selected_rule.region[0]] > 0:
        #             selected_rule.region[3] = sample_start[not selected_rule.region[0]]-1 # used to be [2]
        #
        #         if sample_start[not selected_rule.region[0]] < 4:
        #             # second learner produced by this needs to be actually written in
        #             clipped_after = copy.deepcopy(selected_rule)
        #             clipped_after.region[2] = sample_start[not selected_rule.region[0]]+1
        #             clipped_rule = Rule(uuid.uuid4(), clipped_after.region, clipped_after.action_set, clipped_after.fitness)
        #             clipped = Learner(uuid.uuid4(), clipped_rule)
        #             self.learners.append(clipped)
        #     # covers sampling for outskirt cells, as we can not add or subtract from those
        #     else:
        #         sample_start[not selected_rule.region[0]] = random.randint(selected_rule.region[2],
        #                                                                    selected_rule.region[3])
        #
        #
        #     if env.check_legal(sample_start):
        #         illegal = False
        #     else:
        #         # action = random.randint(0, 3)
        #         # known bug, for now just throw out the results...
        #         print('dud')
        #         return False

        # print(f'Sample start: {sample_start}')

        env.current_state = (sample_start[0], sample_start[1])

        # env.current_state = self.start_state  # TODO will I replace this for the stuff above?... depends if we want sampling or not
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
        backTrackLimit = 0  # todo replace with repeat penalty?
        flip = 0
        while ((reward >= 0 and flip < len(action_set)) or
               (reward < 0 and flip < len(action_set) and not backTrack) or
               (reward < 0 and self.in_parent_region(updated_parent.region, env.current_state, action))) \
                and backTrackLimit < 10:
            backTrackLimit += 1
            if reward < 0 and not self.in_parent_region(updated_parent.region, env.current_state, action):
                flip += 1
                if flip == len(action_set):  # don't love this, but need a way to pull it out of the loop...
                    break
                else:
                    # flip the action
                    new_action = 0
                    for i in range(len(action_set)):
                        if action != action_set[i]:
                            new_action = action_set[i]
                    action = new_action

            # if the team is within the region of the previous rule, we need to backtrack (and not set a region)
            if reward < 0 and self.in_parent_region(updated_parent.region, env.current_state, action):
                print('backTrack!')
                backTrack = True
                backTrackedLowerBound = 0
                backTrackedUpperBound = 0
                # print('backtracked')
                # print(env.current_state)
                # if the state where backtracking is required is the lower bound
                # if env.current_state[not updated_parent.region[0]] == updated_parent.region[2]:
                if action == 1 or action == 3:
                    # backtrack the region bound, we add here as it is always a lower bound
                    if updated_parent.region[2] < env.rows-1:#4:
                        backTrackedLowerBound = updated_parent.region[2] + 1
                        # print(f'Backtrackregioncehck: {updated_parent.region}')
                        # updated_parent.region[2] = updated_parent.region[2] + 1
                    if updated_parent.region[0] == 1:
                        # update the env state
                        # new_state = (updated_parent.region[2], env.current_state[1])
                        new_state = (backTrackedLowerBound, env.current_state[1])
                        # print(f'new state --> {new_state}')
                        if env.check_legal(new_state):
                            updated_parent.region[2] = backTrackedLowerBound
                            env.current_state = new_state
                            region[1] = env.current_state[0]
                    else:
                        # new_state = (env.current_state[0], updated_parent.region[2])
                        new_state = (env.current_state[0], backTrackedLowerBound)
                        # print(f'new state --> {new_state}')
                        if env.check_legal(new_state):
                            updated_parent.region[2] = backTrackedLowerBound
                            env.current_state = new_state
                            region[1] = env.current_state[1]

                # coord that we're not keeping constant must equal the upper bound
                else:
                    # backtrack the region bound, we subtract here as it is always an upper bound
                    if updated_parent.region[3] > 0:
                        # updated_parent.region[3] = updated_parent.region[3] - 1
                        backTrackedUpperBound = updated_parent.region[3] - 1
                        # print(f'Backtrackregioncehck: {updated_parent.region}')
                    # correct the position of the agent, tuples are immutable...
                    if updated_parent.region[0] == 1:
                        # soon, this will be replaced by just having the searcher step into the env
                        # that way, we don't have to call these checks...
                        # new_state = (updated_parent.region[3], env.current_state[1])
                        new_state = (backTrackedUpperBound, env.current_state[1])
                        # print(f'new state --> {new_state}')
                        if env.check_legal(new_state):
                            updated_parent.region[3] = backTrackedUpperBound
                            env.current_state = new_state
                            region[1] = env.current_state[0]
                    else:
                        # search_space.current_state = (prev_rule.region[3], search_space.current_state[0])
                        # new_state = (env.current_state[0], updated_parent.region[3])
                        new_state = (env.current_state[0], backTrackedUpperBound)
                        # print(f'new state --> {new_state}')

                        if env.check_legal(new_state):
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
            print(f'New state for {self.id} --> {state}')
            # print('New real step: ')
            # print(action)
            # print(state)

            if terminate:
                # print('win!')
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
        # TODO clipping was moved to occur on insertion, we'll still keep clipping on backtrack as that's kinda different
        # if not terminate:
        #     if (action == 0 or action == 2) and region[3] > 0 and (region[2] - region[3] != 0):
        #         region[3] -= 1
        #     elif (action == 1 or action == 3) and region[2] < 4 and (region[2] - region[3] != 0):
        #         region[2] += 1

        # need to clip updated_parent if backtrack is true
        ## TODO just removed this
        # if backTrack:
        #     if (action == 0 or action == 2) and updated_parent.region[3] > 0 and \
        #             (updated_parent.region[2] - updated_parent.region[3] != 0):
        #         updated_parent.region[3] -= 1
        #     elif (action == 1 or action == 3) and updated_parent.region[2] < env.rows-1 and \
        #             (updated_parent.region[2] - updated_parent.region[3] != 0):
        #         updated_parent.region[2] += 1

        # update the parent's region in the team's learners if backtracking is true
        # need to do this before updating mostRecent
        if backTrack:
            for i in range(len(self.learners)):
                if self.learners[i].id == self.mostRecent.id:
                    self.learners[i].program.rule.region = updated_parent.region

        # construct the learner holding the new rule
        # rule = Rule(uuid.uuid4(), region, action, fitness)
        rule = Rule(uuid.uuid4(), region, action_set, fitness)
        learner = Learner(uuid.uuid4(), rule)
        print(region)
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
                parent_region[2] <= child_position[not parent_region[0]] <= (parent_region[3] + 1):
            return True
        if (action == 1 or action == 3) and child_position[parent_region[0]] == parent_region[1] and \
                (parent_region[2] - 1) <= child_position[not parent_region[0]] <= parent_region[3]:
            return True
        return False
        # if child_position[parent_region[0]] == parent_region[1] and \
        #         (parent_region[2] <= child_position[not parent_region[0]] <= parent_region[3]):
        #     return True
        # return False



    def search_no_back_track(self, env):
        selected_rule = self.mostRecent.program.rule

        action_set = []
        if selected_rule.action_set[0] == 0 and selected_rule.action_set[1] == 1:  # if north south, set to east west
            action_set = [2, 3]
        else:  # if it was east and west, set to north and south
            action_set = [0, 1]

        # sample which action goes first
        action = action_set[random.randint(0, 1)]

        # sample start within the region
        # we use current state instead of the max region because the max gets clipped from orthogonal backtracking
        sample_start = [0, 0]

        # assign the non-moving space to the non-moving coord
        sample_start[selected_rule.region[0]] = selected_rule.region[1]

        illegal = True

        # sample a legal starting state
        while illegal:
            if (selected_rule.region[3] - selected_rule.region[2]) == 0:
                sample_start[not selected_rule.region[0]] = selected_rule.region[2]
            else:
                sample_start[not selected_rule.region[0]] = random.randint(selected_rule.region[2], selected_rule.region[3])
            if env.check_legal(sample_start):
                illegal = False

        if selected_rule.region[2] != selected_rule.region[3]:
            if sample_start[not selected_rule.region[0]] == env.rows-1:
                selected_rule.region[3] = sample_start[not selected_rule.region[0]] - 1
                # print(f'clipping produced --> {selected_rule.region}')
            elif sample_start[not selected_rule.region[0]] == 0:
                selected_rule.region[2] = sample_start[not selected_rule.region[0]] + 1
                # print(f'clipping produced --> {selected_rule.region}')
            else:
                if sample_start[not selected_rule.region[0]] == selected_rule.region[3]:
                    selected_rule.region[3] = selected_rule.region[3] - 1
                    # print(f'clipping produced --> {selected_rule.region}')
                elif sample_start[not selected_rule.region[0]] == selected_rule.region[2]:
                    selected_rule.region[2] = selected_rule.region[2] + 1
                    # print(f'clipping produced --> {selected_rule.region}')
                else:
                    after_clip = copy.deepcopy(selected_rule)
                    selected_rule.region[3] = sample_start[not selected_rule.region[0]] - 1
                    after_clip.region[2] = sample_start[not selected_rule.region[0]] + 1
                    after_clip_learner = Learner(uuid.uuid4(), after_clip)
                    self.learners.append(after_clip_learner)
                    # print(f'clipping produced --> {selected_rule.region} and {after_clip.region}')

        env.current_state = (sample_start[0], sample_start[1])

        # init region
        reward = 0
        region = [0, 0, 0, 0]
        if action == 0:
            region[0] = 1
            region[1] = env.current_state[1]
            region[2] = env.current_state[0]
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
        elif action == 3:
            region[0] = 0
            region[1] = env.current_state[0]
            # the action is west, so the current state will always be decreasing
            # thus, set the upper region bound to the current state
            region[3] = env.current_state[1]

        fitness = 0
        # search region
        terminate = False

        flip = 0
        step_count = 0
        while (reward >= 0 and flip < len(action_set)) or (reward < 0 and flip < len(action_set)):

            # only way this was let in if reward is negative but flip is not done
            if reward < 0:
                flip += 1
                if flip == len(action_set):  # don't love this, but need a way to pull it out of the loop...
                    break
                else:
                    # flip the action
                    new_action = 0
                    for i in range(len(action_set)):
                        if action != action_set[i]:
                            new_action = action_set[i]
                    action = new_action

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
            step_count += 1
            state, reward, terminate = env.step(action)
            # print(f'New state for {self.id} --> {state}')

            if terminate:
                # print('win!')
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
        self.start_state = env.current_state

        # penalize a 0 step count
        if step_count == 2 and (region[3] - region[2] == 0): # right...?
            print('no steps!')
            fitness += -100

        print('------')
        print(step_count)
        print(region)
        print('------')

        # query for gp is n+1 where n is region size
        # region[3] - region[2] will give its size
        if region[3] - region[2] >= 0:
            self.gp_query_env += (region[3] - region[2]) + 1

        # construct the learner holding the new rule
        rule = Rule(uuid.uuid4(), region, action_set, fitness)
        # record the winning state on the winning rule, so we don't have to query the env for it later
        if terminate:
            rule.win = env.current_state
        print(rule.region)
        learner = Learner(uuid.uuid4(), rule)
        # print(region)
        # add that rule to the teams learners
        self.learners.append(learner)
        # add the rule's fitness to the team's overall fitness
        self.fitness += rule.fitness
        # set most recent to the rule that was just created
        self.mostRecent = learner

        return terminate

    def goal_start_search(self, env):
        selected_rule = self.mostRecent.program.rule

        action_set = []
        if selected_rule.action_set[0] == 0 and selected_rule.action_set[1] == 1:  # if north south, set to east west
            action_set = [2, 3]
        else:  # if it was east and west, set to north and south
            action_set = [0, 1]

        # sample which action goes first
        action = action_set[random.randint(0, 1)]

        # sample start within the region
        # we use current state instead of the max region because the max gets clipped from orthogonal backtracking
        sample_start = [0, 0]

        # assign the non-moving space to the non-moving coord
        sample_start[selected_rule.region[0]] = selected_rule.region[1]

        illegal = True

        # sample a legal starting state
        while illegal:
            if (selected_rule.region[3] - selected_rule.region[2]) == 0:
                sample_start[not selected_rule.region[0]] = selected_rule.region[2]
            else:
                print(selected_rule.region)
                sample_start[not selected_rule.region[0]] = random.randint(selected_rule.region[2], selected_rule.region[3])
            if env.check_legal(sample_start):
                illegal = False

        env.current_state = (sample_start[0], sample_start[1])

        # init region
        reward = 0
        region = [0, 0, 0, 0]
        if action == 0:
            region[0] = 1
            region[1] = env.current_state[1]
            region[2] = env.current_state[0]
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
        elif action == 3:
            region[0] = 0
            region[1] = env.current_state[0]
            # the action is west, so the current state will always be decreasing
            # thus, set the upper region bound to the current state
            region[3] = env.current_state[1]

        fitness = 0
        # search region
        terminate = False

        flip = 0
        while (reward >= 0 and flip < len(action_set)) or (reward < 0 and flip < len(action_set)):

            # only way this was let in if reward is negative but flip is not done
            if reward < 0:
                flip += 1
                if flip == len(action_set):  # don't love this, but need a way to pull it out of the loop...
                    break
                else:
                    # flip the action
                    new_action = 0
                    for i in range(len(action_set)):
                        if action != action_set[i]:
                            new_action = action_set[i]
                    action = new_action

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
            # print(f'New state for {self.id} --> {state}')

            if terminate:
                # print('win!')
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

        # GOAL START CHILD CLIPPING
        # after the child region is fully developed, find it's intersection with the parent region,
        # and remove that state from the child region

        # find intersection between parent and child
            # between selected_rule.region and region

        # intersect has to be the sample start
        intersect = sample_start

        # deconstruct the region into coords
        child_states = []
        for i in range(region[2], region[3] + 1):
            coord = [0, 0]
            coord[region[0]] = region[1]
            coord[not region[0]] = i
            child_states.append(coord)

        # find the intersect and remove it from the list of coords
        pop_index = 0
        found = False
        for n in range(len(child_states)):
            if child_states[n] == intersect and not found:
                found = True
                pop_index = n
        if found:
            child_states.pop(pop_index)
        else:
            return []

        # reconstruct the child region, it comes out as a list
        # use a list as there may be more than one regions if clipping occurred in the middle
        clipped_child_regions = []
        # child = [region[0], region[1], region[2], 0]
        child = [region[0], region[1], region[2], region[2]]
        for i in range(len(child_states)):
            if i > 0:
                if not child_states[i][not region[0]] - 1 == child_states[i - 1][not region[0]]:
                    clipped_child_regions.append(child)
                    # child = [region[0], region[1], i + 1, i + 1]
                    child = [region[0], region[1], child[2] + 1, child[3] + 1]
                else:
                    child[3] = child[3] + 1
        clipped_child_regions.append(child)


        # set the start_state for the next rule to where the last rule left off
        self.start_state = env.current_state


        for clipped_child_region in clipped_child_regions:
            # construct the learner holding the new rule
            # rule = Rule(uuid.uuid4(), region, action_set, fitness)
            rule = Rule(uuid.uuid4(), clipped_child_region, action_set, fitness)
            learner = Learner(uuid.uuid4(), rule)
            # print(region)
            # add that rule to the teams learners
            self.learners.append(learner)
            # add the rule's fitness to the team's overall fitness
            self.fitness += rule.fitness
            # set most recent to the rule that was just created
            self.mostRecent = learner

        return terminate

    ##############################
    # Region search stuff ends
    ##############################

    # the in-betweeen....

    ##############################
    # Q After Search stuff starts
    ##############################

    def prune_single_cell_regions(self):
        print('PRUNING SINGLE CELL REGIONS!')
        print(len(self.learners))
        pruned = []
        for learner in self.learners:
            if learner.program.rule.region[2] != learner.program.rule.region[3]:
                # or (learner.program.rule.region[2] == 0 and learner.program.rule.region[3] == 0):
                pruned.append(learner)
        self.learners = pruned
        print(len(self.learners))

    def prune_duplicate_regions(self):
        # print('PRUNING DUPLICATES!')
        # print(len(self.learners))

        index = 0
        for learner in self.learners:
            index = 0
            for duplicate_search in self.learners:
                if learner.id != learner.id and learner.program.rule.region == duplicate_search.program.rule.region:
                    self.learners.pop(index)

        # print(len(self.learners))


    # selects a learner to q_evaluate who has a region that the current state is within
    # this needs to be a separate function than q_evaluation as we need it to select the t+1 learner (see transition_update function below)
    # so we eval 'learner', then select 'learner+1' from the state 'learner' left off, and use 'learner+1' as the MAX(q(l+1, a)) for 'learner''s q-update
    # this ordering of these functions is very important!
    def select_learner(self, current_state, selected_region):
        eligible_learners = []
        # find which regions are in that state
        for learner in self.learners:
            if self.state_within_region(current_state, learner.program.rule.region) and learner.program.rule.region != selected_region:
                # print(f'regions --> {selected_region} is eligible with {learner.program.rule.region}')
                eligible_learners.append(learner)
        # if len(eligible_learners) == 0:
        #     print('oh no!')

        for learner in eligible_learners:
            print(f'{learner.program.rule.region} --> {learner.program.rule.action_set}')

        # if len(eligible_learners) == 0:
        #     print('eek!')
        #     print(env.current_state)
        #     for learner in self.learners:
        #         print(learner.program.rule.region)


        # if len(eligible_learners) > 1:
        #     selected_learner = eligible_learners[random.randint(0, len(eligible_learners) - 1)]
        # else:
        #     selected_learner = eligible_learners[0]

        if len(eligible_learners) > 1:
            selected_learner = eligible_learners[random.randint(0, len(eligible_learners) - 1)]
        elif len(eligible_learners) == 1:
            selected_learner = eligible_learners[0]
        else:
            print('eek!')
            return
        # print(f'we chose --> {selected_learner.program.rule.region}')
        return selected_learner

    # just used to check if a state is in a learner's region
    def state_within_region(self, state, region):
        if state[region[0]] == region[1] and region[2] <= state[not region[0]] <= region[3]:
            return True
        return False

    def q_evaluation(self, current_state, selected_learner, illegal_states, dimensions):
        # go until transition is found
        win = False
        action = 0
        reward = 0
        while self.state_within_region(current_state, selected_learner.program.rule.region):

            # use e-greedy to parse through, assigning q-values to the actions as we go
            action = selected_learner.program.rule.e_greedy()
            # go until transition is found
            # state, reward, win = env.step(action)

            current_state, win = selected_learner.program.rule.step(action, current_state, illegal_states, dimensions)


            # for i in range(len(selected_learner.program.rule.action_set)):
            #     if action == selected_learner.program.rule.action_set[i]:
            #         selected_learner.program.rule.value_set[i] += reward

            # print(selected_learner.program.rule.region)
            # print(selected_learner.program.rule.action_set)
            # print(selected_learner.program.rule.value_set)
            # print(action)
            # print(state)
            if win:
                break
        # when we find transition, the learner's action becomes the action
        print(f'Winning action: {action}')

        if win:
            print('win!')
            reward = 100
        else:
            reward = 0.01

        return win, selected_learner, reward, action, current_state

    # typical q-update
    # needs to be called AFTER transition so we know which the learner for the next region is
    def transition_update(self, reward, winning_action, learner_t, learner_t_plus_one):
        # find MAX(q(l+1, a))
        max_plus_one_q = max(learner_t_plus_one.program.rule.value_set)

        # assign the winning learner the action of one reward
        for i in range(len(learner_t.program.rule.action_set)):
            if learner_t.program.rule.action_set[i] == winning_action:
                learner_t.program.rule.value_set[i] += self.alpha * (reward + self.discount * max_plus_one_q - learner_t.program.rule.value_set[i])

    # special q-update for when we win
    # MAX(q(l+1, a)) is simply set to zero, as there is no 't+1' learner
    def final_update(self, reward, winning_action, winning_learner):
        # assign the winning learner the action of one reward
        for i in range(len(winning_learner.program.rule.action_set)):
            if winning_learner.program.rule.action_set[i] == winning_action:
                winning_learner.program.rule.value_set[i] += self.alpha * (reward - winning_learner.program.rule.value_set[i])

    ##############################
    # Q After Search stuff ends
    ##############################
