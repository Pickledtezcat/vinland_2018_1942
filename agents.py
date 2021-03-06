import bge
import mathutils
import bgeutils
import agent_actions
import vehicle_model
import particles
import random
import effects


class Agent(object):
    agent_type = "AGENT"

    def __init__(self, environment, position, team, load_key, load_dict):

        self.environment = environment
        self.load_key = load_key
        self.state = None

        self.box = self.add_box()
        self.agent_hook = bgeutils.get_ob("agent_hook", self.box.children)
        self.tilt_hook = bgeutils.get_ob("tilt_hook", self.agent_hook.children)

        self.stats = None
        self.model = None
        self.occupied = None
        self.path = None
        self.visible = True
        self.active_action = None
        self.on_screen = True
        self.visible = False
        self.messages = []
        self.target_data = {}

        if not load_dict:
            self.stats = self.add_stats(tuple(position), team)
            self.set_behavior("BEHAVIOR_DEFAULT")
        else:
            self.reload_from_dict(load_dict)

        self.model = self.add_model()
        self.movement = self.get_movement()
        self.set_position()
        self.busy = False

        if not self.has_effect("DEAD"):
            self.set_occupied(self.get_stat("position"), rebuild_graph=False)
            self.environment.agents[self.get_stat("agent_id")] = self
            self.set_starting_action()
        else:
            self.end()

    def get_icon_name(self):
        return self.load_key

    def get_movement(self):
        return agent_actions.VehicleMovement(self, 0.013)

    def set_active_action(self, new_action):
        self.active_action = new_action
        self.environment.switch_ui("PLAYER")

    def quick_trigger(self, target_action):
        action_trigger = self.trigger_action(target_action, self.get_stat("position"))
        self.active_action = self.get_action_key("MOVE")
        self.environment.switch_ui("PLAYER")

    def set_starting_action(self):
        actions = self.get_stat("action_dict")
        for action_key in actions:
            action = actions[action_key]
            if action["action_name"] == "MOVE":
                self.active_action = action_key

    def get_action_key(self, action_type):
        actions = self.get_stat("action_dict")
        for action_key in actions:
            action = actions[action_key]
            if action["action_name"] == action_type:
                return action_key

    def add_model(self):
        if self.model:
            self.model.terminate()

        return vehicle_model.VehicleModel(self)

    def get_stat(self, stat_string):
        return self.stats[stat_string]

    def set_stat(self, stat_string, value):
        self.stats[stat_string] = value

    def get_cover(self):
        position = self.get_stat("position")
        tile = self.environment.pathfinder.graph[position]
        if tile.cover:
            return 15

        x, y = position

        search_array = [(0, -1, 1), (1, 0, 2), (0, 1, 4), (-1, 0, 8)]
        cover_string = 0

        for i in range(len(search_array)):
            n = search_array[i]
            neighbor_key = (x + n[0], y + n[1])
            nx, ny = neighbor_key
            if 0 <= nx < self.environment.max_x:
                if 0 <= ny < self.environment.max_y:
                    neighbor_tile = self.environment.pathfinder.graph[neighbor_key]
                    if neighbor_tile.cover:
                        cover_string += n[2]

        return cover_string

    def set_occupied(self, position, rebuild_graph=True):
        self.check_in_building()

        if not self.has_effect("LOADED"):

            if self.occupied:
                self.clear_occupied()

            self.environment.set_tile(position, "occupied", self.get_stat("agent_id"))
            self.occupied = position

            if rebuild_graph:
                self.environment.turn_manager.update_pathfinder()

    def clear_occupied(self):
        if self.occupied:
            self.environment.set_tile(self.occupied, "occupied", None)
            self.occupied = None

    def update(self):
        self.process()

    def get_mouse_over(self):
        ai_flag = [effect_key for effect_key in self.get_stat("effects") if "BEHAVIOR" in effect_key]
        if self.environment.environment_type != "GAMEPLAY" and ai_flag:
            ai_string = "AI TYPE:{}".format(ai_flag[0])
            agent_effects = self.get_stat("effects")
            effect_list = ["{}:{}".format(".".join((ek[0] for ek in effect_key.split("_"))), agent_effects[effect_key])
                           for effect_key in agent_effects]
            effect_string = "/ ".join(effect_list)

        else:
            ai_string = ""
            effect_string = ""

        crew = "[{}/{}]".format(self.get_stat("number"), self.get_stat("base_number"))

        agent_args = [self.get_stat("display_name"), self.get_stat("ammo"), self.get_stat("armor"),
                      self.get_stat("hps") - self.get_stat("hp_damage"), self.get_stat("drive_damage"), crew, ai_string,
                      effect_string]

        agent_string = "{}\nAMMO:{}\nARMOR:{}\nHPs:{}\nDRIVE DAMAGE:{}\nCREW:{}\n{}\n{}".format(
            *agent_args)

        return agent_string

    def get_current_action(self):
        current_action = self.get_stat("action_dict")[self.active_action]
        return current_action

    def check_immobile(self):

        if self.has_effect('PRONE'):
            return True

        if self.has_effect("CRIPPLED"):
            return True

        if self.has_effect("LOADED"):
            return True

        if self.has_effect("DYING"):
            return True

        if self.has_effect("DEAD"):
            return True

        if self.has_effect("AMBUSH"):
            return True

    def check_in_building(self):
        x, y = self.get_stat("position")
        tile = self.environment.get_tile((x, y))
        building_key = tile["building"]
        indoors = False
        bunkered_up = False

        if building_key:
            building = self.environment.buildings[building_key]
            if building.get_stat("can_enter") and not building.get_stat("destroyed"):
                indoors = True
                if building.get_stat("armor") > 1:
                    bunkered_up = True

        if indoors:
            self.add_effect("IN_BUILDING", -1)
        else:
            self.clear_effect("IN_BUILDING")

        if bunkered_up:
            self.add_effect("BUNKERED_UP", -1)
        else:
            self.clear_effect("BUNKERED_UP")

    def in_view(self):
        if self.visible:
            position = self.box.worldPosition.copy()
            camera = self.box.scene.active_camera
            if camera.pointInsideFrustum(position):
                self.on_screen = True
            else:
                self.on_screen = False

    def check_visible(self):
        if not self.environment.player_visibility:
            return False

        if self.has_effect('LOADED'):
            return False

        if self.get_stat("team") == 2:
            if self.has_effect("AMBUSH"):
                return False

            x, y = self.get_stat("position")
            lit = self.environment.player_visibility.lit(x, y)
            if lit == 0:
                return False

        return True

    def check_valid_target(self, direct_fire):
        if self.get_stat("team") == 2:
            return False

        if not self.environment.player_visibility:
            return False

        if self.has_effect("BAILED_OUT"):
            return False

        if self.has_effect("DYING"):
            return False

        if self.has_effect('LOADED'):
            return False

        if self.has_effect("AMBUSH"):
            return False

        x, y = self.get_stat("position")
        lit = self.environment.enemy_visibility.lit(x, y)
        if lit == 0:
            return False

        if direct_fire and lit == 1:
            return False

        return True

    def check_valid_supply_source(self, own_team):
        if self.get_stat("team") != own_team:
            return False

        if self.has_effect("BAILED_OUT"):
            return False

        if self.has_effect("DYING"):
            return False

        if self.has_effect('LOADED'):
            return False

        if self.has_effect("AMBUSH"):
            return False

        if not self.get_stat("can_supply"):
            return False

        return True

    def check_active_enemy(self):
        if self.get_stat("team") == 1:
            return False

        if self.has_effect("BAILED_OUT"):
            return False

        if self.has_effect("DYING"):
            return False

        if self.has_effect('LOADED'):
            return False

        if self.has_effect("AMBUSH"):
            return False

        if self.has_effect("CRIPPLED"):
            return False

        return True

    def check_valid_support_target(self):
        if self.get_stat("team") != 2:
            return False

        if not self.environment.player_visibility:
            return False

        if self.has_effect("BAILED_OUT"):
            return False

        if self.has_effect("DYING"):
            return False

        if self.has_effect('LOADED'):
            return False

        if self.has_effect("AMBUSH"):
            return False

        if not self.has_effect("HAS_RADIO"):
            return False

        return True

    def check_valid_jammer_target(self):
        if self.get_stat("team") != 1:
            return False

        if not self.environment.player_visibility:
            return False

        if self.has_effect("BAILED_OUT"):
            return False

        if self.has_effect("DYING"):
            return False

        if self.has_effect('LOADED'):
            return False

        if self.has_effect("AMBUSH"):
            return False

        x, y = self.get_stat("position")
        visibility = self.environment.enemy_visibility.lit(x, y)
        if visibility != 2:
            return False

        return True

    def get_position(self):
        return self.get_stat("position")

    def add_box(self):
        box = self.environment.add_object("agent")
        return box

    def set_position(self):
        self.movement.set_starting_position()

    def regenerate(self):
        base_actions = self.get_stat("base_actions")

        if self.has_effect("DEAD"):
            self.set_stat("free_actions", 0)

        elif self.has_effect("DYING"):
            if not self.has_effect("DEAD"):
                self.add_effect("DEAD", -1)
                self.set_stat("free_actions", 0)
                self.clear_occupied()
                self.environment.turn_manager.update_pathfinder()

        elif self.has_effect("BAILED_OUT"):
            self.set_stat("free_actions", 0)

        else:
            if self.has_effect("PLACING_MINES"):
                self.place_mines()
                self.clear_effect("PLACING_MINES")

            if self.has_effect("GET_REINFORCEMENT"):
                self.reinforce_crew()
                self.clear_effect("GET_REINFORCEMENT")

            if self.has_effect("REMOVING_MINES"):
                self.remove_mines()
                self.clear_effect("REMOVING_MINES")

            if self.has_effect("CONFUSED"):
                base_actions -= 1
                self.clear_effect("CONFUSED")

            if self.has_effect("OVERWATCH"):
                base_actions += 1
                self.clear_effect("OVERWATCH")

            if self.has_effect("COMMANDER"):
                base_actions += 1

            shock = self.get_stat("shock")
            if shock > 10:
                if self.agent_type != "VEHICLE":
                    self.add_effect("PRONE", -1)

            shock_reduction = int(shock * 0.1)

            new_actions = (base_actions - shock_reduction)
            new_shock = 0

            if new_actions < 0:
                new_shock = new_actions * -10
                new_actions = 0

            self.set_stat("shock", new_shock)
            self.set_stat("free_actions", new_actions)
            actions = self.get_stat("action_dict")
            for action_key in actions:
                action = actions[action_key]
                if action["triggered"]:
                    action["recharged"] -= 1
                    if action["recharged"] <= 0:
                        action["triggered"] = False

            self.set_starting_action()
            self.process_effects()

            self.rough_riding()

        self.check_drive()

    def check_has_supply(self):
        source_tile = self.get_stat("position")
        x, y = source_tile

        search_array = [[0, 0], [0, 1], [1, 0], [0, -1], [-1, 0], [-1, -1], [1, -1], [-1, 1], [1, 1]]

        for n in search_array:
            neighbor_key = (x + n[0], y + n[1])

            neighbor_tile = self.environment.get_tile(neighbor_key)
            if neighbor_tile["building"]:
                building = self.environment.buildings[neighbor_tile["building"]]
                if building.can_supply():
                    return True
            if neighbor_tile["occupied"]:
                occupier = self.environment.agents[neighbor_tile["occupied"]]
                if occupier.check_valid_supply_source(self.get_stat("team")):
                    return True

        return False

    def rough_riding(self):

        if self.has_effect("MOVED"):
            position = self.get_stat("position")
            tile = self.environment.get_tile(position)
            rough_riding = 3

            if not tile["road"] and not tile["bridge"]:
                if tile["softness"] == 4:
                    rough_riding += 3

                elif tile["softness"] > 1:
                    rough_riding += 2

            if tile["bushes"]:
                rough_riding += 2

            if self.has_effect("FAST"):
                rough_riding += 1

            if self.get_stat("drive_damage") > 1:
                rough_riding += 1

            if self.has_effect("OVERDRIVE"):
                rough_riding += 1

            target_number = rough_riding - self.get_stat("handling")

            damage_chance = bgeutils.d6(2)
            if damage_chance < target_number:
                particles.DebugText(self.environment, "DRIVE\nDAMAGED!", self.box.worldPosition.copy())
                self.set_stat("drive_damage", self.get_stat("drive_damage") + 1)

    def check_drive(self):
        on_road = self.get_stat("on_road") - self.get_stat("drive_damage")
        off_road = self.get_stat("off_road") - self.get_stat("drive_damage")

        if on_road < 0 or off_road < 0:
            self.add_effect("CRIPPLED", -1)
        else:
            self.clear_effect("CRIPPLED")

        return on_road, off_road

    def get_movement_cost(self):
        on_road, off_road = self.check_drive()

        if self.has_effect("CRIPPLED"):
            return False

        if self.has_effect("QUICK_MARCH"):
            on_road *= 2
            off_road *= 2

        if self.has_effect("OVERDRIVE"):
            on_road += 1
            off_road += 1

        if on_road > 0:
            on_road_cost = 1.0 / on_road
        else:
            return False

        if off_road > 0:
            off_road_cost = 1.0 / off_road
        else:
            return False

        return on_road_cost, off_road_cost

    def save_to_dict(self):
        self.clear_occupied()
        return self.stats

    def reload_from_dict(self, load_dict):
        self.stats = load_dict
        self.set_stat("position", tuple(self.get_stat("position")))
        self.set_stat("facing", tuple(self.get_stat("facing")))
        self.load_key = self.get_stat("agent_name")

    def process(self):
        self.visible = self.check_visible()
        self.in_view()
        self.busy = self.process_actions()
        if not self.busy:
            self.check_in_building()
            self.check_active_effects()
            self.process_messages()

    def check_active_effects(self):

        ammo_store = self.get_stat("ammo")
        total_ammo = self.get_stat("starting_ammo")

        if total_ammo > 0:
            if ammo_store <= 0:
                self.add_effect("OUT_OF_AMMO", -1)
                self.clear_effect("LOW_AMMO")
            elif ammo_store <= (total_ammo * 0.25):
                self.add_effect("LOW_AMMO", -1)
                self.clear_effect("OUT_OF_AMMO")
            else:
                self.clear_effect("OUT_OF_AMMO")
                self.clear_effect("LOW_AMMO")

        if not self.has_effect("BUTTONED_UP") and not self.has_effect("PRONE"):
            self.add_effect("VISION", -1)
        else:
            self.clear_effect("VISION")

    def process_actions(self):
        busy = False

        self.movement.set_speed()

        if not self.movement.done:
            self.movement.update()

            if self.movement.done:
                self.environment.pathfinder.update_graph()
            else:
                busy = True

        animating = self.model.update()
        if animating:
            busy = True

        return busy

    def add_stats(self, position, team):
        vehicle_dict = self.environment.vehicle_dict.copy()
        weapon_dict = self.environment.weapons_dict.copy()
        base_action_dict = self.environment.action_dict.copy()

        base_stats = vehicle_dict[self.load_key].copy()
        base_stats["effects"] = {}
        base_stats["can_supply"] = False

        # TODO set special actions based on vehicle

        actions = []

        if self.agent_type == "ARTILLERY":
            action_strings = ["TOGGLE_STANCE", "MOVE", "REDEPLOY", "GRAB_SUPPLIES", "CALL_REINFORCEMENTS",
                              "EMERGENCY_REPAIR"]
        else:
            action_strings = ["OVERDRIVE", "BAIL_OUT", "MOVE", "FACE_TARGET", "CALL_REINFORCEMENTS", "EMERGENCY_REPAIR",
                              "GRAB_SUPPLIES"]

        # TODO add some special abilities

        specials = [special for special in base_stats["special"]]

        if "OPEN_TOP" not in specials and "AA_TURRET" not in specials and not self.agent_type == "ARTILLERY":
            action_strings.append("TOGGLE_BUTTONED_UP")

        for action_string in action_strings:
            actions.append(base_action_dict[action_string].copy())

        radios = ["RADIO", "COMMAND_RADIO", "TACTICAL_RADIO", "AIR_FORCE_RADIO"]

        for special in specials:
            if special == "COMMANDER":
                actions.append(base_action_dict["COMMANDER"].copy())
            if special == "PERISCOPE":
                actions.append(base_action_dict["SPOTTING"].copy())
            if special == "LOADER":
                actions.append(base_action_dict["FAST_RELOAD"].copy())
                actions.append(base_action_dict["CLEAR_JAM"].copy())

            if special == "STORAGE":
                base_stats["can_supply"] = True
                actions.append(base_action_dict["REPAIR"].copy())
                actions.append(base_action_dict["REARM_AND_RELOAD"].copy())
                actions.append(base_action_dict["LOAD_TROOPS"].copy())
                actions.append(base_action_dict["UNLOAD_TROOPS"].copy())
                actions.append(base_action_dict["CREW"].copy())

            if special in radios:
                base_stats["effects"]["HAS_RADIO"] = -1

            if special == "COMMAND_RADIO" and "COMMAND_RADIO" not in base_stats["effects"]:
                base_stats["effects"]["COMMAND_RADIO"] = -1
                command_actions = ["QUICK_MARCH", "DIRECT_ORDER", "RECOVER_MORALE"]

                for command_action in command_actions:
                    actions.append(base_action_dict[command_action].copy())

            if special == "TACTICAL_RADIO" and "TACTICAL_RADIO" not in base_stats["effects"]:
                base_stats["effects"]["TACTICAL_RADIO"] = -1
                tactical_actions = ["MARK_TARGET", "RADIO_JAMMING", "TARGET_RECOGNITION", "RADIO_CONFUSION"]

                for tactical_action in tactical_actions:
                    actions.append(base_action_dict[tactical_action].copy())

            if special == "AIR_FORCE_RADIO" and "AIR_FORCE_RADIO" not in base_stats["effects"]:
                base_stats["effects"]["AIR_FORCE_RADIO"] = -1
                air_force_actions = ["SPOTTER_PLANE", "AIR_STRIKE", "PARADROP"]

                for air_force_action in air_force_actions:
                    actions.append(base_action_dict[air_force_action].copy())

            if special == "AA_TURRET":
                actions.append(base_action_dict["ANTI_AIRCRAFT_FIRE"].copy())

        if "HAS_RADIO" in base_stats["effects"]:
            actions.append(base_action_dict["CHANGE_FREQUENCIES"].copy())
            actions.append(base_action_dict["OVERWATCH"].copy())
            actions.append(base_action_dict["RAPID_FIRE"].copy())
            actions.append(base_action_dict["SPECIAL_AMMO"].copy())
            actions.append(base_action_dict["STEADY_AIM"].copy())

        ai_default = base_stats["ai_default"]
        base_stats["default_behavior"] = "BEHAVIOR_{}".format(ai_default)

        weapon_locations = ["turret_primary", "turret_secondary", "hull_primary", "hull_secondary"]

        for location in weapon_locations:
            weapon_string = base_stats[location]

            if weapon_string:
                weapon = weapon_dict[weapon_string].copy()
                base_stats[location] = weapon.copy()
                base_actions = [action for action in weapon["actions"]]

                for action in base_actions:
                    # TODO make valid choices based on special tags (sights etc...)
                    # TODO make sure rapid fire isn't added twice, reduce rate of supporting fire,
                    # check infantry armor penetration, add variable damage

                    invalid_choice = False

                    if not invalid_choice:
                        action_details = base_action_dict[action].copy()
                        action_weapon_stats = weapon.copy()

                        modifiers = [["accuracy_multiplier", "accuracy"],
                                     ["armor_multiplier", "penetration"],
                                     ["damage_multiplier", "damage"],
                                     ["shock_multiplier", "shock"]]

                        for modifier in modifiers:
                            if modifier[0] == "accuracy_multiplier":
                                base = action_weapon_stats["base_accuracy"]
                            else:
                                base = action_weapon_stats["power"]

                            modifier_value = action_details[modifier[0]]
                            new_value = int(round(base * modifier_value))

                            if modifier_value > 1.0:
                                if new_value == base:
                                    new_value += 1

                            elif modifier_value < 1.0:
                                if new_value == base:
                                    new_value -= 1

                            if new_value < 0:
                                new_value = 0

                            if modifier[0] == "accuracy_multiplier":
                                if "turret" in location:
                                    new_value += 1

                            action_weapon_stats[modifier[1]] = new_value

                        action_weapon_stats["shots"] *= action_details["shot_multiplier"]

                        action_details = base_action_dict[action].copy()
                        action_details["action_cost"] += weapon["base_actions"]
                        action_details["recharge_time"] += weapon["base_recharge"]

                        action_details["weapon_name"] = weapon["name"]
                        action_details["weapon_stats"] = action_weapon_stats
                        action_details["weapon_location"] = location
                        actions.append(action_details)

            else:
                base_stats[location] = None

        action_dict = {}
        for setting_action in actions:
            action_id = self.environment.get_new_id()
            action_key = "{}_{}".format(setting_action["action_name"], action_id)
            action_dict[action_key] = setting_action

        # dummy stats for artillery
        base_stats["mesh"] = "ENGINEER"
        base_stats["base_number"] = base_stats["number"] = base_stats["size"]
        base_stats["toughness"] = 10

        base_stats["starting_ammo"] = base_stats["ammo"]
        base_stats["action_dict"] = action_dict
        base_stats["position"] = position
        base_stats["facing"] = (0, 1)
        base_stats["team"] = team
        base_stats["agent_name"] = self.load_key
        base_stats["shock"] = 0
        base_stats["level"] = 1
        base_stats["base_actions"] = 2
        base_stats["free_actions"] = 2
        base_stats["loaded_troops"] = []
        base_stats["max_load"] = 4
        id_number = self.environment.get_new_id()
        base_stats["agent_id"] = "{}_{}".format(self.load_key, id_number)
        base_stats["hp_damage"] = 0
        base_stats["drive_damage"] = 0
        base_stats["shock"] = 0
        base_stats['objective_index'] = 9

        return base_stats

    def check_needs_supply(self):
        if self.has_effect("DYING") or self.has_effect("LOADED") or self.has_effect("AMBUSH"):
            return ["NONE", 2.0, 1000, self]

        base_ammo = self.get_stat("starting_ammo")
        ammo_store = self.get_stat("ammo")
        position = self.get_stat("position")
        movement_cost = self.environment.pathfinder.get_movement_cost(position) * -1

        if self.has_effect("BAILED_OUT"):
            return ["CREW", 0.01, movement_cost, self]

        if base_ammo > 0:
            ammo_ratio = ammo_store / base_ammo
            if ammo_ratio < 1.0:
                return ["REARM_AND_RELOAD", ammo_ratio, movement_cost, self]

        if self.get_stat("drive_damage") > 0:
            drive_damage_ratio = 1.0 / self.get_stat("drive_damage") + 1
            return ["REPAIR", drive_damage_ratio, movement_cost, self]

        if self.get_stat("hp_damage") > 0:
            damage_ratio = self.get_stat("hps") / self.get_stat("hp_damage")
            if damage_ratio < 1.0:
                return ["REPAIR", damage_ratio, movement_cost, self]

        return ["NONE", 2.0, 1000, self]

    def out_of_ammo(self, action_key):
        current_action = self.get_stat("action_dict")[action_key]
        if current_action["action_type"] != "WEAPON":
            return False

        if self.get_stat("ammo") <= 0:
            return True

        return False

    def check_jammed(self, action_key):
        current_action = self.get_stat("action_dict")[action_key]
        if current_action["action_type"] == "WEAPON":
            if self.has_effect("JAMMED"):
                return True

        return False

    def use_up_ammo(self, action_key):

        current_action = self.get_stat("action_dict")[action_key]
        ammo_drain = current_action["weapon_stats"]["damage"]
        shots = current_action["weapon_stats"]["shots"]
        for s in range(shots):
            remaining = max(0, self.get_stat("ammo") - ammo_drain)

            self.set_stat("ammo", remaining)
            self.jamming_save(action_key)

    def jamming_save(self, action_key):
        first_chance = bgeutils.d6(1)
        if first_chance == 1:
            current_action = self.get_stat("action_dict")[action_key]
            jamming_chance = current_action["weapon_stats"]["jamming_chance"]
            jamming_save = bgeutils.d6(1)
            if jamming_save <= jamming_chance:
                self.add_effect("JAMMED", 3)
                particles.DebugText(self.environment, "WEAPONS JAMMED!", self.box.worldPosition.copy())

    def check_valid_selection(self):
        if self.has_effect("BAILED_OUT"):
            return False
        if self.has_effect("DYING"):
            return False
        if self.get_stat("team") != 1:
            return False
        if self.has_effect("LOADED"):
            return False

        return True

    def ui_select_type(self):
        if not self.visible:
            return None

        if self.get_stat("team") == 1:
            if self.has_effect("BAILED_OUT"):
                return "INACTIVE"
            if self.has_effect("DYING"):
                return "INACTIVE"

            return "ACTIVE"

        else:
            if self.has_effect("BAILED_OUT"):
                return "INACTIVE_ENEMY"
            if self.has_effect("DYING"):
                return "INACTIVE_ENEMY"

            return "ENEMY"

    def check_action_valid(self, action_key, target_tile):
        results = ["BUSY", "NO_RADIO", "NO_AMMO", "JAMMED", "AIR_SUPPORT", "NO_ACTIONS", "TRIGGERED",
                   "INVISIBLE", "SELECT_FRIEND", "TOO_FAR", "VALID_TARGET", "NO_SUPPLY"]

        if self.busy:
            return ["BUSY"]

        current_action = self.get_stat("action_dict")[action_key]

        action_cost = current_action["action_cost"]
        current_target = current_action["target"]

        target_agent = None
        valid_selection = False
        target_type = "NONE"

        mouse_over_tile = self.environment.get_tile(target_tile)
        adjacent = target_tile in self.environment.pathfinder.adjacent_tiles

        if self.get_stat("free_actions") < action_cost:
            return ["NO_ACTIONS"]

        if current_action["requires_supply"]:
            if not self.check_has_supply():
                return ["NO_SUPPLY"]

        triggered = current_action["triggered"]
        if triggered:
            return ["TRIGGERED"]

        working_radio = self.has_effect("HAS_RADIO") and not self.has_effect("RADIO_JAMMING")

        if current_target == "AIRCRAFT" and working_radio and mouse_over_tile:
            return ["AIR_SUPPORT"]

        if self.get_stat("team") == 1:
            visibility = self.environment.player_visibility.lit(*target_tile)
        else:
            visibility = self.environment.enemy_visibility.lit(*target_tile)

        target = mouse_over_tile["occupied"]
        target_building = mouse_over_tile["building"]
        friendly = False
        immobile = self.check_immobile()

        if target:
            target_agent = self.environment.agents[target]
            if target_agent.get_stat("team") == self.get_stat("team"):
                friendly = True
            else:
                if target_agent.has_effect("AMBUSH"):
                    target_agent = None
                elif self.get_stat("team") == 5 and target_agent.has_effect("BAILED_OUT"):
                    # TODO allow enemy to target knocked out units for recrewing
                    target_agent = None

        if target_agent:
            valid_selection = target_agent.check_valid_selection()
            target_working_radio = target_agent.has_effect("HAS_RADIO") and not target_agent.has_effect("RADIO_JAMMING")

            if target_agent == self:
                target_type = "SELF"
            elif friendly:
                if adjacent and current_target == "FRIEND":
                    target_type = "FRIEND"
                elif target_working_radio:
                    target_type = "ALLIES"
                else:
                    if valid_selection:
                        return ["SELECT_FRIEND", target]
            else:
                if adjacent and current_target == "FRIEND" and target_agent.has_effect("BAILED_OUT"):
                    target_type = "FRIEND"
                else:
                    target_type = "ENEMY"
        else:
            building = tuple(self.environment.tile_over) in self.environment.pathfinder.building_tiles

            if current_target == "BUILDING" and building and not immobile:
                return ["BUILDING"]
            elif current_target == "ENEMY" and target_building and visibility == 2:
                target_building_object = self.environment.buildings[target_building]
                if target_building_object.check_valid_target():
                    target_type = "BUILDING"
                    return ["VALID_TARGET", current_target, target_type, target_building, action_cost]
            else:
                target_type = "MAP"

        allies = ["FRIEND", "ALLIES", "FRIENDLY"]

        if current_target == "FRIEND" and target_type == "ALLIES":
            if valid_selection:
                return ["SELECT_FRIEND", target]

        if current_target not in allies and target_type in allies:
            if valid_selection:
                return ["SELECT_FRIEND", target]

        if current_action["radio_points"] > 0 and not working_radio:
            return ["NO_RADIO"]

        if self.out_of_ammo(action_key):
            return ["NO_AMMO"]

        if self.check_jammed(action_key):
            return ["JAMMED"]

        if current_target == "BUILDING" and immobile:
            return ["IMMOBILE"]

        movement_cost = self.environment.pathfinder.get_movement_cost(target_tile)
        if current_target == "MOVE":
            if current_action["effect"] == "ROTATE":
                return ["ROTATE"]

            if visibility == 0:
                return ["INVISIBLE"]

            if target_type == "MAP":
                if immobile:
                    return ["IMMOBILE"]

                if movement_cost > self.get_stat("free_actions"):
                    return ["TOO_FAR"]
                path = self.environment.pathfinder.current_path[1:]
                if not path:
                    return ["IMPASSABLE"]

                return ["MOVE", movement_cost]

        valid_target = current_target == target_type or (current_target == "MAP" and target_type == "ENEMY")

        if current_target == "ENEMY" and visibility < 2:
            return ["INVISIBLE"]
        elif visibility == 0:
            return ["INVALID_TARGET"]
        else:
            if not valid_target:
                return ["INVALID_TARGET"]

            return ["VALID_TARGET", current_target, target_type, target, action_cost]

    def trigger_action(self, action_key, target_tile):
        target_tile = tuple(target_tile)

        action_check = self.check_action_valid(action_key, target_tile)
        current_action = self.get_stat("action_dict")[action_key]
        action_cost = current_action["action_cost"]

        message = None
        triggered = False

        if action_check:
            action_status = action_check[0]

            if action_status == "AIR_SUPPORT":
                self.trigger_air_support(action_key, target_tile)
                triggered = True

            elif action_status == "SELECT_FRIEND":
                target = action_check[1]
                self.environment.turn_manager.active_agent = target
                self.environment.pathfinder.update_graph()
                return True

            elif action_status == "MOVE":
                self.environment.pathfinder.find_path(target_tile)
                path = self.environment.pathfinder.current_path[1:]
                action_cost = action_check[1]

                if path:
                    self.add_effect("MOVED", 1)
                    if len(path) > 4:
                        self.add_effect("FAST", 1)

                    message = {"agent_id": self.get_stat("agent_id"), "header": "FOLLOW_PATH",
                               "contents": [path]}
                    triggered = True

            elif action_status == "ROTATE":
                message = {"agent_id": self.get_stat("agent_id"), "header": "TARGET_LOCATION",
                           "contents": [target_tile]}

                triggered = True

            elif action_status == "BUILDING":
                message = {"agent_id": self.get_stat("agent_id"), "header": "ENTER_BUILDING",
                           "contents": [target_tile]}

                triggered = True

            elif action_status == "VALID_TARGET":
                action_status, current_target, target_type, target, action_cost = action_check

                # TODO check for other validity variables
                target_agent = None
                if target in self.environment.agents:
                    target_agent = self.environment.agents[target]

                header = "PROCESS_ACTION"
                message = {"agent_id": self.get_stat("agent_id"), "header": header,
                           "contents": [action_key, target, self.get_stat("agent_id"),
                                        self.get_stat("position"), target_tile, target_type]}

                face_target = False
                if target_type == "FRIEND" or target_type == "ENEMY":
                    face_target = True
                    position = self.get_stat("position")
                    target_position = target_agent.get_stat("position")

                elif target_type == "MAP" or target_type == "BUILDING":
                    face_target = True
                    position = self.get_stat("position")
                    target_position = target_tile

                if face_target:
                    target_vector = mathutils.Vector(target_position) - mathutils.Vector(position)
                    best_vector = bgeutils.get_facing(target_vector)
                    if best_vector:
                        if self.movement.done:
                            self.movement.set_target_facing(tuple(best_vector))

                if self.clear_effect("AMBUSH"):
                    particles.DebugText(self.environment, "AMBUSH TRIGGERED!", self.box.worldPosition.copy())

                if current_action["action_type"] == "WEAPON":
                    self.use_up_ammo(action_key)

                triggered = True

            if triggered:
                if message:
                    self.environment.message_list.append(message)

                self.set_stat("free_actions", self.get_stat("free_actions") - action_cost)
                if current_action["recharge_time"] > 0:
                    current_action["triggered"] = True
                    current_action["recharged"] = current_action["recharge_time"]

                return True

        return False

    def trigger_air_support(self, action_key, target_tile):

        current_action = self.get_stat("action_dict")[action_key]

        if current_action["effect"] == "SPOTTER_PLANE":
            effects.SpotterPlane(self.environment, self.get_stat("team"), None, target_tile, 0)

        if current_action["effect"] == "AIR_STRIKE":
            effects.AirStrike(self.environment, self.get_stat("team"), None, target_tile, 0)

        if current_action["effect"] == "DROP_TROOPS":
            effects.Paradrop(self.environment, self.get_stat("team"), None, target_tile, 0)

        self.environment.update_map()

    def trigger_explosion(self, message_contents):
        self.trigger_reveal()

        action_id, target_id, owner_id, origin, tile_over, target_type = message_contents

        current_action = self.get_stat("action_dict")[action_id]

        if self.agent_type != "INFANTRY":
            self.model.set_animation("SHOOTING", current_action)
        else:
            self.model.set_animation("FIDGET")

        origin_id = self.get_stat("agent_id")
        target_check = self.environment.turn_manager.get_target_data(origin_id, target_id, action_id, tile_over)

        target_type = target_check["target_type"]

        if target_type == "INVALID":
            print("invalid action, no target")
        else:
            contents = target_check["contents"]
            damage, shock, base_target, penetration, reduction = contents

            effects.RangedAttack(self.environment, self.get_stat("team"), None, tile_over, 0, self.get_stat("agent_id"),
                                 action_id, reduction)

            # self.use_up_ammo(action_id)

    def trigger_attack(self, message_contents):

        action_id, target_id, owner_id, origin, tile_over, target_type = message_contents
        origin_id = self.get_stat("agent_id")

        target_check = self.environment.turn_manager.get_target_data(origin_id, target_id, action_id, tile_over,
                                                                     target_type)
        target_type = target_check["target_type"]
        contents = target_check["contents"]

        current_action = self.get_stat("action_dict")[action_id]

        special = []
        if "TRACKS" in current_action["effect"]:
            special.append("TRACKS")

        if "SPLASH" in current_action["effect"]:
            special.append("SPLASH")

        if self.agent_type == "INFANTRY":
            special.append("INFANTRY")

        if self.agent_type != "INFANTRY":
            self.model.set_animation("SHOOTING", current_action)
        else:
            if target_id in self.environment.agents:
                target_position = self.environment.agents[target_id].get_stat("position")
            else:
                target_position = tile_over

            self.model.target_location = target_position
            self.model.set_animation("SHOOTING", current_action)

        if target_type == "INVALID":
            print("invalid action, no target")
        else:
            damage, shock, flanked, covered, base_target, armor_target = contents

            message = {"agent_id": target_id, "header": "HIT",
                       "contents": [origin, base_target, armor_target, damage, shock, special, tile_over]}
            self.environment.message_list.append(message)
            # self.use_up_ammo(action_id)

    def set_damaged(self, restore):
        base_number = self.get_stat("base_number")
        ammo_store = self.get_stat("starting_ammo")

        if restore:
            self.set_stat("drive_damage", 0)
            self.set_stat("hp_damage", 0)
            self.set_stat("number", base_number)

            self.set_stat("ammo", ammo_store)
            self.check_drive()
            self.model = self.add_model()
            return "DAMAGE CLEARED"

        else:
            particles.ShellImpact(self.environment, self.get_stat("position"), 5)

            max_hps = self.get_stat("hps")
            damage = int(random.uniform(0.3, 0.7) * max_hps)
            max_damage = max(damage, min(0, max_hps - 2))
            drive_damage = random.randint(1, 3)

            self.set_stat("hp_damage", max_damage)

            self.set_stat("ammo", int(ammo_store * random.uniform(0.3, 0.7)))

            if self.agent_type == "VEHICLE":
                self.set_stat("drive_damage", drive_damage)

            new_number = int(base_number * 0.5)
            self.set_stat("number", new_number)

            self.check_drive()
            self.model = self.add_model()
            return "AGENT DAMAGED"

    def process_hit(self, hit_message):

        hit = hit_message["contents"]
        in_the_hatch = False
        on_target = False
        penetrated = False
        damage = 3
        origin = None
        special = []

        if hit:
            origin, base_target, armor_target, damage, shock, special, tile_over = hit
            self.damage_building(hit_message)

            visual_effect = damage

            if not self.has_effect("DYING"):
                self.model.set_animation("HIT")
                attack_roll = bgeutils.d6(2)
                on_target = True
                critical = attack_roll == 2
                area_effect = "SPLASH" in special or "RANGED_ATTACK" in special or "GRENADE" in special

                if attack_roll > base_target or attack_roll == 12:
                    if "SPLASH" in special:
                        particles.DebugText(self.environment, "SPLASH DAMAGE!", self.box.worldPosition.copy())
                        damage = int(damage * 0.5)
                        shock = int(shock * 0.5)
                    else:
                        particles.DebugText(self.environment, "MISSED", self.box.worldPosition.copy())
                        origin = None
                        on_target = False

                if on_target:
                    penetration_roll = bgeutils.d6(1)

                    if "TRACKS" in special:
                        self.drive_damage()

                    if "GRENADE" in special:
                        if not self.has_effect("BUTTONED_UP"):
                            if bgeutils.d6(1) < 4:
                                in_the_hatch = True

                    if "DIRECT_HIT" in special:
                        if not self.has_effect("BUTTONED_UP"):
                            if bgeutils.d6(1) == 1:
                                in_the_hatch = True

                        armor_target += 2

                    if critical:
                        armor_target += 2

                    if penetration_roll > armor_target and not in_the_hatch:
                        particles.DebugText(self.environment, "DEFLECTION", self.box.worldPosition.copy())
                        self.set_stat("shock", self.get_stat("shock") + int(shock * 0.5))
                    else:
                        penetrated = True

                        if area_effect and self.has_effect("PRONE"):
                            damage = int(damage * 0.5)

                        self.handle_damage(critical, damage, shock)

        hit_position = self.box.worldPosition.copy()

        if "RANGED_ATTACK" not in special:
            if on_target and not self.agent_type == "INFANTRY":
                if penetrated:
                    particles.ShellImpact(self.environment, hit_position, visual_effect)
                else:
                    particles.ShellDeflection(self.environment, hit_position, visual_effect)

            else:
                if "INFANTRY" not in special:
                    particles.ShellExplosion(self.environment, hit_position, visual_effect)

        if origin:
            origin_point = mathutils.Vector(origin).to_3d()
            self.apply_knock(origin_point, damage)

    def damage_building(self, hit_message):
        position = self.get_stat("position")
        tile = self.environment.get_tile(position)

        if tile:
            if tile["building"]:
                building = self.environment.buildings[tile["building"]]
                building.process_hit(hit_message)

    def handle_damage(self, critical, damage, shock):

        if critical:
            critical_amount = bgeutils.d6(1)

            damage += critical_amount
            shock += critical_amount

            damage = int(damage * 2)
            shock = int(shock * 2)

            for _ in range(critical_amount):
                self.drive_damage()
                self.crew_critical()

        crew_hit = max(1, int(damage * 0.333))
        for _ in range(crew_hit):
            self.crew_critical()

        self.set_stat("hp_damage", self.get_stat("hp_damage") + damage)
        self.set_stat("shock", self.get_stat("shock") + shock)

        killed = False
        if self.get_stat("hp_damage") > self.get_stat("hps"):
            killed = True

        self.show_damage(killed)
        particles.DebugText(self.environment, "{}".format(damage), self.box.worldPosition.copy())

    def crush_kill(self):
        self.set_stat("number", 0)
        self.add_effect("DYING", -1)

    def crew_critical(self):
        first_save = bgeutils.d6(1)
        if not self.has_effect("BAILED_OUT"):
            if first_save == 1:
                crew = self.get_stat("number")
                crew_save = bgeutils.d6(1)
                if crew_save == 1 or crew <= 1:
                    self.set_stat("number", 0)
                    particles.DebugText(self.environment, "CREW KNOCKED OUT!", self.box.worldPosition.copy())
                    self.add_effect("BAILED_OUT", -1)
                else:
                    self.set_stat("number", crew - 1)

    def reinforce_crew(self):
        max_crew = self.get_stat("base_number")
        current_crew = self.get_stat("number")
        new_crew = min(max_crew, current_crew + 1)
        self.set_stat("number", new_crew)

        if max_crew != current_crew:
            particles.DebugText(self.environment, "REINFORCED!", self.box.worldPosition.copy())

    def apply_knock(self, origin, damage):
        pass

    def drive_damage(self):
        pass

    def repair_damage(self):
        pass

    def show_damage(self, killed):
        if killed:
            effects.Smoke(self.environment, self.get_stat("team"), None, self.get_stat("position"), 0)
            self.add_effect("DYING", -1)
            position = mathutils.Vector(self.get_stat("position")).to_3d()
            particles.DestroyedVehicle(self.environment, position, self.get_stat("size"))

    def process_messages(self):

        new_messages = self.environment.get_messages(self.get_stat("agent_id"))

        for new_message in new_messages:
            self.messages.append(new_message)

        if self.messages:
            message = self.messages.pop()

            if message["header"] == "FOLLOW_PATH":
                self.model.set_animation("MOVEMENT")
                path = message["contents"][0]
                if not self.busy:
                    if self.movement.done:
                        self.movement.set_path(path)

            elif message["header"] == "ENTER_BUILDING":
                self.model.set_animation("MOVEMENT")
                path = [message["contents"][0]]
                if not self.busy:
                    if self.movement.done:
                        self.movement.set_path(path)

            elif message["header"] == "TARGET_LOCATION":
                self.model.set_animation("MOVEMENT")
                position = self.get_stat("position")
                target_position = message["contents"][0]
                if not position == target_position:
                    target_vector = mathutils.Vector(target_position) - mathutils.Vector(position)
                    best_vector = bgeutils.get_facing(target_vector)
                    if best_vector and not self.busy:
                        if self.movement.done:
                            self.movement.set_target_facing(tuple(best_vector))

            elif message["header"] == "PROCESS_ACTION":
                action_id = message["contents"][0]
                active_action = self.get_stat("action_dict")[action_id]
                if active_action["action_type"] == "WEAPON":
                    weapon = active_action["weapon_stats"]
                    shots = weapon["shots"]

                    if "HIT" in active_action["effect"]:
                        message = {"agent_id": message["agent_id"], "header": "TRIGGER_ATTACK",
                                   "contents": message["contents"].copy()}

                    elif "EXPLOSION" in active_action["effect"]:
                        message = {"agent_id": message["agent_id"], "header": "TRIGGER_EXPLOSION",
                                   "contents": message["contents"].copy()}

                    elif "SMOKE" in active_action["effect"]:
                        message = {"agent_id": message["agent_id"], "header": "TRIGGER_EXPLOSION",
                                   "contents": message["contents"].copy()}

                    if self.has_effect("RAPID_FIRE") and weapon["mount"] == "secondary":
                        if shots > 1:
                            shots *= 2

                    for s in range(shots):
                        number = 1
                        if self.agent_type == "INFANTRY":
                            number = self.get_stat("number")

                        for n in range(number):
                            self.messages.append(message)

                else:
                    duration = active_action["effect_duration"]
                    if duration != 0:
                        self.add_effect(active_action["effect"], duration)
                    else:
                        self.trigger_instant_effect(message)

                    if active_action["end_turn"]:
                        self.set_stat("free_actions", 0)

                self.environment.turn_manager.reset_ui()
                particles.DebugText(self.environment, action_id, self.box.worldPosition.copy())

            elif message["header"] == "HIT":
                self.process_hit(message)

            elif message["header"] == "TRIGGER_ATTACK":
                self.trigger_attack(message["contents"])

            elif message["header"] == "TRIGGER_EXPLOSION":
                self.trigger_explosion(message["contents"])

    def process_effects(self):

        next_generation = {}
        agent_effects = self.get_stat('effects')

        for effect_key in agent_effects:
            duration = agent_effects[effect_key]
            if duration > 0:
                duration -= 1

            if duration > 0:
                next_generation[effect_key] = duration
            elif duration == -1:
                next_generation[effect_key] = duration

        self.set_stat("effects", next_generation)

    def has_effect(self, check_string):

        agent_effects = self.get_stat('effects')
        if check_string in agent_effects:
            return True
        else:
            return False

    def set_behavior(self, behavior):
        agent_effects = self.get_stat("effects")
        removing_effects = []

        for effect_key in agent_effects:
            if "BEHAVIOR" in effect_key:
                removing_effects.append(effect_key)

        for removing_key in removing_effects:
            del agent_effects[removing_key]

        self.set_stat("effects", agent_effects)

        if behavior:
            if "DEFAULT" in behavior:
                behavior = self.get_stat("default_behavior")

            self.add_effect(behavior, -1)

    def get_behavior(self):
        agent_effects = self.get_stat("effects")

        behavior = None

        for effect_key in agent_effects:
            if "BEHAVIOR" in effect_key:
                behavior = effect_key

        if not behavior:
            behavior = "BEHAVIOR_HOLD"
            self.add_effect("BEHAVIOR_HOLD", -1)

        behavior_string = "_".join(behavior.split("_")[1:])

        return behavior_string

    def add_effect(self, adding_effect, effect_duration):
        agent_effects = self.get_stat("effects")
        agent_effects[adding_effect] = effect_duration
        self.set_stat("effects", agent_effects)

    def clear_effect(self, removing_effect):
        if self.has_effect(removing_effect):
            agent_effects = self.get_stat("effects")
            del agent_effects[removing_effect]
            self.set_stat("effects", agent_effects)
            return True

    def trigger_instant_effect(self, message):

        secondary_actions = ["AMBUSH", "ANTI_AIR_FIRE", "BAILED_OUT", "BUTTONED_UP", "OVERWATCH", "PLACING_MINES",
                             "PRONE", "REMOVING_MINES", "JAMMED", "CRIPPLED", "MOVED", "FAST", "MARKED", "RELIABLE",
                             "UNRELIABLE", "RAW_RECRUITS", "VETERANS", "STAY_BUTTONED_UP", "STAY_PRONE", "CONFUSED",
                             "RECOGNIZED", "IN_BUILDING", "RADIO_JAMMING", "GET_REINFORCEMENT", "EMERGENCY_REPAIR"]

        action_id, target_id, own_id, origin, tile_over, target_type = message["contents"]
        active_action = self.get_stat("action_dict")[action_id]
        triggered = False

        if target_id in self.environment.agents:
            target_agent = self.environment.agents[target_id]
        else:
            if target_id in self.environment.buildings:
                target_position = mathutils.Vector(tile_over).to_3d()
                particles.DebugText(self.environment, "BUILDING UNAFFECTED!", target_position)

            target_agent = None

        # TODO add all effects and animations

        if active_action["effect"] == "TRIGGER_AMBUSH":
            triggered = self.set_ambush()

        if active_action["effect"] == "TRIGGER_ANTI_AIRCRAFT":
            self.trigger_anti_aircraft_fire()
            triggered = True

        if active_action["effect"] == "REINFORCEMENT":
            self.add_effect("GET_REINFORCEMENT", -1)
            triggered = True

        if active_action["effect"] == "EMERGENCY_REPAIR":
            self.attempt_emergency_repair()
            triggered = True

        if active_action["effect"] == "GRAB_SUPPLIES":
            self.attempt_grab_supplies()
            triggered = True

        if active_action["effect"] == "BAILING_OUT":
            self.add_effect("BAILED_OUT", -1)
            self.set_stat("number", 0)
            triggered = True

        if active_action["effect"] == "TOGGLE_BUTTONED_UP":
            if self.has_effect("BUTTONED_UP"):
                self.clear_effect("BUTTONED_UP")
            else:
                self.add_effect("BUTTONED_UP", -1)
            triggered = True

        if target_agent and active_action["effect"] == "DIRECT_ORDER":
            if target_agent.has_effect("HAS_RADIO"):
                actions = target_agent.get_stat("free_actions")
                target_agent.set_stat("free_actions", actions + 1)

            triggered = True
            particles.DebugText(self.environment, "DIRECT ORDER!", target_agent.box.worldPosition.copy())

        if target_agent and active_action["effect"] == "SET_QUICK_MARCH":
            if target_agent.has_effect("HAS_RADIO"):
                target_agent.add_effect("QUICK_MARCH", 3)

            triggered = True
            particles.DebugText(self.environment, "QUICK MARCH!", target_agent.box.worldPosition.copy())

        if target_agent and active_action["effect"] == "RADIO_JAMMING":
            if target_agent.has_effect("HAS_RADIO"):
                target_agent.add_effect("RADIO_JAMMING", 3)
                particles.DebugText(self.environment, "RADIO JAMMED!", target_agent.box.worldPosition.copy())

            triggered = True

        if active_action["effect"] == "REMOVE_JAMMING":
            self.clear_effect("RADIO_JAMMING")
            particles.DebugText(self.environment, "FREQUENCIES CHANGED!", target_agent.box.worldPosition.copy())
            triggered = True

        if target_agent and active_action["effect"] == "RECOVER":
            if target_agent.has_effect("HAS_RADIO"):
                target_agent.set_stat("shock", 0)

            triggered = True

        if target_agent and active_action["effect"] == "LOAD_TROOPS":
            loaded_troops = self.get_stat("loaded_troops")
            max_load = self.get_stat("max_load")

            if len(loaded_troops) < max_load and target_agent.agent_type == "INFANTRY":
                target_agent.load_in_to_transport()

                loaded_troops.append(target_id)
                self.set_stat("loaded_troops", loaded_troops)
                self.environment.turn_manager.update_pathfinder()
                triggered = True
            else:
                particles.DebugText(self.environment, "NOT LOADED!", target_agent.box.worldPosition.copy())

        if active_action["effect"] == "UNLOAD_TROOPS":

            x, y = self.get_stat("position")
            search_array = [[-1, 0], [-1, 1], [1, 0], [1, 1], [0, -1], [1, -1], [0, 1], [-1, -1]]
            unloading_tiles = []

            for n in search_array:
                nx, ny = (x + n[0], y + n[1])
                if 0 <= nx < self.environment.max_x:
                    if 0 <= ny < self.environment.max_y:
                        neighbor_id = (nx, ny)
                        neighbor_tile = self.environment.pathfinder.graph[neighbor_id]
                        if neighbor_tile.check_valid_target():
                            unloading_tiles.append(neighbor_id)

            loaded_troops = self.get_stat("loaded_troops")
            number_loaded = len(loaded_troops)

            for i in range(number_loaded):
                if i < len(unloading_tiles):
                    unloading_id = loaded_troops.pop()
                    unloading_agent = self.environment.agents[unloading_id]
                    unloading_agent.unload_from_transport(unloading_tiles[i])
                    triggered = True

            self.set_stat("loaded_troops", loaded_troops)
            self.environment.turn_manager.update_pathfinder()

        if active_action["effect"] == "SET_OVERWATCH":
            self.add_effect("OVERWATCH", -1)
            triggered = True

        if active_action["effect"] == "PLACE_MINE":
            self.add_effect("PLACING_MINES", 1)
            triggered = True

        if active_action["effect"] == "TOGGLE_PRONE":
            if self.has_effect("PRONE"):
                self.clear_effect("PRONE")
            else:
                self.add_effect("PRONE", -1)
            triggered = True

        if target_agent and active_action["effect"] == "RELOAD":
            target_agent.reload_weapons()
            particles.DebugText(self.environment, "WEAPONS RELOADED!", target_agent.box.worldPosition.copy())
            triggered = True

        if active_action["effect"] == "REMOVE_MINE":
            self.add_effect("REMOVING_MINES", 1)
            triggered = True

        if target_agent and active_action["effect"] == "REPAIR":
            target_agent.repair_damage()
            if target_agent.agent_type != "VEHICLE":
                particles.DebugText(self.environment, "NO EFFECT!", target_agent.box.worldPosition.copy())
            else:
                particles.DebugText(self.environment, "REPAIRING!", target_agent.box.worldPosition.copy())
            triggered = True

        if active_action["effect"] == "SPOTTING":
            self.spot_enemy()
            triggered = True

        if active_action["effect"] == "FAST_RELOAD":
            actions = self.get_stat("action_dict")
            for action_key in actions:
                action = actions[action_key]
                if action["action_type"] == "WEAPON":
                    action["triggered"] = False
                    action["recharged"] = 0
            triggered = True

        if target_agent and active_action["effect"] == "CREW":
            target_agent.set_stat("team", self.get_stat("team"))
            target_agent.clear_effect("BAILED_OUT")
            max_crew = target_agent.get_stat("base_number")
            target_agent.set_stat("number", max_crew)
            target_agent.model = target_agent.add_model()
            triggered = True

        if target_agent and active_action["effect"] == "MARKING":
            target_agent.add_effect("MARKED", 3)
            triggered = True
            particles.DebugText(self.environment, "TARGET MARKED", target_agent.box.worldPosition.copy())

        if target_agent and active_action["effect"] == "RECOGNITION":
            target_agent.add_effect("RECOGNIZED", 3)
            triggered = True
            particles.DebugText(self.environment, "TARGET RECOGNIZED!", target_agent.box.worldPosition.copy())

        if target_agent and active_action["effect"] == "CONFUSION":
            target_agent.add_effect("CONFUSED", -1)
            triggered = True
            particles.DebugText(self.environment, "TARGET CONFUSED!", target_agent.box.worldPosition.copy())

        if active_action["effect"] == "CLEAR_JAM":
            self.clear_effect("JAMMED")
            particles.DebugText(self.environment, "JAM CLEARED!", target_agent.box.worldPosition.copy())
            triggered = True

        if triggered:
            current_cost = active_action["action_cost"]
            free_actions = self.get_stat("free_actions") >= current_cost
            untriggered = not active_action["triggered"]

            if not free_actions or not untriggered:
                self.set_starting_action()
            else:
                if active_action["target"] == "ALLIES":
                    self.set_starting_action()
                if active_action["target"] == "FRIEND":
                    self.set_starting_action()
                if active_action["effect"] == "ROTATE":
                    self.set_starting_action()

    def attempt_grab_supplies(self):
        if self.check_has_supply():
            self.reload_weapons()
            particles.DebugText(self.environment, "RELOADED!", self.box.worldPosition.copy())

        else:
            particles.DebugText(self.environment, "NO SUPPLIES!", self.box.worldPosition.copy())

    def attempt_emergency_repair(self):
        drive_damage = self.get_stat("drive_damage")
        if drive_damage < 1:
            particles.DebugText(self.environment, "NO DAMAGE TO REPAIR!", self.box.worldPosition.copy())

        check = self.emergency_repair_check()
        if check:
            self.set_stat("drive_damage", drive_damage - 1)
            particles.DebugText(self.environment, "REPAIR SUCCESSFUL!", self.box.worldPosition.copy())

        else:
            particles.DebugText(self.environment, "REPAIR FAILED!", self.box.worldPosition.copy())

    def emergency_repair_check(self):
        if self.check_has_supply():
            return True

        repair_attempt = bgeutils.d6(2)
        if repair_attempt == 2:
            return True

        target_number = 3 + self.get_stat("handling") - self.get_stat("drive_damage")

        # TODO add modifiers for unreliable

        if target_number > repair_attempt:
            return True

        return False

    def trigger_reveal(self):
        effects.Reveal(self.environment, self.get_stat("team"), None, self.get_stat("position"), 0)

    def trigger_anti_aircraft_fire(self):
        self.trigger_reveal()

        base_action = None
        success = False
        base_actions = ["SHOOT", "BURST_FIRE"]

        for action_key in self.get_stat("action_dict"):
            action = self.get_stat("action_dict")[action_key]
            if action["action_type"] == "WEAPON":
                if action["weapon_location"] == "turret_primary" and action["action_name"] in base_actions:
                    base_action = action_key

        if base_action:
            for effect_key in self.environment.effects:

                effect = self.environment.effects[effect_key]
                position = mathutils.Vector(effect.position).to_3d()

                if effect.apply_anti_air(self.get_stat("agent_id"), base_action):
                    particles.DebugText(self.environment, "AIRCRAFT INTERDICTED!", position)
                    success = True

                if not success:
                    particles.DebugText(self.environment, "INTERDICTION FAILED!", position)

        self.environment.update_map()

    def set_ambush(self):
        x, y = self.get_stat("position")

        indoors = self.has_effect("IN_BUILDING")

        if not indoors:
            particles.DebugText(self.environment, "NOT IN BUILDING!", self.box.worldPosition.copy())
            return False

        team = self.get_stat("team")

        if team == 1:
            visibility = self.environment.enemy_visibility
        else:
            visibility = self.environment.player_visibility

        visible = visibility.lit(x, y)
        if visible != 0:
            particles.DebugText(self.environment, "AMBUSH FAILED!", self.box.worldPosition.copy())
            return False
        else:
            self.add_effect("AMBUSH", -1)
            particles.DebugText(self.environment, "AMBUSH SET!", self.box.worldPosition.copy())
            return True

    def spot_enemy(self):
        spotting_range = 6
        spotted = False
        team = self.get_stat("team")

        ox, oy = self.get_stat("position")

        for x in range(-spotting_range, spotting_range):
            for y in range(-spotting_range, spotting_range):
                tx = ox + x
                ty = oy + y

                tile = self.environment.get_tile((tx, ty))
                if tile:
                    occupier = tile["occupied"]
                    if occupier:
                        target_agent = self.environment.agents[occupier]
                        target_team = target_agent.get_stat("team")
                        if target_team != team:
                            visible = self.environment.player_visibility.lit(tx, ty)
                            if visible == 2:
                                if random.randint(0, 1):
                                    target_agent.add_effect("SPOTTED", 1)
                                    particles.DebugText(self.environment, "ENEMY SPOTTED!",
                                                        target_agent.box.worldPosition.copy())

                                if target_agent.has_effect("AMBUSH"):
                                    target_agent.clear_effect("AMBUSH")
                                    target_agent.add_effect("SPOTTED", 1)
                                    spotted = True
                                    particles.DebugText(self.environment, "AMBUSH SPOTTED!",
                                                        target_agent.box.worldPosition.copy())

                            else:
                                if random.randint(0, 1):
                                    spotted = True
                                    target_position = target_agent.get_stat("position")

                                    effects.Reveal(self.environment, target_team, None, target_position)
                                    particles.DebugText(self.environment, "ENEMY DETECTED!",
                                                        target_agent.box.worldPosition.copy())

        if spotted:
            self.environment.turn_manager.update_pathfinder()
            # TODO update map
            pass

    def place_mines(self):
        position = self.get_stat("position")
        team = self.get_stat("team")

        target_tile = self.environment.get_tile(position)
        if target_tile:
            mines = target_tile["mines"]
            if mines:
                particles.DebugText(self.environment, "MINES PRESENT!", self.box.worldPosition.copy())
            else:
                particles.DebugText(self.environment, "MINES PLACED!", self.box.worldPosition.copy())
                effects.Mines(self.environment, team, None, position, 0)

    def get_mines(self):
        mines_list = []

        x, y = self.get_stat("position")

        search_array = [[-1, 0], [-1, 1], [1, 0], [1, 1], [0, -1], [1, -1], [0, 1], [-1, -1]]

        for n in search_array:
            neighbor_key = (x + n[0], y + n[1])
            neighbor_tile = self.environment.get_tile(neighbor_key)
            if neighbor_tile:
                mines = neighbor_tile["mines"]

                if mines:
                    mines_list.append(neighbor_tile)

        return mines_list

    def remove_mines(self):
        mines_list = self.get_mines()
        if mines_list:
            if len(mines_list) > 1:
                target_tile = random.choice(mines_list)
            else:
                target_tile = mines_list[0]

                particles.DebugText(self.environment, "MINES REMOVED!", self.box.worldPosition.copy())
                self.environment.remove_effect(target_tile, "mines")

        else:
            particles.DebugText(self.environment, "NO MINES FOUND!", self.box.worldPosition.copy())

    def spread_radio_contact(self):
        # reserve for future tactical plans

        x, y = self.get_stat("position")

        search_array = [[-1, 0], [-1, 1], [1, 0], [1, 1], [0, -1], [1, -1], [0, 1], [-1, -1]]

        for n in search_array:
            neighbor_key = (x + n[0], y + n[1])
            neighbor_tile = self.environment.get_tile(neighbor_key)
            if neighbor_tile:
                if neighbor_tile["occupied"]:
                    target_agent = self.environment.agents[neighbor_tile["occupied"]]
                    radio_contact = target_agent.has_effect("HAS_RADIO_CONTACT")

                    if radio_contact:
                        if target_agent.get_stat("effects")["HAS_RADIO_CONTACT"] != -1:
                            target_agent.add_effect("HAS_RADIO_CONTACT", 1)
                    else:
                        target_agent.add_effect("HAS_RADIO_CONTACT", 1)

                    particles.DebugText(self.environment, "RADIO CONTACT!", target_agent.box.worldPosition.copy())

    def reload_weapons(self):
        base_ammo = self.get_stat("starting_ammo")
        current_ammo = self.get_stat("ammo")

        new_ammo = min(base_ammo, current_ammo + 50)

        self.set_stat("ammo", new_ammo)

    def load_in_to_transport(self):
        self.add_effect("LOADED", -1)
        self.clear_occupied()
        self.set_stat("free_actions", 0)

    def unload_from_transport(self, unloading_tile):
        self.clear_effect("LOADED")
        self.set_stat("position", unloading_tile)
        free_actions = self.get_stat("free_actions")
        reduced = max(0, free_actions - 1)
        self.set_stat("free_actions", reduced)

        self.set_occupied(unloading_tile, rebuild_graph=False)
        self.set_position()
        return True

    def end(self):
        self.clear_occupied()
        self.model.terminate()
        self.box.endObject()


