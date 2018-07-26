import bge
import bgeutils
import mathutils
import particles
import static_dicts
import infantry_dummies


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
        self.action = None
        self.animation_duration = 12
        self.target_location = None
        self.prone = False
        self.buttoned_up = False
        self.objective_flag = self.add_objective_flag()

        self.turret = bgeutils.get_ob("turret", self.model.children)
        self.hull_emitters = bgeutils.get_ob_list("gun_emitter", self.model.children)
        self.turret_emitters = self.hull_emitters
        if self.turret:
            self.turret_emitters = bgeutils.get_ob_list("gun_emitter", self.turret.children)

        self.emit = 0
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
            self.objective_flag.worldPosition = self.agent.box.worldPosition.copy()

    def recycle(self):
        self.triggered = False
        self.target_location = None
        self.action = None
        self.timer = 0
        self.playing = None

    def process(self):
        if self.agent.has_effect("DEAD"):
            self.model.setVisible(False, True)
        else:
            if self.playing:
                if self.playing == "SHOOTING":
                    self.shoot_animation()
                elif self.playing == "MOVEMENT":
                    self.movement_animation()
                elif self.playing == "HIT":
                    self.hit_animation()

            self.background_animation()

    def movement_animation(self):
        self.animation_finished = True
        self.recycle()

    def hit_animation(self):

        if not self.triggered:
            self.triggered = True

        if self.timer > 12:
            self.animation_finished = True
            self.recycle()
        else:
            self.timer += 1

    def set_animation(self, animation_type, action=None):
        if not self.playing:
            if action:
                self.action = action
            self.playing = animation_type
            self.animation_finished = False

    def get_emitter(self, location):
        if "turret" in location:
            emitters = self.turret_emitters
        else:
            emitters = self.hull_emitters

        if self.emit >= len(emitters):
            self.emit = 0

        emitter = emitters[self.emit]
        self.emit += 1

        return emitter

    def shoot_animation(self):

        if not self.triggered:
            action = self.action
            location = action["weapon_location"]
            weapon_stats = action["weapon_stats"]
            power = weapon_stats["power"]

            emitter = self.get_emitter(location)

            if "ROCKET" in action["effect"]:
                particles.RocketFlash(self.environment, emitter, power)
            else:
                particles.MuzzleBlast(self.environment, emitter, power)

            self.triggered = True

        if self.timer > 6:
            self.animation_finished = True
            self.recycle()
        else:
            self.timer += 1

    def terminate(self):
        self.model.endObject()
        self.objective_flag.endObject()

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
        self.paradrop_object = None
        self.squad = infantry_dummies.InfantrySquad(self)

    def add_model(self):
        model = self.adder.scene.addObject("dummy_squad", self.adder, 0)
        model.setParent(self.adder)

        return model

    def paradrop_animation(self):
        if not self.paradrop_object:
            self.paradrop_object = self.environment.add_object("paradrop_icon")
            self.paradrop_object.worldPosition = self.model.worldPosition.copy()
            self.paradrop_object.worldPosition.z = 10.0

        else:
            if self.paradrop_object.worldPosition.z < 0.5:
                self.model.worldPosition = self.adder.worldPosition.copy()
                self.paradrop_object.endObject()
                self.animation_finished = True
                self.recycle()
            else:
                self.model.worldPosition = self.paradrop_object.worldPosition
                self.paradrop_object.worldPosition.z -= 0.03

    def process(self):
        if self.playing:
            if self.playing == "SHOOTING":
                self.shooting()
            elif self.playing == "FIDGET":
                self.fidget_animation()
            elif self.playing == "MOVEMENT":
                self.movement_animation()
            elif self.playing == "HIT":
                self.infantry_animation()
            elif self.playing == "PARADROP":
                self.paradrop_animation()

        self.background_animation()

    def movement_animation(self):
        self.squad.get_formation()
        self.animation_finished = True
        self.recycle()

    def shooting(self):
        action_name = self.action["action_name"]

        rapid_fire = ["ASSAULT_RIFLES",
                      "SMG",
                      "SUPPORT_FIRE",
                      "SIDE_ARMS",
                      "HEAVY_SUPPORT_FIRE"]

        if not self.triggered:
            if action_name in rapid_fire:
                self.animation_duration = 8
                self.squad.rapid = True
            else:
                self.animation_duration = 30
                self.squad.rapid = False

            self.squad.shooting = True
            self.triggered = True

        if self.timer > self.animation_duration:
            self.animation_finished = True
            self.recycle()
        else:
            self.timer += 1

    def fidget_animation(self):
        if not self.triggered:
            self.squad.get_formation()
            self.animation_duration = 24
            self.triggered = True

        if self.timer > self.animation_duration:
            self.animation_finished = True
            self.recycle()
        else:
            self.timer += 1

    def infantry_animation(self):

        if not self.triggered:
            self.animation_duration = 12
            self.triggered = True

        if self.timer > self.animation_duration:
            self.animation_finished = True
            self.recycle()
        else:
            self.timer += 1

    def recycle(self):
        self.triggered = False
        self.squad.shooting = False
        self.target_location = None
        self.squad.rapid = False
        self.timer = 0
        self.action = None
        self.playing = None

    def background_animation(self):
        self.squad.update()

    def terminate(self):
        self.model.endObject()
        self.objective_flag.endObject()
        self.squad.terminate()