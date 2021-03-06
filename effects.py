import bge
import mathutils
import bgeutils
import random
import particles
import ranged_attacks
import static_dicts
from objective_data import *


class Effect(object):
    effect_type = "NONE"

    def __init__(self, environment, team, effect_id, position=None, turn_timer=0):
        self.environment = environment
        self.team = team
        self.position = position
        self.box = self.add_box()
        self.delay = 1
        self.busy = False
        self.check_visibility = False
        self.anti_air_target = False

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

    def get_objective_id(self):
        return 9

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
        return [self.effect_type, self.team, self.effect_id, self.position, self.turn_timer, None, None]

    def apply_anti_air(self, agent_key, action_key):
        return False

    def cycle(self):
        self.turn_timer += 1

        if self.max_turns > 0:
            if self.turn_timer >= self.max_turns:
                self.ended = True


class Reveal(Effect):
    effect_type = "REVEAL"

    def __init__(self, environment, team, effect_id, position=None, turn_timer=0):
        super().__init__(environment, team, effect_id, position, turn_timer)

        self.check_visibility = True
        self.max_turns = 1
        self.radius = 1


class Objective(Effect):
    effect_type = "OBJECTIVE"

    def __init__(self, environment, team, effect_id, position, turn_timer, stats, flag):

        self.objective_flag = flag
        if not stats:
            self.stats = self.get_stats()
        else:
            self.stats = stats

        super().__init__(environment, team, effect_id, position, turn_timer)

        self.set_map_presence()
        self.trigger_flag = self.box.scene.addObject("objective_trigger_flag", self.box, 0)
        self.trigger_flag.setParent(self.box)
        self.objective_data = self.get_objective_data()

    def get_stat(self, stat_string):
        return self.stats[stat_string]

    def set_stat(self, stat_string, value):
        self.stats[stat_string] = value

    def get_map_string(self):
        return "objective"

    def get_objective_id(self):
        objective_id = self.get_stat("index")
        return objective_id

    def get_stats(self):

        objective_dict = {"objective_flag": self.objective_flag,
                          "max_turns": -1,
                          "status": "ACTIVE",
                          "index": 9,
                          "trigger_index": 9,
                          "color": [0.0, 0.0, 0.0, 1.0],
                          "trigger_color": [0.0, 0.0, 0.0, 1.0],
                          "HIDDEN_TIME_LIMIT": False,
                          "HIDDEN_OBJECTIVE": False}

        return objective_dict

    def get_objective_data(self):
        objective_list = ["ATTACK",
                          "DEFEND",
                          "SALVAGE",
                          "ESCORT",
                          "DESTROY",
                          "AMBUSH",
                          "CAPTURE",
                          "SEARCH",
                          "RESERVES",
                          "CAVALRY",
                          "RETREAT",
                          "CUT_OFF_RETREAT",
                          "MINIMAL_CASUALTIES",
                          "NO_AIR_SUPPORT",
                          "CAPTURE_SUPPLIES",
                          "CLEAN UP",
                          "SURVIVAL",
                          "MINES"]

        finished_objetives = []

        objective_dict = {"ATTACK": "AttackObjective"}

        if self.objective_flag in objective_dict:
            behavior_class = objective_dict[self.objective_flag]
        else:
            behavior_class = "ATTACK"

        return globals()[behavior_class](self)

    def process(self):

        if self.environment.environment_type != "GAMEPLAY":
            self.box.color = self.get_stat("color")
            self.trigger_flag.color = self.get_stat("trigger_color")
        else:
            # TODO set up flag visibility and display
            self.objective_data.update()
            self.box.visible = False
            self.trigger_flag.visible = False

    def get_mouse_over(self):
        return "\n".join(["{}: {}".format(stat_key, self.stats[stat_key]) for stat_key in self.stats])

    def check_triggered(self):
        trigger = self.get_stat("trigger_index")
        if trigger != 9:
            for effect_key in self.environment.effects:
                effect = self.environment.effects[effect_key]
                if effect.effect_type == "OBJECTIVE":
                    if effect.get_stat("index") == trigger:
                        untriggered = ["FAILED", "ACTIVE"]
                        if effect.get_stat("status") in untriggered:
                            return False

        return True

    def update_stats(self):
        # TODO get boundary and nav points for navigation

        status = ["INACTIVE", "ACTIVE", "COMPLETE", "FAILED"]

        if not self.check_triggered():
            self.set_stat("status", "INACTIVE")

        index = self.get_stat("index")
        if index not in static_dicts.objective_color_dict:
            index = 9

        objective_color = static_dicts.objective_color_dict[index]
        self.set_stat("color", objective_color.copy())

        trigger_index = self.get_stat("trigger_index")
        if trigger_index not in static_dicts.objective_color_dict:
            trigger_index = 9

        trigger_color = static_dicts.objective_color_dict[trigger_index]
        self.set_stat("trigger_color", trigger_color.copy())

    def add_box(self):
        box = self.environment.add_object("objective_flag")
        box.worldPosition = mathutils.Vector(self.position).to_3d()
        return box

    def save_to_dict(self):
        self.terminate()
        return [self.effect_type, self.team, self.effect_id, self.position, self.turn_timer, self.stats,
                self.objective_flag]

    def cycle(self):
        self.objective_data.cycle()


