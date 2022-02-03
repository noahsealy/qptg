from .team import Team


class Agent:

    def __init__(self, id, team: Team):
        self.id = id
        self.team = team
        self.win = False
        self.fitness = 0

    def evaluate_fitness(self, env):
        l_t, a_t = self.team.evaluate(env.current_state)
        t = 0
        t_max = 100  # change this...
        total_reward = 0

        while t < t_max:
            s_next, reward, isDone = env.step(a_t)
            total_reward += reward
            if isDone:
                self.team.final_update(l_t, a_t, reward)
                # print(self.team.q_table)
                print('winner!! start')
                for q_value in self.team.q_table:
                    print(str(q_value['learner']) + ' ' + str(q_value['action']) + ' ' + str(q_value['q']))
                print('winner!! end')
                return total_reward, True

            l_next, a_next = self.team.evaluate(env.current_state)

            if l_t.id != l_next.id:
                self.team.update(l_t, l_next, a_t, reward)

            a_t = a_next
            l_t = l_next
            t = t + 1
        return total_reward, False

    def replay(self, env):
        # print('agent state ----------------------------')
        # for q_value in self.team.q_table:
        #     print(str(q_value['learner']) + ' ' + str(q_value['action']) + ' ' + str(q_value['q']))
        # print('agent, do yo thing ----------------------------')
        l_t, a_t = self.team.evaluate(env.current_state)
        t = 0
        t_max = 100  # change this...
        total_reward = 0
        states = []  # return the states visited during replay
        states.append(env.current_state)

        while t < t_max:
            s_next, reward, isDone = env.step(a_t)
            states.append(s_next)
            total_reward += reward
            if isDone:
                # for q_value in self.team.q_table:
                #     print(str(q_value['learner']) + ' ' + str(q_value['action']) + ' ' + str(q_value['q']))
                # print('agent end ----------------------------')
                return total_reward, True, states

            l_next, a_next = self.team.evaluate(env.current_state)

            a_t = a_next
            t = t + 1
        # for q_value in self.team.q_table:
        #     print(str(q_value['learner']) + ' ' + str(q_value['action']) + ' ' + str(q_value['q']))
        # print('agent end ----------------------------')
        return total_reward, False, states
