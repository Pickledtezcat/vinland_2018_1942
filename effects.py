import bge
import mathutils
import bgeutils
import random
import particles
import ranged_attacks
import static_dicts


class Effect(object):
    effect_type = "NONE"

    def __init__(self, environment, team, effect_id, position=None, turn_timer=0):
        self.environment = environment
        self.team = team
        self.position = position
        self.box = self.add_box()
        self.delay = 1
        self.busy = False

        self.ended = False
        self.turn_timer = turn_timer
        self.max_turns = -1
        self.map_string = self.get_map_string()

        if not effect_id:
            self.effect_id = self.set_id()
        else:
            self.effect_id = effect_id

        self.environment.effects[self.effect_id] = self

    def add_box(self):
        return None

    def get_map_string(self):
        return None

    def set_id(self):
        effect_id = "effect_{}".format(self.environment.get_new_id())
        return effect_id

    def terminate(self):
        if self.map_string:
            self.clear_map_presence()
        if self.box:
            self.box.endObject()

    def update(self):
        self.process()

    def process(self):
        pass

    def set_map_presence(self):
        self.environment.set_tile(self.position, self.map_string, self.effect_id)

    def clear_map_presence(self):
        self.environment.set_tile(self.position, self.map_string, None)

    def save_to_dict(self):
        self.terminate()
        return [self.effect_type, self.team, self.effect_id, self.position, self.turn_timer, None]

    def cycle(self):
        self.turn_timer += 1

        if self.max_turns > 0:
            if self.turn_timer >= self.max_turns:
                self.ended = True


class Objective(Effect):
    effect_type = "OBJECTIVE"

    def __init__(self, environment, team, effect_id, position, turn_timer, stats):
        self.stats = stats
        super().__init__(environment, team, effect_id, position, turn_timer)
        self.set_map_presence()
        self.trigger_flag = self.box.scene.addObject("objective_trigger_flag", self.box, 0)
        self.trigger_flag.setParent(self.box)

    def get_stat(self, stat_string):
        return self.stats[stat_string]

    def set_stat(self, stat_string, value):
        self.stats[stat_string] = value

    def get_map_string(self):
        return "objective"

    def process(self):
        # TODO check for mission success / failure

        if self.environment.environment_type != "GAMEPLAY":
            self.box.color = self.get_stat("color")
            self.trigger_flag.color = self.get_stat("trigger_color")
        else:
            self.box.visible = False
            self.trigger_flag.visible = False

    def get_mouse_over(self):
        return "\n".join(["{}: {}".format(stat_key, self.stats[stat_key]) for stat_key in self.stats])

    def update_stats(self):
        # TODO get boundary and nav points for navigation

        index = self.get_stat("index")
        objective_color = static_dicts.objective_color_dict[index]
        self.set_stat("color", objective_color.copy())

        trigger_index = self.get_stat("trigger_index")
        trigger_color = static_dicts.objective_color_dict[trigger_index]
        self.set_stat("trigger_color", trigger_color.copy())

    def add_box(self):
        box = self.environment.add_object("objective_flag")
        box.worldPosition = mathutils.Vector(self.position).to_3d()
        return box

    def save_to_dict(self):
        self.terminate()
        return [self.effect_type, self.team, self.effect_id, self.position, self.turn_timer, self.stats]


class MapPoint(Effect):
    effect_type = "MAP_POINT"

    def __init__(self, environment, team, effect_id, position, turn_timer, stats):
        self.stats = stats
        super().__init__(environment, team, effect_id, position, turn_timer)
        self.set_map_presence()

    def get_map_string(self):
        return "map_point"

    def get_stat(self, stat_string):
        return self.stats[stat_string]

    def set_stat(self, stat_string, value):
        self.stats[stat_string] = value

    def process(self):
        if self.environment.environment_type != "GAMEPLAY":
            self.box.color = self.get_stat("color")
        else:
            self.box.visible = False

    def update_stats(self):
        index = self.get_stat("index")
        objective_color = static_dicts.objective_color_dict[index]
        self.set_stat("color", objective_color)

    def add_box(self):
        if self.get_stat("point_type") == "BOUNDARY_POINT":
            visual_string = "border_flag"
        else:
            visual_string = "nav_point_flag"

        box = self.environment.add_object(visual_string)
        box.worldPosition = mathutils.Vector(self.position).to_3d()
        return box


