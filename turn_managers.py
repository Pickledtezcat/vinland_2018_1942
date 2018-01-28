import bge
import bgeutils


class TurnManager(object):

    turn_type = "PROTOTYPE"

    def __init__(self, environment):

        self.team = 1
        self.environment = environment
        self.finished = False
        self.active_agent = None
        self.valid_agents = []

    def check_valid_units(self):
        team_units = []
        for agent_key in self.environment.agents:
            if self.environment.agents[agent_key].stats["team"] == self.team:
                # TODO add more checks for validity of agents, actions remaining etc...
                team_units.append(agent_key)
            else:
                print(self.environment.agents[agent_key].stats["team"], self.team)

        if not team_units:
            self.active_agent = None
        else:
            if self.active_agent:
                pass
            else:
                self.active_agent = team_units[0]

        self.valid_agents = team_units

    def update(self):
        self.process()

        if self.end_check():
            self.finished = True

    def process(self):
        pass

    def end_check(self):
        self.check_valid_units()
        if not self.valid_agents:
            return True

        return False


class PlayerTurn(TurnManager):

    def __init__(self, environment):
        self.turn_type = "PLAYER"
        super().__init__(environment)
        self.team = 1


class EnemyTurn(TurnManager):

    def __init__(self, environment):
        self.turn_type = "ENEMY"
        super().__init__(environment)
        self.team = 2

    def process(self):
        pass