class MapPoint(Effect):
    effect_type = "MAP_POINT"

    def __init__(self, environment, team, effect_id, position, turn_timer, stats, flag):
        self.map_flag = flag
        self.stats = stats
        super().__init__(environment, team, effect_id, position, turn_timer)
        self.set_map_presence()

    def get_map_string(self):
        return "map_point"

    def get_stat(self, stat_string):
        return self.stats[stat_string]

    def set_stat(self, stat_string, value):
        self.stats[stat_string] = value

    def get_stats(self):

        map_dict = {"point_type": self.map_flag,
                    "visiting": [],
                    "visited": [],
                    "index": 9,
                    "color": [0.0, 0.0, 0.0, 1.0]}

        return map_dict

    def process(self):
        if self.environment.environment_type != "GAMEPLAY":
            self.box.color = self.get_stat("color")
        else:
            self.box.visible = False

    def clear_visited(self, removing_agent):
        visiting = self.get_stat("visiting")
        visited = self.get_stat("visited")

        visiting = [agent_id for agent_id in visiting if agent_id != removing_agent]
        visited = [agent_id for agent_id in visited if agent_id != removing_agent]

        self.set_stat("visiting", visiting)
        self.set_stat("visited", visited)

    def add_visiting(self, adding_agent):
        visiting = self.get_stat("visiting")
        visiting.append(adding_agent)
        self.set_stat("visiting", visiting)

    def add_visited(self, adding_agent):
        visited = self.get_stat("visited")
        visited.append(adding_agent)
        self.set_stat("visited", visited)

    def update_stats(self):
        index = self.get_stat("index")
        if index in static_dicts.objective_color_dict:
            index = 9

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

    def save_to_dict(self):
        self.terminate()
        return [self.effect_type, self.team, self.effect_id, self.position, self.turn_timer, self.stats, self.map_flag]


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
        self.effect = None

        if not smoke_tile["smoke"]:
            super().__init__(environment, team, effect_id, position, turn_timer)

            self.environment.set_tile(self.position, "smoke", self.effect_id)
            self.set_map_presence()
            self.max_turns = 5
            self.process()
            self.effect = particles.TowerSmoke(self.environment, self.box.worldPosition)
        else:
            # add an effect to show the explosion
            pass

    def add_box(self):
        box = self.environment.add_object("dummy_object")
        box.worldPosition = mathutils.Vector(self.position).to_3d()
        return box

    def get_map_string(self):
        return "smoke"

    def process(self):
        if self.effect:
            if self.environment.player_visibility:
                visible = False

                x, y = self.position
                lit = self.environment.player_visibility.lit(x, y)
                if lit > 0:
                    visible = True

                if visible:
                    self.effect.active = True
                else:
                    self.effect.active = False

    def terminate(self):
        self.environment.set_tile(self.position, "smoke", False)

        if self.box:
            self.box.endObject()

        if self.effect:
            self.effect.shut_down()


class AirSupport(Effect):
    effect_type = "GENERAL_AIR_SUPPORT"

    def __init__(self, environment, team, effect_id, position, turn_timer):

        super().__init__(environment, team, effect_id, position, turn_timer)

        self.check_visibility = True
        self.pulse_timer = 0.0
        self.pulsing = True
        self.max_turns = 6
        self.anti_air_target = True
        self.armor = 0

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

    def apply_anti_air(self, agent_key, action_key):

        aa_agent = self.environment.agents[agent_key]
        main_gun = aa_agent.get_stat("action_dict")[action_key]

        if main_gun:

            details = main_gun["weapon_stats"]
            shots = details["shots"]
            power = details["power"]
            accuracy = details["accuracy"]

            origin = aa_agent.get_stat("position")
            target = self.position

            target_vector = mathutils.Vector(target) - mathutils.Vector(origin)
            reduction = int(round(target_vector.length * 0.333))

            target_value = 5 + (accuracy - reduction)

            for s in range(shots):
                if not aa_agent.use_up_ammo(action_key):
                    return False

                attack_roll = bgeutils.d6(2)

                if attack_roll < target_value:
                    armor_base = power
                    armor_base -= self.armor

                    armor_roll = bgeutils.d6(1)
                    if armor_roll < armor_base:
                        self.turn_timer = self.max_turns
                        return True

                # TODO add AA particles

        return False

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