class Mines(Effect):
    effect_type = "MINES"

    def __init__(self, environment, team, effect_id, position=None, turn_timer=0):
        super().__init__(environment, team, effect_id, position, turn_timer)

        self.set_map_presence()

    def get_map_string(self):
        return "mines"

    def add_box(self):
        box = self.environment.add_object("mines")
        box.worldPosition = mathutils.Vector(self.position).to_3d()
        return box


class Smoke(Effect):
    effect_type = "SMOKE"

    def __init__(self, environment, team, effect_id, position, turn_timer):
        smoke_tile = environment.get_tile(position)

        if not smoke_tile["smoke"]:
            super().__init__(environment, team, effect_id, position, turn_timer)

            self.environment.set_tile(self.position, "smoke", self.effect_id)
            self.set_map_presence()
            self.max_turns = 5

            self.max_target = 1.0
            self.max_size = 0.0

            self.deploy = random.uniform(0.0005, 0.0015)

            self.pulse_timer = 0.0
            self.pulsing = True

            self.process()
        else:
            # add an effect to show the explosion
            pass

    def add_box(self):
        box = self.environment.add_object("smoke")
        box.worldPosition = mathutils.Vector(self.position).to_3d()
        return box

    def get_map_string(self):
        return "smoke"

    def process(self):

        self.max_target = 1.0 - (0.18 * self.turn_timer)
        self.max_size = bgeutils.interpolate_float(self.max_size, self.max_target, 0.02)

        if self.pulsing:
            if self.pulse_timer < 1.0:
                self.pulse_timer += 0.01
            else:
                self.pulsing = False
        else:
            if self.pulse_timer > 0.0:
                self.pulse_timer -= 0.01
            else:
                self.pulsing = True

        min_size = self.max_size * 0.7

        min_size_vector = mathutils.Vector([min_size, min_size, min_size])
        max_size_vector = mathutils.Vector([self.max_size, self.max_size, self.max_size])

        self.box.localScale = max_size_vector.lerp(min_size_vector, bgeutils.smoothstep(self.pulse_timer))

    def terminate(self):
        self.environment.set_tile(self.position, "smoke", False)

        if self.box:
            self.box.endObject()


class AirSupport(Effect):
    effect_type = "GENERAL_AIR_SUPPORT"

    def __init__(self, environment, team, effect_id, position, turn_timer):

        super().__init__(environment, team, effect_id, position, turn_timer)

        self.pulse_timer = 0.0
        self.pulsing = True
        self.max_turns = 6

        self.min_size = 0.0
        self.max_size = 0.0

        self.box.localScale = [0.0, 0.0, 0.0]
        # takes effect after this number of turns
        self.delay = 1
        # used for visibility
        self.radius = 4

    def add_box(self):
        box = self.environment.add_object("aircraft_icon")
        box.worldPosition = mathutils.Vector(self.position).to_3d()
        return box

    def process(self):

        if self.pulsing:
            if self.pulse_timer < 1.0:
                self.pulse_timer += 0.01
            else:
                self.pulsing = False
        else:
            if self.pulse_timer > 0.0:
                self.pulse_timer -= 0.01
            else:
                self.pulsing = True

        if self.turn_timer > self.max_turns - 2:
            self.min_size -= 0.01
            self.max_size -= 0.01
        else:
            self.min_size = min(0.7, self.min_size + 0.01)
            self.max_size = min(1.0, self.max_size + 0.01)

        min_size_vector = mathutils.Vector([self.min_size, self.min_size, self.min_size])
        max_size_vector = mathutils.Vector([self.max_size, self.max_size, self.max_size])

        self.box.localScale = max_size_vector.lerp(min_size_vector, bgeutils.smoothstep(self.pulse_timer))


