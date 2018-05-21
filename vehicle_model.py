import bge
import bgeutils
import mathutils
import particles
import static_dicts


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
        self.objective_flag = self.add_objective_flag()

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

    def add_objective_flag(self):

        if self.environment.environment_type != "GAMEPLAY":
            objective_flag = self.adder.scene.addObject("unit_flag", self.adder, 0)
            return objective_flag

        return None

    def update(self):
        self.update_objective_flag()
        self.process()
        return not self.animation_finished

    def update_objective_flag(self):
        if self.objective_flag:
            color = static_dicts.objective_color_dict[self.agent.get_stat("objective_index")]
            self.objective_flag.color = color
            self.objective_flag.worldPosition = self.model.worldPosition.copy()

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
        self.number = self.agent.get_stat("number")

    def add_model(self):
        number = self.agent.get_stat("number")
        model_string = "squad_{}".format(number)

        model = self.adder.scene.addObject(model_string, self.adder, 0)
        model.setParent(self.adder)

        return model

    def set_mesh(self):
        number = self.agent.get_stat("number")
        if self.prone:
            prone_string = "_prone"
        else:
            prone_string = ""

        self.model.replaceMesh("squad_{}{}".format(number, prone_string))

    def background_animation(self):

        if self.agent.has_effect("LOADED"):
            self.model.setVisible(False, True)
        else:
            self.model.setVisible(True, True)

        number = self.agent.get_stat("number")

        if self.number != number:
            self.number = number
            self.set_mesh()
            particles.DebugText(self.environment, "MAN DOWN!!", self.model.worldPosition.copy())

        if self.agent.has_effect("PRONE"):
            if not self.prone:
                self.prone = True
                self.set_mesh()
                particles.DebugText(self.environment, "GOING PRONE", self.model.worldPosition.copy())

        else:
            if self.prone:
                self.prone = False
                self.set_mesh()
                particles.DebugText(self.environment, "GETTING UP", self.model.worldPosition.copy())
