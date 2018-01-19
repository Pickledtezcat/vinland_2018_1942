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