class Vehicle(Agent):
    agent_type = "VEHICLE"

    def __init__(self, environment, position, team, load_key, load_dict):
        super().__init__(environment, position, team, load_key, load_dict)

    def apply_knock(self, origin, damage):

        recoil_vector = self.box.worldPosition.copy() - origin.copy()
        recoil_length = min(0.25, (damage * 0.05))
        recoil_vector.length = recoil_length

        self.model.recoil += recoil_vector

    def drive_damage(self):
        first_save = bgeutils.d6(1)

        if first_save == 1:
            drive_save = bgeutils.d6(1)

            if self.has_effect("UNRELIABLE"):
                drive_damage = 3
            elif self.has_effect("RELIABLE"):
                drive_damage = 1
            else:
                drive_damage = 2

            if self.get_stat("drive_type") == "WHEELED":
                drive_damage += 2
            elif self.get_stat("drive_type") == "HALF_TRACK":
                drive_damage += 1

            if drive_save <= drive_damage:
                particles.DebugText(self.environment, "DRIVE DAMAGED!", self.box.worldPosition.copy())
                self.set_stat("drive_damage", self.get_stat("drive_damage") + drive_damage)

            self.check_drive()

    def check_active_effects(self):
        max_load = self.get_stat("max_load")
        loaded_troops = self.get_stat("loaded_troops")

        loaded = False
        full = False

        if len(loaded_troops) > 0:
            loaded = True
            if len(loaded_troops) >= max_load:
                full = True

        if loaded:
            self.add_effect("LOADED_UP", -1)
        else:
            self.clear_effect("LOADED_UP")

        if full:
            self.add_effect("FULL_LOAD", -1)
        else:
            self.clear_effect("FULL_LOAD")

        ammo_store = self.get_stat("ammo")
        total_ammo = self.get_stat("starting_ammo")

        if total_ammo > 0:
            if ammo_store <= 0:
                self.add_effect("OUT_OF_AMMO", -1)
                self.clear_effect("LOW_AMMO")
            elif ammo_store <= (total_ammo * 0.25):
                self.add_effect("LOW_AMMO", -1)
                self.clear_effect("OUT_OF_AMMO")
            else:
                self.clear_effect("OUT_OF_AMMO")
                self.clear_effect("LOW_AMMO")

        if not self.has_effect("BUTTONED_UP") and not self.has_effect("PRONE"):
            self.add_effect("VISION", -1)
        else:
            self.clear_effect("VISION")

    def repair_damage(self):
        if self.get_stat("drive_damage") > 0:
            self.set_stat("drive_damage", self.get_stat("drive_damage") - 1)

        self.check_drive()