class SpotterPlane(AirSupport):
    effect_type = "SPOTTER_PLANE"

    def __init__(self, environment, team, effect_id, position, turn_timer):
        super().__init__(environment, team, effect_id, position, turn_timer)

        self.max_turns = 8
        self.delay = 2
        self.radius = 4

    def add_box(self):
        box = self.environment.add_object("aircraft_icon")
        box.worldPosition = mathutils.Vector(self.position).to_3d()
        return box


class RangedAttack(Effect):
    def __init__(self, environment, team, effect_id, position, turn_timer, owner_id, action_id, scatter):
        super().__init__(environment, team, effect_id, position, turn_timer)
        self.max_turns = 0

        self.owner_id = owner_id
        self.action_id = action_id

        self.scatter = scatter
        self.special = ["TRACKS"]

        self.shells = []
        self.launch_projectiles()

    def process(self):
        super().process()

        if len(self.shells) > 0:
            self.busy = True
            next_generation = []

            for shell in self.shells:
                if not shell.update():
                    next_generation.append(shell)

            self.shells = next_generation
        else:
            self.busy = False
            self.ended = True

    def launch_projectiles(self):

        owner = self.environment.agents[self.owner_id]
        action = owner.get_stat("action_dict")[self.action_id]

        weapon = action["weapon_stats"]
        power = weapon["damage"]
        target_position = self.position
        scatter = self.scatter
        accuracy = weapon["accuracy"]
        special = self.special
        effect = action["effect"]

        smoke = False
        if "SMOKE" in effect:
            special.append("SMOKE")
            smoke = True

        if "GRENADE" in effect:
            special.append("GRENADE")

        if "ROCKET" in effect:
            special.append("ROCKET")

        location = action["weapon_location"]

        if "turret" in location:
            adder = owner.model.turret_emitter
        elif "hull" in location:
            adder = owner.model.turret_emitter
        else:
            adder = owner.model.model

        contents = [accuracy, power, target_position, scatter, special]
        projectile_data = ranged_attacks.ranged_attack(self.environment, contents)

        if projectile_data:
            hit_position = projectile_data["hit_position"]
            hit_list = projectile_data["hit_list"]

            # TODO add other shell types. Rockets, grenades and so on.
            if "GRENADE" in special:
                shell = ranged_attacks.GrenadeShell(self.environment, hit_position, self, hit_list, adder, smoke,
                                                    self.team)
            elif "ROCKET" in special:
                shell = ranged_attacks.RocketShell(self.environment, hit_position, self, hit_list, adder, smoke,
                                                   self.team)

            else:
                shell = ranged_attacks.ArtilleryShell(self.environment, hit_position, self, hit_list, adder, smoke,
                                                      self.team)

            self.shells.append(shell)

        else:
            self.ended = True


class AirStrike(AirSupport):
    effect_type = "AIR_STRIKE"

    def __init__(self, environment, team, effect_id, position, turn_timer):
        super().__init__(environment, team, effect_id, position, turn_timer)

        self.max_turns = 2
        self.triggered = False

        self.delay = 1
        self.power = 25
        self.shots = 4
        self.scatter = 4
        self.radius = 2
        self.bombs = []

    def cycle(self):
        super().cycle()

        if self.turn_timer == self.delay:
            if not self.triggered:
                self.triggered = True
                self.drop_bombs()

    def process(self):
        super().process()

        if len(self.bombs) > 0:
            self.busy = True
            next_generation = []

            for bomb in self.bombs:
                if not bomb.update():
                    next_generation.append(bomb)

            self.bombs = next_generation
        else:
            self.busy = False

    def drop_bombs(self):

        shots = self.shots
        power = self.power
        target_position = self.position
        scatter = self.scatter
        accuracy = 3
        special = []

        for s in range(shots):

            contents = [accuracy, power, target_position, scatter, special]
            projectile_data = ranged_attacks.ranged_attack(self.environment, contents)

            if projectile_data:
                hit_position = projectile_data["hit_position"]
                hit_list = projectile_data["hit_list"]
                bomb = ranged_attacks.Bomb(self.environment, hit_position, self, hit_list)
                self.bombs.append(bomb)
