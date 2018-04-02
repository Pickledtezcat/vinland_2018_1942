import bge
import mathutils


class AgentModel(object):

    def __init__(self, agent, adder):

        self.agent = agent
        self.environment = self.agent.environment
        self.adder = adder

        self.model = self.add_model()
        self.timer = 0
        self.animation_finished = True
        self.playing = None

    def add_model(self):
        model = self.adder.scene.addObject(self.agent.load_key, self.adder, 0)
        model.setParent(self.adder)

        return model

    def update(self):
        self.process()

    def process(self):
        pass

    def set_animation(self, animation_type):
        self.timer = 0
        self.playing = animation_type
        self.animation_finished = False

    def attack_animation(self):
        if self.timer > 300:
            self.animation_finished = True
        else:
            self.timer += 1

    def movement_animation(self):
        self.animation_finished = True

    def background_animation(self):
        pass


class VehicleModel(AgentModel):
    def __init__(self, agent, adder):
        super().__init__(agent, adder)


class InfantryModel(AgentModel):
    def __init__(self, agent, adder):
        super().__init__(agent, adder)

    def add_model(self):
        model = self.adder.scene.addObject("squad", self.adder, 0)
        model.setParent(self.adder)

        return model


