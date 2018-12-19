import bge
import bgeutils
import mathutils
import particles
import static_dicts
import infantry_dummies
import random


class GunRecoil(object):

    def __init__(self, animated_object):
        self.animated_object = animated_object
        self.start = animated_object.localPosition.copy()
        self.end = self.start.copy()
        self.end.y -= 0.03

    def set_animation(self, animation_count):
        self.animated_object.localPosition = self.start.lerp(self.end, bgeutils.smoothstep(animation_count))


class AnimatedLeg(object):

    def __init__(self, animated_object):
        self.animated_object = animated_object
        self.start = animated_object.localOrientation.copy()
        self.end = self.start.copy()

        z_rot = self.animated_object.get("rot", 0.0)
        eul = mathutils.Euler((0.2, 0.0, z_rot), 'XYZ')
        self.end.rotate(eul)

    def set_animation(self, animation_count):
        self.animated_object.localOrientation = self.start.lerp(self.end, bgeutils.smoothstep(animation_count))


class GunMount(object):

    def __init__(self, animated_object):
        self.animated_object = animated_object
        self.start = animated_object.localOrientation.copy()
        self.end = self.start.copy()

        x_rot = self.animated_object.get("rot", 0.0)
        eul = mathutils.Euler((x_rot, 0.0, 0.0), 'XYZ')
        self.end.rotate(eul)

    def set_animation(self, animation_count):
        self.animated_object.localOrientation = self.start.lerp(self.end, bgeutils.smoothstep(animation_count))


class AgentModel(object):

    def __init__(self, agent):
        self.adder = None
        self.agent = agent
        self.environment = self.agent.environment

        self.model = self.add_model()
        self.currently_visible = True
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

        self.turret = bgeutils.get_ob("turret", self.model.childrenRecursive)

        hull_emitters = bgeutils.get_ob_list("hull_emitter", self.model.childrenRecursive)
        turret_emitters = bgeutils.get_ob_list("turret_emitter", self.model.childrenRecursive)

        self.hull_primary = bgeutils.get_ob_list("primary", hull_emitters)
        self.hull_secondary = bgeutils.get_ob_list("secondary", hull_emitters)

        self.turret_primary = bgeutils.get_ob_list("primary", turret_emitters)
        self.turret_secondary = bgeutils.get_ob_list("secondary", turret_emitters)

        self.emit = 0
        self.commander = bgeutils.get_ob("commander", self.model.childrenRecursive)
        self.crewmen = bgeutils.get_ob_list("crewman", turret_emitters)
        self.wheels = bgeutils.get_ob_list("wheels", turret_emitters)

        legs = bgeutils.get_ob_list("leg", self.model.childrenRecursive)
        self.legs = [AnimatedLeg(leg) for leg in legs]

        aa_mounts = bgeutils.get_ob_list("aa_mount", self.model.childrenRecursive)
        self.aa_mounts = [GunMount(gun) for gun in aa_mounts]

        gun_barrels = bgeutils.get_ob_list("gun_barrel", self.model.childrenRecursive)
        self.gun_barrels = [GunMount(gun) for gun in gun_barrels]

        self.deployed = 0.0
        self.ranged = 0.0

    def add_model(self):
        self.adder = self.agent.tilt_hook

        model = self.adder.scene.addObject(self.agent.load_key, self.adder, 0)
        model.setParent(self.adder)

        return model

    def add_objective_flag(self):
        objective_flag = self.environment.add_object("unit_flag")
        objective_flag.worldPosition = self.agent.box.worldPosition.copy()

        if self.environment.environment_type == "GAMEPLAY":
            objective_flag.visible = False

        return objective_flag

    def update(self):
        self.currently_visible = self.check_currently_visible()
        self.process()
        self.update_objective_flag()

        deployed = self.set_deployed()

        if not deployed:
            return True

        if not self.animation_finished:
            return True

        return False

    def set_deployed(self):
        return True

    def animate_movement(self):

        speed = self.agent.movement.throttle
        speed *= 0.02

        if self.model.color[0] >= 4.0:
            self.model.color[0] = 0

        self.model.color[0] += speed

        for wheel in self.wheels:
            wheel.applyRotation([-speed, 0.0, 0.0], True)

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

        if self.playing:
            if self.playing == "SHOOTING":
                self.shoot_animation()
            elif self.playing == "MOVEMENT":
                self.movement_animation()
            elif self.playing == "HIT":
                self.hit_animation()

        self.background_animation()

    def movement_animation(self):

        if not self.triggered:
            chassis_type = "CAR"
            drive_type = self.agent.get_stat("drive_type")
            size = self.agent.get_stat("size")

            if drive_type == "GUN_CARRIAGE":
                chassis_type = "GUN"
            elif drive_type == "TRACKED":
                chassis_type = "TANK"

            elif size > 4:
                chassis_type = "TRUCK"

            if self.agent.get_stat("team") == 2:
                team = "HRE"
            else:
                team = "VIN"

            sound_type = "MOVE_{}_{}".format(chassis_type, team)
            sound_pitch = random.uniform(0.8, 1.3)
            position = self.model.worldPosition.copy()
            particles.SoundDummy(self.environment, position, sound_type, volume=2.0, pitch=sound_pitch)

            self.triggered = True

        if self.timer > 60:
            self.animation_finished = True
            self.recycle()
        else:
            self.timer += 1

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
            if "primary" in location:
                emitters = self.turret_primary
            else:
                emitters = self.turret_secondary
        else:
            if "primary" in location:
                emitters = self.hull_primary
            else:
                emitters = self.hull_secondary

        if self.emit >= len(emitters):
            self.emit = 0

        if emitters:
            emitter = emitters[self.emit]
            self.emit += 1

            return emitter

        return None

    def shoot_animation(self):

        if not self.triggered:
            action = self.action
            location = action["weapon_location"]
            weapon_stats = action["weapon_stats"]
            power = weapon_stats["power"]

            emitter = self.get_emitter(location)
            if emitter:

                if "ROCKET" in action["effect"]:
                    particles.RocketFlash(self.environment, emitter, power)
                else:
                    particles.MuzzleBlast(self.environment, emitter, power)

            else:
                print("NO EMITTER: {}".format(location))

            self.triggered = True

        if self.timer > 6:
            self.animation_finished = True
            self.recycle()
        else:
            self.timer += 1

    def check_currently_visible(self):

        if not self.environment.player_visibility:
            return True

        position = self.agent.box.worldPosition.copy()
        tile_position = bgeutils.position_to_location(position)
        visible = self.environment.player_visibility.lit(*tile_position)
        if visible > 0:
            return True

        return False

    def terminate(self):
        self.model.endObject()
        self.objective_flag.endObject()

    def background_animation(self):
        pass


