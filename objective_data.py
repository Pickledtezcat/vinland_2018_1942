import bge
import bgeutils
import mathutils

class ObjectiveData(object):
    def __init__(self, objective):
        self.objective = objective
        self.environment = self.objective.environment

    def update(self):
        pass

    def cycle(self):
        pass