class Paradrop(AirSupport):
    effect_type = "PARADROP"

    def __init__(self, environment, team, effect_id, position, turn_timer):
        super().__init__(environment, team, effect_id, position, turn_timer)

        self.max_turns = 3
        self.delay = 0
        self.radius = 2
        self.triggered = False
        self.added_troops = None

    def add_box(self):
        box = self.environment.add_object("aircraft_icon")
        box.worldPosition = mathutils.Vector(self.position).to_3d()
        return box

    def drop_troops(self):
        drop_location = self.get_drop_location()
        if not drop_location:
            self.added_troops = None
        else:
            self.add_troops(drop_location)

    def get_drop_location(self):
        x, y = self.position
        targets = []

        for ox in range(-2, 2):
            for oy in range(-2, 2):
                tx = x + ox
                ty = y + oy

                if 0 <= tx < self.environment.max_x:
                    if 0 <= ty < self.environment.max_y:
                        targets.append((x + ox, y + oy))

        random.shuffle(targets)
        for target in targets:
            tile = self.environment.pathfinder.graph[target]
            if tile.check_valid_target():
                return target

    def add_troops(self, drop_location):
        self.added_troops = self.environment.load_agent(None, drop_location, self.team, "pt")
        # TODO agent animation for paradrop
        self.added_troops.model.set_animation("PARADROP")
        self.environment.update_map()

    def cycle(self):
        self.turn_timer += 1

        if self.turn_timer == self.max_turns:
            if not self.triggered:
                self.triggered = True
                self.drop_troops()
                self.ended = True


class SpotterPlane(AirSupport):
    effect_type = "SPOTTER_PLANE"

    def __init__(self, environment, team, effect_id, position, turn_timer):
        super().__init__(environment, team, effect_id, position, turn_timer)

        self.max_turns = 4
        self.triggered = False
        self.delay = 2
        self.radius = 8

    def add_box(self):
        box = self.environment.add_object("aircraft_icon")
        box.worldPosition = mathutils.Vector(self.position).to_3d()
        return box

    def cycle(self):
        super().cycle()

        if self.turn_timer == self.delay:
            if not self.triggered:
                self.triggered = True
                particles.DummyAircraft(self.environment, self.position, self.team)


class AirStrike(AirSupport):
    effect_type = "AIR_STRIKE"

    def __init__(self, environment, team, effect_id, position, turn_timer):
        super().__init__(environment, team, effect_id, position, turn_timer)

        self.max_turns = 3
        self.triggered = False

        self.delay = 2
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
                particles.DummyAircraft(self.environment, self.position, self.team)

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
                bomb = ranged_attacks.Bomb(self.environment, hit_position, self, hit_list, self.team, self.power)
                self.bombs.append(bomb)


class RangedAttack(Effect):
    effect_type = "RANGED_ATTACK"

    def __init__(self, environment, team, effect_id, position, turn_timer, owner_id, action_id, scatter):
        super().__init__(environment, team, effect_id, position, turn_timer)
        self.max_turns = 0

        self.owner_id = owner_id
        self.action_id = action_id

        self.scatter = scatter
        self.special = ["TRACKS", "RANGED_ATTACK"]
        self.rating = 1

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
        damage = weapon["damage"]
        self.rating = damage
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

        if owner.agent_type != "INFANTRY":
            adder = owner.model.get_emitter(location)
        else:
            adder = owner.model.model

        contents = [accuracy, damage, target_position, scatter, special]
        projectile_data = ranged_attacks.ranged_attack(self.environment, contents)

        if projectile_data:
            hit_position = projectile_data["hit_position"]
            hit_list = projectile_data["hit_list"]

            # TODO add other shell types. Rockets, grenades and so on.
            if "GRENADE" in special:
                shell = ranged_attacks.GrenadeShell(self.environment, hit_position, self, hit_list, adder, smoke,
                                                    self.team, self.rating)
            elif "ROCKET" in special:
                shell = ranged_attacks.RocketShell(self.environment, hit_position, self, hit_list, adder, smoke,
                                                   self.team, self.rating)

            else:
                shell = ranged_attacks.ArtilleryShell(self.environment, hit_position, self, hit_list, adder, smoke,
                                                      self.team, self.rating)

                self.environment.camera_control.camera_action(hit_position)

            self.shells.append(shell)

        else:
            self.ended = True