class Artillery(Agent):
    agent_type = "ARTILLERY"

    def __init__(self, environment, position, team, load_key, load_dict):
        super().__init__(environment, position, team, load_key, load_dict)

    def add_model(self):
        if self.model:
            self.model.terminate()

        return vehicle_model.ArtilleryModel(self)

    def get_movement(self):
        return agent_actions.VehicleMovement(self, 0.01)

    def show_damage(self, killed):
        if killed:
            effects.Smoke(self.environment, self.get_stat("team"), None, self.get_stat("position"), 0)
            self.add_effect("DYING", -1)
            position = mathutils.Vector(self.get_stat("position")).to_3d()
            particles.DestroyedVehicle(self.environment, position, self.get_stat("size"))
            self.set_stat("number", 0)

    def apply_knock(self, origin, damage):

        recoil_vector = self.box.worldPosition.copy() - origin.copy()
        recoil_length = min(0.25, (damage * 0.05))
        recoil_vector.length = recoil_length

        self.model.recoil += recoil_vector

    def reinforce_crew(self):
        max_crew = self.get_stat("base_number")
        current_crew = self.get_stat("number")
        new_crew = min(max_crew, current_crew + 1)
        self.set_stat("number", new_crew)
        self.model = self.add_model()


class Infantry(Agent):
    agent_type = "INFANTRY"

    def __init__(self, environment, position, team, load_key, load_dict):
        super().__init__(environment, position, team, load_key, load_dict)

    def get_icon_name(self):

        team = "VIN_"
        if self.get_stat("team") != 1:
            team = "HRR_"

        icon_name = "{}{}".format(team, self.get_stat("mesh"))

        return icon_name

    def add_model(self):
        if self.model:
            self.model.terminate()

        return vehicle_model.InfantryModel(self)

    def reinforce_crew(self):
        max_crew = self.get_stat("base_number")
        current_crew = self.get_stat("number")
        new_crew = min(max_crew, current_crew + 1)
        self.set_stat("number", new_crew)
        toughness = self.get_stat("toughness")
        damage = self.get_stat("hp_damage")
        new_damage = max(0, damage - toughness)
        self.set_stat("hp_damage", new_damage)

        particles.DebugText(self.environment, "REINFORCED!", self.box.worldPosition.copy())

        self.model = self.add_model()

    def get_movement(self):
        return agent_actions.VehicleMovement(self, 0.025)

    def rough_riding(self):
        pass

    def crew_critical(self):
        pass

    def show_damage(self, killed):

        if killed:
            self.add_effect("DYING", -1)
            self.set_stat("number", 0)
        else:
            toughness = self.get_stat("toughness")
            damage = self.get_stat("hp_damage")

            casualties = int(damage / toughness)
            reduction = self.get_stat("base_number") - casualties

            self.set_stat("number", max(1, reduction))

    def check_needs_supply(self):

        if self.has_effect("DYING") or self.has_effect("LOADED") or self.has_effect("AMBUSH"):
            return ["NONE", 2.0, 1000, self]

        base_ammo = self.get_stat("starting_ammo")
        ammo_store = self.get_stat("ammo")
        position = self.get_stat("position")
        movement_cost = self.environment.pathfinder.get_movement_cost(position) * -1

        if base_ammo > 0:
            ammo_ratio = ammo_store / base_ammo
            if ammo_ratio < 1.0:
                return ["REARM_AND_RELOAD", ammo_ratio, movement_cost, self]

        return ["NONE", 2.0, 1000, self]

    def get_mouse_over(self):
        ai_flag = [effect_key for effect_key in self.get_stat("effects") if "BEHAVIOR" in effect_key]
        if self.environment.environment_type != "GAMEPLAY" and ai_flag:
            ai_string = "AI TYPE:{}".format(ai_flag[0])
            agent_effects = self.get_stat("effects")
            effect_list = ["{}:{}".format(".".join((ek[0] for ek in effect_key.split("_"))), agent_effects[effect_key])
                           for
                           effect_key in agent_effects]

            effect_string = "/ ".join(effect_list)

        else:
            ai_string = ""
            effect_string = ""

        agent_args = [self.get_stat("display_name"), self.get_stat("ammo"),
                      self.get_stat("hps") - self.get_stat("hp_damage"), self.get_stat("number"), ai_string,
                      effect_string]

        agent_string = "{}\nAMMO:{}\nHPs:{}\nSOLDIERS:{}\n\n{}\n{}".format(*agent_args)

        return agent_string

    def check_drive(self):

        on_road = self.get_stat("on_road")
        off_road = self.get_stat("off_road")

        return on_road, off_road

    def add_stats(self, position, team):
        infantry_dict = self.environment.infantry_dict.copy()
        base_action_dict = self.environment.action_dict.copy()

        base_stats = infantry_dict[self.load_key].copy()

        base_stats["effects"] = {}
        base_stats["base_accuracy"] = 3
        actions_strings = [action_string for action_string in base_stats["actions"]]

        weapon_stats = {"power": 1, "base_recharge": 0, "base_actions": 0, "name": "infantry_attack", "shots": 1,
                        "mount": "secondary", "jamming_chance": 0}

        basic_actions = ["THROW_GRENADE", "ENTER_BUILDING", "MOVE", "TOGGLE_STANCE", "GRAB_SUPPLIES",
                         "CALL_REINFORCEMENTS", "REDEPLOY", "REMOVE_MINES", "AMBUSH"]

        for adding_action in basic_actions:
            actions_strings.append(adding_action)

        actions = []

        for base_action in actions_strings:
            action_details = base_action_dict[base_action].copy()
            if action_details["action_type"] == "WEAPON":
                action_weapon_stats = weapon_stats.copy()

                if "EXPLOSION" in action_details["effect"] or "SPLASH" in action_details["effect"]:
                    action_weapon_stats["mount"] = "primary"

                modifiers = [["accuracy_multiplier", "accuracy"],
                             ["armor_multiplier", "penetration"],
                             ["damage_multiplier", "damage"],
                             ["shock_multiplier", "shock"]]

                for modifier in modifiers:

                    if modifier[0] == "accuracy_multiplier":
                        base = base_stats["base_accuracy"]
                    else:
                        base = action_weapon_stats["power"]

                    modifier_value = action_details[modifier[0]]
                    new_value = int(round(base * modifier_value))

                    if modifier_value > 1.0:
                        if new_value == base:
                            new_value += 1
                    elif modifier_value < 1.0:
                        if new_value == base:
                            new_value -= 1

                    if new_value < 0:
                        new_value = 0

                    action_weapon_stats[modifier[1]] = new_value

                action_weapon_stats["shots"] = action_details["shot_multiplier"]
                action_details["weapon_name"] = "infantry_attack"
                action_details["weapon_stats"] = action_weapon_stats
                action_details["weapon_location"] = "INFANTRY"

            actions.append(action_details)

        action_dict = {}

        for set_action in actions:
            action_id = self.environment.get_new_id()
            action_key = "{}_{}".format(set_action["action_name"], action_id)
            action_dict[action_key] = set_action

        base_stats["can_supply"] = False
        base_stats["starting_ammo"] = base_stats["ammo"]
        base_stats["on_road"] = 1
        base_stats["off_road"] = 1
        base_stats["handling"] = 6
        base_stats["turret"] = 0
        base_stats["drive_type"] = "infantry"
        base_stats["armor"] = [0, 0]
        base_stats["base_number"] = base_stats["number"]
        base_stats["hps"] = base_stats["toughness"] * base_stats["number"]

        ai_default = base_stats["ai_default"]
        base_stats["default_behavior"] = "BEHAVIOR_{}".format(ai_default)

        base_stats["action_dict"] = action_dict
        base_stats["position"] = position
        base_stats["facing"] = (0, 1)
        base_stats["team"] = team
        base_stats["agent_name"] = self.load_key
        base_stats["shock"] = 0
        base_stats["level"] = 1
        base_stats["base_actions"] = 2
        base_stats["free_actions"] = 2
        id_number = self.environment.get_new_id()
        base_stats["agent_id"] = "{}_{}".format(self.load_key, id_number)
        base_stats["hp_damage"] = 0
        base_stats["drive_damage"] = 0
        base_stats["shock"] = 0
        base_stats['objective_index'] = 9

        return base_stats
