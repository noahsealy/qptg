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
        t_max = 30
        total_reward = 0
        seq = [{'learner': l_t, 'action': a_t}]
        states = [env.current_state]
        while t < t_max:
            s_next, reward, isDone = env.step(a_t)
            states.append(env.current_state)
            total_reward += reward
            if isDone:
                self.team.final_update(l_t, a_t, reward)
                return total_reward, True, states, seq
            l_next, a_next = self.team.evaluate(env.current_state)

            if l_t.id != l_next.id:
                self.team.update(l_t, l_next, a_t, reward)

            a_t = a_next
            l_t = l_next
            seq.append({'learner': l_t, 'action': a_t})
            t = t + 1
        return total_reward, False, states, seq

    def replay(self, env):
        l_t, a_t = self.team.evaluate(env.current_state)
        t = 0
        t_max = 50  # change this...
        total_reward = 0
        states = [env.current_state]  # return the states visited during replay

        while t < t_max:
            s_next, reward, isDone = env.step(a_t)
            states.append(s_next)
            total_reward += reward
            if isDone:
                return total_reward, True, states

            l_next, a_next = self.team.evaluate(env.current_state)

            a_t = a_next
            t = t + 1
        return total_reward, False, states
