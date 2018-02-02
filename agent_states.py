import bge
import mathutils


class AgentState(object):

    def __init__(self, agent):
        self.agent = agent
        self.environment = self.agent.environment

        self.name = type(self).__name__
        self.transition = None
        self.count = 0

    def end(self):
        pass

    def update(self):

        exit_check = self.exit_check()
        if exit_check:
            self.transition = exit_check
        else:
            self.process()

    def exit_check(self):
        return False

    def process(self):
        pass


class AgentStartUp(AgentState):

    def __init__(self, agent):
        super().__init__(agent)
        self.agent.set_occupied(self.agent.stats["position"])
        self.agent.busy = False

    def exit_check(self):
        return AgentIdle


class AgentIdle(AgentState):

    def __init__(self, agent):
        super().__init__(agent)
        self.agent.busy = False

    def exit_check(self):
        if not self.agent.movement.done:
            return AgentMoving


class AgentMoving(AgentState):
    def __init__(self, agent):
        super().__init__(agent)
        self.agent.busy = True

    def process(self):
        self.agent.movement.update()

    def exit_check(self):
        if self.agent.movement.done:
            self.agent.environment.turn_manager.pathfinder.update_map()
            return AgentIdle








