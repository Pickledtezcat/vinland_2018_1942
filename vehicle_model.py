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
        self.prone = False
        self.buttoned_up = False

        self.turret = bgeutils.get_ob("turret", self.model.children)
        self.hull_emitter = bgeutils.get_ob("gun_emitter", self.model.children)
        self.turret_emitter = self.hull_emitter
        if self.turret:
            self.turret_emitter = bgeutils.get_ob("gun_emitter", self.turret.children)

        self.commander = bgeutils.get_ob("commander", self.model.childrenRecursive)

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

        if self.agent.has_effect("DEAD"):
            self.model.setVisible(False, True)
        else:
            if self.playing:
                if self.playing == "TURRET_SHOOT":
                    self.shoot_animation("TURRET")
                if self.playing == "HULL_SHOOT":
                    self.shoot_animation("HULL")
                if self.playing == "HIT":
                    self.hit_animation()

            self.background_animation()

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

    def background_animation(self):
        if self.agent.has_effect("LOADED"):
            self.model.setVisible(False, True)
        else:
            self.model.setVisible(True, True)

        if self.agent.has_effect("BUTTONED_UP"):
            self.commander.visible = False
        else:
            self.commander.visible = True


class InfantryModel(AgentModel):
    def __init__(self, agent, adder):
        super().__init__(agent, adder)

    def add_model(self):
        number = self.agent.get_stat("number")
        model_string = "squad_{}".format(number)

        model = self.adder.scene.addObject(model_string, self.adder, 0)
        model.setParent(self.adder)

        return model

    def background_animation(self):

        number = self.agent.get_stat("number")
        model_string = "squad_{}".format(number)
        self.model.replaceMesh(model_string)

        if self.agent.has_effect("LOADED"):
            self.model.setVisible(False, True)
        else:
            self.model.setVisible(True, True)

        number = self.agent.get_stat("number")

        if self.agent.has_effect("PRONE"):
            if not self.prone:
                self.prone = True
                self.model.replaceMesh("squad_{}_prone".format(number))

        else:
            if self.prone:
                self.prone = False
                self.model.replaceMesh("squad_{}".format(number))
