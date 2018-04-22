import bge
import bgeutils
import mathutils
import particles


class AgentModel(object):

    def __init__(self, agent, adder):

        self.agent = agent
        self.environment = self.agent.environment
        self.adder = adder

        self.model = self.add_model()
        self.timer = 0
        self.max_timer = 6
        self.animation_finished = True
        self.playing = None
        self.triggered = False

        self.turret = bgeutils.get_ob("turret", self.model.children)
        self.hull_emitter = bgeutils.get_ob("gun_emitter", self.model.children)
        self.turret_emitter = self.hull_emitter
        if self.turret:
            self.turret_emitter = bgeutils.get_ob("gun_emitter", self.turret.children)

    def add_model(self):
        model = self.adder.scene.addObject(self.agent.load_key, self.adder, 0)
        model.setParent(self.adder)

        return model

    def update(self):
        self.process()
        return not self.animation_finished

    def recycle(self):
        self.triggered = False
        self.timer = 0
        self.playing = None

    def process(self):
        if self.playing:
            if self.playing == "TURRET_SHOOT":
                self.shoot_animation("TURRET")
            if self.playing == "HULL_SHOOT":
                self.shoot_animation("HULL")
            if self.playing == "HIT":
                self.hit_animation()

    def hit_animation(self):

        if not self.triggered:
            self.triggered = True

        if self.timer > 12:
            self.animation_finished = True
            self.recycle()
        else:
            self.timer += 1

    def set_animation(self, animation_type):
        self.playing = animation_type
        self.animation_finished = False

    def attack_animation(self):

        if self.timer > 300:
            self.animation_finished = True
            self.recycle()
        else:
            self.timer += 1

    def shoot_animation(self, location):

        if not self.triggered:
            if location == "TURRET":
                emitter = self.turret_emitter
            else:
                emitter = self.hull_emitter

            particles.DummyGunFlash(self.agent.environment, emitter, 1)
            self.triggered = True

        if self.timer > 12:
            self.animation_finished = True
            self.recycle()
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


