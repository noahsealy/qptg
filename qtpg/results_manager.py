import uuid
import csv

from .team import Team
from .learner import Learner
from .rule import Rule


class ResultsManager:

    def save_champions(self, envName, run_winners, gp_queries, win_loss):
        print('Saving end...')
        save_id = envName
        file_name = f'qtpg/saved_champions/{save_id}.csv'

        with open(file_name, 'w') as csv_file:
            csv_writer = csv.writer(csv_file)
            for run in range(len(run_winners)):
                csv_writer.writerow(['run'])
                for champ in run_winners[run]['winners']:
                    csv_writer.writerow(['new champ', champ.id, champ.gen_created])
                    for learner in champ.learners:
                        row = []
                        row.append(learner.id)
                        row.append(learner.program.rule.id)
                        row.append(learner.program.rule.region)
                        row.append(learner.program.rule.action_set)
                        row.append(learner.program.rule.value_set)
                        row.append(learner.program.rule.fitness)
                        csv_writer.writerow(row)

        print('Env saved successfully!')
        print(file_name)

        file_name = f'qtpg/saved_champions/query_totals_{save_id}.csv'
        with open(file_name, 'w') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([gp_queries])
            csv_writer.writerow([win_loss])

    def load_champions(self, envName):
        print('Loading champions...')
        file_name = f'qtpg/saved_champions/{envName}.csv'

        run_winners = []
        run = 0
        champions = []
        team = Team(0, 0, 0, 0, 0, 0)
        with open(file_name, 'r') as csv_file:
            result_set = csv.reader(csv_file)
            for row in result_set:
                if row[0] == 'run':
                    if len(champions) > 0:
                        run_winners.append({'run': run, 'winners': champions})
                        run += 1
                    champions = []
                elif row[0] == 'new champ':
                    if team.id != 0:
                        champions.append(team)
                    team = Team(row[1], 0, 0, 0, 0, 0)
                else:
                    rule = Rule(row[1], eval(row[2]), eval(row[3]), eval(row[5]))
                    # rule.value_set = eval(row[4])
                    rule.value_set = [0, 0]
                    rule.value_set[0] = float(eval(row[4])[0])
                    rule.value_set[1] = float(eval(row[4])[1])
                    print(type(rule.value_set[0]))
                    print(rule.region)
                    print(rule.fitness)
                    print(f'region index type: {type(rule.region[0])}')
                    learner = Learner(row[0], rule)
                    team.learners.append(learner)

        query_totals = []
        with open(f'qtpg/saved_champions/query_totals_{envName}.csv', 'r') as csv_file:
            totals = csv.reader(csv_file)
            # query_totals = eval(totals[0][0])
            # win_loss = eval(totals[1][0])
            count = 0
            for row in totals:
                if count == 0:
                    query_totals = eval(row[0])
                else:
                    win_loss = eval(row[0])
                count += 1

        print('Champions loaded successfully!')
        return run_winners, query_totals, win_loss

    # def load(self, id, display=True):
    #     print('Loading env...')
    #     file_name = f'qtpg/saved_environments/{id}.csv'
    #     with open(file_name, 'r') as csv_file:
    #         env = csv.reader(csv_file)
    #
    #         for row in env:
    #             self.rows = int(row[1])
    #             self.cols = int(row[2])
    #             self.start_state = eval(row[3])
    #             self.win_state = eval(row[4])
    #             self.illegal_states = eval(row[5])
    #
    #     print('Env loaded successfully!')
    #     if display:
    #         self.display()
