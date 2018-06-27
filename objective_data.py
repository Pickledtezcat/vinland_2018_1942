import bge
import bgeutils
import mathutils


class ObjectiveData(object):
    def __init__(self, objective):
        self.objective = objective
        self.environment = self.objective.environment
        self.objective_index = self.objective.get_stat("index")

    def update(self):
        if self.objective.get_stat("status") == "INACTIVE":
            if self.objective.check_triggered():
                self.objective.set_stat("status", "ACTIVE")

        if self.objective.get_stat("status") == "ACTIVE":
            if self.fail_check():
                self.objective.set_stat("status", "FAILED")

            elif not self.success_check():
                self.objective.set_stat("status", "COMPLETE")

    def fail_check(self):
        return False

    def success_check(self):
        return False

    def cycle(self):
        if self.objective.get_stat("status") == "ACTIVE":
            self.objective.turn_timer += 1

    def get_agents(self):
        agents = []
        for agent_key in self.environment.agents:
            agent = self.environment.agents[agent_key]
            if agent.get_stat("objective_index") == self.objective_index:
                if agent.check_active_enemy():
                    agents.append(agent_key)

        return agents


class AttackObjective(ObjectiveData):
    def __init__(self, objective):
        super().__init__(objective)

    def active_agents(self):
        agents = self.get_agents()
        if len(agents) > 0:
            return True

        return False

    def fail_check(self):
        max_turns = self.objective.get_stat("max_turns")
        if max_turns > 0:
            if self.objective.turn_timer > max_turns:
                return True

        return False

    def success_check(self):
        if not self.active_agents():
            return True

        return False