class VehicleModel(AgentModel):
    def __init__(self, agent):
        super().__init__(agent)
        self.tilt = 0.0
        self.damping = 0.03
        self.recoil_damping = 0.03
        self.recoil = mathutils.Vector([0.0, 0.0, 0.0])
        self.dirt_timer = 0.0

    def set_deployed(self):

        if self.agent.has_effect("DEAD"):
            return True

        current_action = self.agent.get_current_action()
        ranged = False

        if current_action["action_type"] != "WEAPON":
            ranged = True
        else:
            if current_action["target"] == "MAP":
                ranged = True

        if self.agent.movement.done:
            self.deployed = min(1.0, self.deployed + 0.03)
        else:
            ranged = True
            self.deployed = max(0.0, self.deployed - 0.03)

        if ranged:
            self.ranged = min(1.0, self.ranged + 0.03)
        else:
            self.ranged = max(0.0, self.ranged - 0.03)

        for leg in self.legs:
            leg.set_animation(self.deployed)

        for gun in self.gun_barrels:
            gun.set_animation(self.ranged)

        for aa_gun in self.aa_mounts:
            aa_gun.set_animation(self.ranged)

        if self.deployed >= 1.0:
            if ranged and self.ranged >= 1.0:
                return True
            if not ranged and self.ranged <= 0:
                return True

        return False

    def background_animation(self):

        if self.agent.has_effect("DEAD"):
            self.model.setVisible(False, True)
        else:
            if self.agent.has_effect("LOADED"):
                self.model.setVisible(False, True)
            else:
                self.model.setVisible(True, True)

            if self.commander:
                commander_visible = True

                if self.agent.has_effect("DYING"):
                    commander_visible = False

                if self.agent.has_effect("BUTTONED_UP"):
                    commander_visible = False

                if self.agent.has_effect("BAILED_OUT"):
                    commander_visible = False

                if commander_visible:
                    self.commander.visible = True
                else:
                    self.commander.visible = False

            if self.currently_visible:
                self.set_recoil()
                self.dirt_trail()
                self.animate_movement()

    def shoot_animation(self):

        if not self.triggered:
            action = self.action
            location = action["weapon_location"]
            weapon_stats = action["weapon_stats"]
            power = weapon_stats["power"]
            if weapon_stats["shots"] > 1:
                self.animation_duration = 6
            else:
                self.animation_duration = 24

            emitter = self.get_emitter(location)
            if emitter:

                if "ROCKET" in action["effect"]:
                    particles.RocketFlash(self.environment, emitter, power)
                else:
                    particles.MuzzleBlast(self.environment, emitter, power)

            else:
                print("NO EMITTER: {}".format(location))

            recoil = power * 0.05
            recoil_vector = mathutils.Vector([0.0, -recoil, 0.0])
            recoil_vector.rotate(self.agent.agent_hook.worldOrientation.copy())

            self.recoil += recoil_vector
            self.triggered = True

        if self.timer > self.animation_duration:
            self.animation_finished = True
            self.recycle()
        else:
            self.timer += 1

    def set_recoil(self):

        self.recoil = self.recoil.lerp(mathutils.Vector([0.0, 0.0, 0.0]), self.recoil_damping)
        if self.recoil.length > 0.25:
            self.recoil *= 0.85

        throttle = self.agent.movement.throttle
        throttle_target = self.agent.movement.throttle_target
        throttle_difference = (throttle - throttle_target)
        max_tilt = 0.25
        tilt = max(-max_tilt, min(max_tilt, throttle_difference))

        self.tilt = bgeutils.interpolate_float(self.tilt, tilt, self.damping)

        y_vector = self.agent.agent_hook.getAxisVect([0.0, 1.0, 0.0])

        tilt_vector = mathutils.Vector([0.0, self.tilt, 1.0]).normalized()
        tilt_vector.rotate(self.agent.agent_hook.worldOrientation.copy())

        base_z = self.agent.tilt_hook.getAxisVect([0.0, 0.0, 1.0])
        z_vector = self.recoil.copy() + tilt_vector

        mixed_z = base_z.lerp(z_vector, self.damping * 0.5)

        self.agent.tilt_hook.alignAxisToVect(y_vector, 1, 1.0)
        self.agent.tilt_hook.alignAxisToVect(mixed_z, 2, 1.0)

    def dirt_trail(self):
        if self.agent.movement.throttle_target > 0.01:
            throttle_target = self.agent.movement.throttle_target
            size = 0.5 + (throttle_target * 0.5)
            position = self.agent.box.worldPosition.copy()
            tile_position = bgeutils.position_to_location(position)

            self.dirt_timer += random.uniform(0.05, 0.15)
            if self.dirt_timer > 1.0:
                self.dirt_timer = 0.0
                tile = self.environment.get_tile(tile_position)
                if tile:
                    ground_type = "SOFT"
                    if tile["softness"] < 2 or tile["road"]:
                        ground_type = "HARD"

                    if tile["softness"] > 2 or tile["bushes"]:
                        size *= 1.5

                    particles.DirtTrail(self.environment, position, size, ground_type)
        else:
            self.dirt_timer = 0.0


class ArtilleryModel(AgentModel):
    def __init__(self, agent):
        super().__init__(agent)
        self.squad = infantry_dummies.InfantrySquad(self)
        self.tilt = 0.0
        self.damping = 0.03
        self.recoil_damping = 0.03
        self.recoil = mathutils.Vector([0.0, 0.0, 0.0])

    def add_model(self):
        self.adder = self.agent.tilt_hook
        model = self.adder.scene.addObject(self.agent.load_key, self.adder, 0)
        model.setParent(self.adder)

        return model

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

        self.background_animation()

    def set_deployed(self):

        if self.agent.has_effect("DEAD"):
            return True

        current_action = self.agent.get_current_action()
        ranged = False

        if current_action["action_type"] != "WEAPON":
            ranged = True
        else:
            if current_action["target"] == "MAP":
                ranged = True

        if self.agent.movement.done:
            self.deployed = min(1.0, self.deployed + 0.03)
        else:
            ranged = True
            self.deployed = max(0.0, self.deployed - 0.03)

        if ranged:
            self.ranged = min(1.0, self.ranged + 0.03)
        else:
            self.ranged = max(0.0, self.ranged - 0.03)

        for leg in self.legs:
            leg.set_animation(self.deployed)

        for gun in self.gun_barrels:
            gun.set_animation(self.ranged)

        for aa_gun in self.aa_mounts:
            aa_gun.set_animation(self.ranged)

        if self.deployed >= 1.0:
            return True

        return False

    def shooting(self):
        if not self.triggered:

            action = self.action
            location = action["weapon_location"]
            weapon_stats = action["weapon_stats"]
            power = weapon_stats["power"]
            if weapon_stats["shots"] > 1:
                self.animation_duration = 6
            else:
                self.animation_duration = 24

            emitter = self.get_emitter(location)
            if emitter:

                if "ROCKET" in action["effect"]:
                    particles.RocketFlash(self.environment, emitter, power)
                else:
                    particles.MuzzleBlast(self.environment, emitter, power)
            else:
                print("NO EMITTER: {}".format(location))

            recoil = power * 0.05
            recoil_vector = mathutils.Vector([0.0, -recoil, 0.0])
            recoil_vector.rotate(self.agent.agent_hook.worldOrientation.copy())

            self.recoil += recoil_vector
            self.triggered = True

        if self.timer > self.animation_duration:
            self.animation_finished = True
            self.recycle()
        else:
            self.timer += 1

    def set_recoil(self):
        self.recoil = self.recoil.lerp(mathutils.Vector([0.0, 0.0, 0.0]), self.recoil_damping)
        if self.recoil.length > 0.25:
            self.recoil *= 0.85

        throttle = self.agent.movement.throttle
        throttle_target = self.agent.movement.throttle_target
        throttle_difference = (throttle - throttle_target)
        max_tilt = 0.25
        tilt = max(-max_tilt, min(max_tilt, throttle_difference))

        self.tilt = bgeutils.interpolate_float(self.tilt, tilt, self.damping)

        y_vector = self.agent.agent_hook.getAxisVect([0.0, 1.0, 0.0])

        tilt_vector = mathutils.Vector([0.0, self.tilt, 1.0]).normalized()
        tilt_vector.rotate(self.agent.agent_hook.worldOrientation.copy())

        base_z = self.agent.tilt_hook.getAxisVect([0.0, 0.0, 1.0])
        z_vector = self.recoil.copy() + tilt_vector

        mixed_z = base_z.lerp(z_vector, self.damping * 0.5)

        self.agent.tilt_hook.alignAxisToVect(y_vector, 1, 1.0)
        self.agent.tilt_hook.alignAxisToVect(mixed_z, 2, 1.0)

    def fidget_animation(self):
        if not self.triggered:
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

        if self.agent.has_effect("DEAD"):
            self.model.setVisible(False, True)
        else:
            if self.currently_visible:
                self.set_recoil()
                self.animate_movement()

            self.squad.update()

    def terminate(self):
        self.model.endObject()
        self.objective_flag.endObject()
        self.squad.terminate()


class InfantryModel(AgentModel):
    def __init__(self, agent):
        super().__init__(agent)
        self.paradrop_object = None
        self.squad = infantry_dummies.InfantrySquad(self)

    def add_model(self):
        self.adder = self.agent.box
        model = self.environment.add_object("dummy_squad")
        model.worldPosition = self.adder.worldPosition.copy()
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
        if self.agent.get_stat("number") > 2:
            sound = "MOVE_MARCH_2"
        else:
            sound = "MOVE_MARCH_1"

        sound_pitch = random.uniform(0.8, 1.3)
        position = self.model.worldPosition.copy()
        particles.SoundDummy(self.environment, position, sound, volume=1.0, pitch=sound_pitch)

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
