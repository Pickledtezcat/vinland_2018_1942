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
        else:
            self.reload_from_dict(load_dict)

        self.model = self.add_model()
        self.movement = agent_actions.VehicleMovement(self)
        self.set_position()
        self.busy = False

        self.environment.agents[self.get_stat("agent_id")] = self

        if not self.has_effect("DYING"):
            self.set_occupied(self.get_stat("position"), rebuild_graph=False)

        self.set_starting_action()

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
        return vehicle_model.VehicleModel(self, self.agent_hook)

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
        else:
            ai_string = ""

        agent_args = [self.get_stat("agent_id"), self.get_stat("primary_ammo"), self.get_stat("secondary_ammo"),
                      self.get_stat("armor"), self.get_stat("hps") - self.get_stat("hp_damage"),
                      self.get_stat("drive_damage"), ai_string]

        agent_effects = self.get_stat("effects")
        effect_list = ["{}:{}".format(".".join((ek[0] for ek in effect_key.split("_"))), agent_effects[effect_key]) for
                       effect_key in agent_effects]

        effect_string = "/ ".join(effect_list)
        agent_args.append(effect_string)
        agent_string = "{}\nPRIMARY AMMO:{}\nSECONDARY AMMO:{}\nARMOR:{}\nHPs:{}\nDRIVE DAMAGE:{}\n{}\n{}".format(*agent_args)

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

    def in_view(self):
        position = self.box.worldPosition.copy()
        camera = self.box.scene.active_camera
        if camera.pointInsideFrustum(position):
            self.on_screen = True
        else:
            self.on_screen = False

    def check_visible(self):
        self.in_view()

        if not self.environment.player_visibility:
            return False

        if self.has_effect("BAILED_OUT"):
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

    def get_position(self):
        return self.get_stat("position")

    def add_box(self):
        box = self.environment.add_object("agent")
        return box

    def set_position(self):
        self.movement.set_starting_position()

    def regenerate(self):

        base_actions = self.get_stat("base_actions")

        if self.has_effect("PLACING_MINES"):
            self.place_mines()
            self.clear_effect("PLACING_MINES")

        if self.has_effect("REMOVING_MINES"):
            self.remove_mines()
            self.clear_effect("REMOVING_MINES")

        if self.has_effect("CONFUSED"):
            base_actions -= 1
            self.clear_effect("CONFUSED")

        if self.has_effect("OVERWATCH"):
            base_actions += 1
            self.clear_effect("OVERWATCH")

        if self.has_effect("DEAD"):
            self.set_stat("free_actions", 0)

        if self.has_effect("BAILED_OUT"):
            self.set_stat("free_actions", 0)

        if self.has_effect("DYING"):
            self.add_effect("DEAD", -1)
            self.set_stat("free_actions", 0)
            self.clear_occupied()
            self.environment.turn_manager.update_pathfinder()
        else:
            shock = self.get_stat("shock")
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

        self.check_drive()

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

        self.busy = self.process_actions()
        if not self.busy:
            self.process_messages()

    def process_actions(self):

        if not self.movement.done:
            self.movement.update()

            if self.movement.done:
                self.environment.pathfinder.update_graph()
            else:
                return True

        animating = self.model.update()
        if animating:
            return True

        return False

    def add_stats(self, position, team):

        vehicle_dict = self.environment.vehicle_dict.copy()
        weapon_dict = self.environment.weapons_dict.copy()
        base_action_dict = self.environment.action_dict.copy()

        base_stats = vehicle_dict[self.load_key].copy()
        base_stats["base_accuracy"] = 6  # did this get removed?
        base_stats["effects"] = {}

        # TODO set quick march or overdrive based on vehicle type
        # TODO set special actions based on vehicle

        actions = []
        action_strings = ["OVERDRIVE", "TOGGLE_BUTTONED_UP", "BAIL_OUT", "FAST_RELOAD",
                          "MOVE", "FACE_TARGET", "OVERWATCH", "CANCEL_ACTIONS", "STEADY_AIM",
                          "RAPID_FIRE", "SPECIAL_AMMO", "CLEAR_JAM"]

        for action_string in action_strings:
            actions.append(base_action_dict[action_string].copy())

        # TODO add some special abilities

        specials = [special for special in base_stats["special"]]
        radios = ["RADIO", "COMMAND_RADIO", "TACTICAL_RADIO", "AIR_FORCE_RADIO"]

        for special in specials:
            if special == "STORAGE":
                actions.append(base_action_dict["REARM_AND_RELOAD"].copy())
                actions.append(base_action_dict["LOAD_TROOPS"].copy())
                actions.append(base_action_dict["UNLOAD_TROOPS"].copy())
            if special in radios:
                base_stats["effects"]["HAS_RADIO"] = -1
            if special == "COMMAND_RADIO" and "COMMAND_RADIO" not in base_stats["effects"]:
                base_stats["effects"]["COMMAND_RADIO"] = -1
                command_actions = ["QUICK_MARCH", "DIRECT_ORDER", "RECOVER_MORALE", "CHANGE_FREQUENCIES"]

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

            if special == "AA_MOUNT":
                actions.append(base_action_dict["ANTI_AIRCRAFT_FIRE"].copy())

        ai_default = base_stats["ai_default"]
        behavior_string = "BEHAVIOR_{}".format(ai_default)
        base_stats["effects"][behavior_string] = -1

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

        base_stats["starting_ammo"] = [base_stats["primary_ammo"], base_stats["secondary_ammo"]]
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

    def check_needs_supply(self):

        if self.has_effect("DYING") or self.has_effect("LOADED") or self.has_effect("AMBUSH"):
            return ["NONE", 2.0, 1000, self]

        primary_base, secondary_base = self.get_stat("starting_ammo")
        primary_ammo_store = self.get_stat("primary_ammo")
        secondary_ammo_store = self.get_stat("secondary_ammo")
        position = self.get_stat("position")
        movement_cost = self.environment.pathfinder.get_movement_cost(position) * -1

        if self.has_effect("BAILED_OUT"):
            return ["CREW", 0.01, movement_cost, self]

        if primary_base > 0:
            primary_ammo_ratio = primary_ammo_store / primary_base
            if primary_ammo_ratio < 1.0:
                return ["REARM_AND_RELOAD", primary_ammo_ratio, movement_cost, self]

        if secondary_base > 0:
            secondary_ammo_ratio = secondary_ammo_store / secondary_base
            if secondary_ammo_ratio < 1.0:
                return ["REARM_AND_RELOAD", secondary_ammo_ratio, movement_cost, self]

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

        ammo_type = current_action["weapon_stats"]["mount"]

        if ammo_type == "primary":
            ammo_store = self.get_stat("primary_ammo")
        else:
            ammo_store = self.get_stat("secondary_ammo")

        ammo_drain = current_action["weapon_stats"]["power"]
        if ammo_drain > ammo_store:
            return True

        return False

    def check_jammed(self, action_key):
        current_action = self.get_stat("action_dict")[action_key]
        if current_action["action_type"] == "WEAPON":
            if self.has_effect("JAMMED"):
                return True

        return False

    def use_up_ammo(self, action_key):
        if self.check_jammed(action_key):
            particles.DebugText(self.environment, "WEAPONS JAMMED!", self.box.worldPosition.copy())
            return False

        if self.out_of_ammo(action_key):
            particles.DebugText(self.environment, "NO AMMO!", self.box.worldPosition.copy())
            return False

        current_action = self.get_stat("action_dict")[action_key]
        ammo_type = current_action["weapon_stats"]["mount"]
        ammo_drain = current_action["weapon_stats"]["damage"]

        if ammo_type == "primary":
            drain_key = "primary_ammo"
        else:
            drain_key = "secondary_ammo"

        self.set_stat(drain_key, self.get_stat(drain_key) - ammo_drain)
        self.jamming_save(action_key)

        return True

    def jamming_save(self, action_key):
        first_chance = bgeutils.d6(1)
        if first_chance == 1:
            current_action = self.get_stat("action_dict")[action_key]
            jamming_chance = current_action["weapon_stats"]["jamming_chance"]
            jamming_save = bgeutils.d6(1)
            if jamming_save <= jamming_chance:
                self.add_effect("JAMMED", 3)
                particles.DebugText(self.environment, "WEAPONS JAMMED!", self.box.worldPosition.copy())

    def check_action_valid(self, action_key, target_tile):

        results = ["BUSY", "NO_RADIO", "NO_AMMO", "JAMMED", "AIR_SUPPORT", "NO_ACTIONS", "TRIGGERED",
                   "INVISIBLE", "SELECT_FRIEND", "TOO_FAR", "VALID_TARGET"]

        if self.busy:
            return ["BUSY"]

        current_action = self.get_stat("action_dict")[action_key]

        action_cost = current_action["action_cost"]
        current_target = current_action["target"]

        target_agent = None

        mouse_over_tile = self.environment.get_tile(target_tile)
        adjacent = target_tile in self.environment.pathfinder.adjacent_tiles

        if current_target != "MOVE":
            if self.get_stat("free_actions") < action_cost:
                return ["NO_ACTIONS"]

        triggered = current_action["triggered"]
        if triggered:
            return ["TRIGGERED"]

        working_radio = self.has_effect("HAS_RADIO") and not self.has_effect("RADIO_JAMMING")

        if current_target == "AIRCRAFT" and working_radio and mouse_over_tile:
            return ["AIR_SUPPORT"]

        target = mouse_over_tile["occupied"]
        friendly = False

        if target:
            target_agent = self.environment.agents[target]
            if target_agent.get_stat("team") == self.get_stat("team"):
                friendly = True
            else:
                if target_agent.has_effect("AMBUSH") or target_agent.has_effect("BAILED_OUT"):
                    # TODO allow bailed_out tanks to be targeted
                    target_agent = None

        if target_agent:
            target_working_radio = target_agent.has_effect("HAS_RADIO") and not target_agent.has_effect("RADIO_JAMMING")

            if target_agent == self:
                target_type = "SELF"
            elif friendly:
                if adjacent and current_target == "FRIEND":
                    target_type = "FRIEND"
                elif target_working_radio:
                    target_type = "ALLIES"
                else:
                    return ["SELECT_FRIEND", target]
            else:
                target_type = "ENEMY"
        else:
            building = tuple(self.environment.tile_over) in self.environment.pathfinder.building_tiles
            if current_target == "BUILDING" and building and not self.check_immobile():
                return ["BUILDING"]
            else:
                target_type = "MAP"

        allies = ["FRIEND", "ALLIES", "FRIENDLY"]

        if current_target == "FRIEND" and target_type == "ALLIES":
            return ["SELECT_FRIEND", target]

        if current_target not in allies and target_type in allies:
            return ["SELECT_FRIEND", target]

        if current_action["radio_points"] > 0 and not working_radio:
            return ["NO_RADIO"]

        if self.out_of_ammo(action_key):
            return ["NO_AMMO"]

        if self.check_jammed(action_key):
            return ["JAMMED"]

        immobile = self.check_immobile()
        if current_target == "BUILDING" and immobile:
            return ["IMMOBILE"]

        if current_target == "MOVE" and immobile:
            return ["IMMOBILE"]

        movement_cost = self.environment.pathfinder.get_movement_cost(target_tile)
        if current_target == "MOVE":
            if current_action["effect"] == "ROTATE":
                return ["ROTATE"]

            if target_type == "MAP":
                if movement_cost > self.get_stat("free_actions"):
                    return ["TOO_FAR"]
                path = self.environment.pathfinder.current_path[1:]
                if not path:
                    return ["IMPASSABLE"]

                return ["MOVE", movement_cost]

        valid_target = current_target == target_type or (current_target == "MAP" and target_type == "ENEMY")

        if self.get_stat("team") == 1:
            visibility = self.environment.player_visibility.lit(*target_tile)
        else:
            visibility = self.environment.enemy_visibility.lit(*target_tile)

        if current_target == "ENEMY" and visibility < 2:
            visible = False
        elif visibility == 0:
            visible = False
        else:
            visible = True

        if not visible:
            return ["INVISIBLE"]

        if not valid_target:
            return ["INVALID_TARGET"]

        return ["VALID_TARGET", current_target, target_type, target, action_cost]

    def trigger_action(self, action_key, target_tile):

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
                if target:
                    target_agent = self.environment.agents[target]

                header = "PROCESS_ACTION"
                message = {"agent_id": self.get_stat("agent_id"), "header": header,
                           "contents": [action_key, target, self.get_stat("agent_id"),
                                        self.get_stat("position"), target_tile]}

                face_target = False
                if target_type == "FRIEND" or target_type == "ENEMY":
                    face_target = True
                    position = self.get_stat("position")
                    target_position = target_agent.get_stat("position")

                elif target_type == "MAP":
                    face_target = True
                    position = self.get_stat("position")
                    target_position = self.environment.tile_over

                if face_target:
                    target_vector = mathutils.Vector(target_position) - mathutils.Vector(position)
                    best_vector = bgeutils.get_facing(target_vector)
                    if best_vector:
                        if self.movement.done:
                            self.movement.set_target_facing(tuple(best_vector))

                if self.clear_effect("AMBUSH"):
                    particles.DebugText(self.environment, "AMBUSH TRIGGERED!", self.box.worldPosition.copy())

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

        action_id, target_id, owner_id, origin, tile_over = message_contents
        current_action = self.get_stat("action_dict")[action_id]

        if not self.use_up_ammo(action_id):
            return

        location = current_action["weapon_location"]

        if "turret" in location:
            self.model.set_animation("TURRET_SHOOT")

        if "hull" in location:
            self.model.set_animation("HULL_SHOOT")

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

    def trigger_attack(self, message_contents):

        action_id, target_id, owner_id, origin, tile_over = message_contents
        origin_id = self.get_stat("agent_id")

        target_check = self.environment.turn_manager.get_target_data(origin_id, target_id, action_id, tile_over)
        target_type = target_check["target_type"]
        contents = target_check["contents"]

        current_action = self.get_stat("action_dict")[action_id]

        if not self.use_up_ammo(action_id):
            return

        special = []
        if "TRACKS" in current_action["effect"]:
            special.append("TRACKS")

        location = current_action["weapon_location"]

        if "turret" in location:
            self.model.set_animation("TURRET_SHOOT")

        if "hull" in location:
            self.model.set_animation("HULL_SHOOT")

        if target_type == "INVALID":
            print("invalid action, no target")
        else:
            damage, shock, flanked, covered, base_target, armor_target = contents

            message = {"agent_id": target_id, "header": "HIT",
                       "contents": [origin, base_target, armor_target, damage, shock, special]}
            self.environment.message_list.append(message)

    def process_hit(self, hit_message):

        hit = hit_message["contents"]
        in_the_hatch = False

        if hit and not self.has_effect("DYING"):
            origin, base_target, armor_target, damage, shock, special = hit

            self.model.set_animation("HIT")
            attack_roll = bgeutils.d6(2)

            if attack_roll > base_target or attack_roll == 12:
                # TODO add effect to show misses
                particles.DebugText(self.environment, "MISSED", self.box.worldPosition.copy())
            else:
                penetration_roll = bgeutils.d6(1)
                critical = attack_roll == 2

                if "TRACKS" in special:
                    self.drive_damage()

                if "GRENADE" in special:
                    if not self.has_effect("BUTTONED_UP"):
                        if penetration_roll < 4:
                            in_the_hatch = True

                if "DIRECT_HIT" in special:
                    if not self.has_effect("BUTTONED_UP"):
                        if penetration_roll == 1:
                            in_the_hatch = True

                    armor_target += 2

                if critical:
                    armor_target += 2

                if penetration_roll > armor_target and not in_the_hatch:
                    particles.DebugText(self.environment, "DEFLECTION", self.box.worldPosition.copy())
                    self.set_stat("shock", self.get_stat("shock") + int(shock * 0.5))

                else:
                    # TODO add critical hit effects

                    if critical:
                        damage = int(damage * 2)
                        shock = int(shock * 2)
                        self.crew_critical()
                        self.drive_damage()

                    self.set_stat("hp_damage", self.get_stat("hp_damage") + damage)
                    self.set_stat("shock", self.get_stat("shock") + shock)

                    killed = False
                    if self.get_stat("hp_damage") > self.get_stat("hps"):
                        # TODO add death effect
                        killed = True

                    self.show_damage(killed)
                    particles.DebugText(self.environment, "{}".format(damage), self.box.worldPosition.copy())

    def crew_critical(self):
        pass

    def drive_damage(self):
        pass

    def repair_damage(self):
        pass

    def show_damage(self, killed):

        if killed:
            effects.Smoke(self.environment, self.get_stat("team"), None, self.get_stat("position"), 0)
            particles.DummyDebris(self.environment, self.get_stat("position"), 1)
            self.add_effect("DYING", -1)

    def process_messages(self):

        new_messages = self.environment.get_messages(self.get_stat("agent_id"))

        for new_message in new_messages:
            self.messages.append(new_message)

        if self.messages:
            message = self.messages.pop()

            if message["header"] == "FOLLOW_PATH":
                path = message["contents"][0]
                if not self.busy:
                    if self.movement.done:
                        self.movement.set_path(path)

            elif message["header"] == "ENTER_BUILDING":
                path = [message["contents"][0]]
                if not self.busy:
                    if self.movement.done:
                        self.movement.set_path(path)

            elif message["header"] == "TARGET_LOCATION":
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

                    # TODO do target tracks and smoke

                    if "HIT" in active_action["effect"]:
                        message = {"agent_id": message["agent_id"], "header": "TRIGGER_ATTACK",
                                   "contents": message["contents"].copy()}

                    elif "EXPLOSION" in active_action["effect"]:
                        message = {"agent_id": message["agent_id"], "header": "TRIGGER_EXPLOSION",
                                   "contents": message["contents"].copy()}

                    elif "SMOKE" in active_action["effect"]:
                        message = {"agent_id": message["agent_id"], "header": "TRIGGER_EXPLOSION",
                                   "contents": message["contents"].copy()}

                    if self.has_effect("RAPID_FIRE"):
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
                             "RECOGNIZED"]

        action_id, target_id, own_id, origin, tile_over = message["contents"]
        active_action = self.get_stat("action_dict")[action_id]
        agent_effects = self.get_stat("effects")
        triggered = False

        if target_id:
            target_agent = self.environment.agents[target_id]
        else:
            target_agent = None

        # TODO add all effects and animations

        if active_action["effect"] == "TRIGGER_AMBUSH":
            triggered = self.set_ambush()

        if active_action["effect"] == "TRIGGER_ANTI_AIRCRAFT":
            self.trigger_anti_aircraft_fire()
            triggered = True

        if active_action["effect"] == "BAILING_OUT":
            if "BAILED_OUT" not in agent_effects:
                agent_effects["BAILED_OUT"] = -1
                triggered = True

        if active_action["effect"] == "TOGGLE_BUTTONED_UP":
            if "BUTTONED_UP" in agent_effects:
                del agent_effects["BUTTONED_UP"]
            else:
                agent_effects["BUTTONED_UP"] = -1
            triggered = True

        if target_agent and active_action["effect"] == "DIRECT_ORDER":
            if target_agent.has_effect("HAS_RADIO"):
                target_agent.regenerate()

            triggered = True
            particles.DebugText(self.environment, "DIRECT ORDER!", target_agent.box.worldPosition.copy())

        if target_agent and active_action["effect"] == "SET_QUICK_MARCH":
            if target_agent.has_effect("HAS_RADIO"):
                target_agent.add_effect("QUICK_MARCH", 1)

            triggered = True
            particles.DebugText(self.environment, "QUICK MARCH!", target_agent.box.worldPosition.copy())

        if active_action["effect"] == "RADIO_JAMMING":
            if target_agent.has_effect("HAS_RADIO"):
                target_agent.add_effect("RADIO_JAMMING", 3)
                particles.DebugText(self.environment, "RADIO JAMMED!", target_agent.box.worldPosition.copy())

            triggered = True

        if active_action["effect"] == "CHANGE_FREQUENCIES":

            agent_effects = self.get_stat("effects")
            if "RADIO_JAMMING" in agent_effects:
                del agent_effects["RADIO_JAMMING"]
                particles.DebugText(self.environment, "JAMMING OVERCOME!", target_agent.box.worldPosition.copy())
            else:
                particles.DebugText(self.environment, "FREQUENCIES CHANGED!", target_agent.box.worldPosition.copy())

            triggered = True

        if active_action["effect"] == "RECOVER":
            if target_agent.has_effect("HAS_RADIO"):
                target_agent.set_stat("shock", 0)

            triggered = True

        if active_action["effect"] == "LOAD_TROOPS":
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
            agent_effects["OVERWATCH"] = -1
            triggered = True

        if active_action["effect"] == "PLACE_MINE":
            agent_effects["PLACING_MINES"] = 1
            triggered = True

        if active_action["effect"] == "TOGGLE_PRONE":
            if "PRONE" in agent_effects:
                del agent_effects["PRONE"]
            else:
                agent_effects["PRONE"] = -1
            triggered = True

        if active_action["effect"] == "RELOAD":
            target_agent.reload_weapons()
            particles.DebugText(self.environment, "WEAPONS RELOADED!", target_agent.box.worldPosition.copy())
            triggered = True

        if active_action["effect"] == "REMOVE_MINE":
            agent_effects["REMOVING_MINES"] = 1
            triggered = True

        if active_action["effect"] == "REPAIR":
            target_agent.repair_damage()
            if target_agent.agent_type != "VEHICLE":
                particles.DebugText(self.environment, "NO EFFECT!", target_agent.box.worldPosition.copy())
            else:
                particles.DebugText(self.environment, "REPAIRING!", target_agent.box.worldPosition.copy())

            triggered = True

        if active_action["effect"] == "SPOTTING":
            self.spot_enemy_ambush()
            triggered = True

        if active_action["effect"] == "FAST_RELOAD":
            actions = self.get_stat("action_dict")
            for action_key in actions:
                action = actions[action_key]
                if action["action_type"] == "WEAPON":
                    action["triggered"] = False
                    action["recharged"] = 0
            triggered = True

        if target_agent and active_action["effect"] == "MARKING":
            target_agent.add_effect("MARKED", 1)
            triggered = True
            particles.DebugText(self.environment, "TARGET MARKED", target_agent.box.worldPosition.copy())

        if target_agent and active_action["effect"] == "RECOGNITION":
            target_agent.add_effect("RECOGNIZED", 1)
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

        self.set_stat("effects", agent_effects)

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

        if success:
            particles.DebugText(self.environment, "INTERDICTION FAILED!", position)

        self.environment.update_map()

    def set_ambush(self):
        x, y = self.get_stat("position")
        tile = self.environment.get_tile((x, y))
        building_key = tile["building"]
        indoors = False

        if building_key:
            building = self.environment.buildings[building_key]
            if building.get_stat("can_enter") and not building.get_stat("destroyed"):
                indoors = True

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

    def spot_enemy_ambush(self):
        spotting_range = 12
        spotted = False

        ox, oy = self.get_stat("position")

        for x in range(-spotting_range, spotting_range):
            for y in range(-spotting_range, spotting_range):
                tx = ox + x
                ty = oy + y

                visible = self.environment.player_visibility.lit(tx, ty)
                if visible == 2:
                    tile = self.environment.get_tile((tx, ty))
                    if tile:
                        occupier = tile["occupied"]
                        if occupier:
                            target_agent = self.environment.agents[occupier]
                            if target_agent.get_stat("team") != self.get_stat("team"):
                                if target_agent.has_effect("AMBUSH"):
                                    target_agent.clear_effect("AMBUSH")
                                    spotted = True
                                    particles.DebugText(self.environment, "AMBUSH SPOTTED!", target_agent.box.worldPosition.copy())

        if spotted:
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

    def remove_mines(self):
        removed = False

        x, y = self.get_stat("position")

        search_array = [[-1, 0], [-1, 1], [1, 0], [1, 1], [0, -1], [1, -1], [0, 1], [-1, -1]]

        for n in search_array:
            neighbor_key = (x + n[0], y + n[1])
            neighbor_tile = self.environment.get_tile(neighbor_key)
            if neighbor_tile and not removed:
                mines = neighbor_tile["mines"]

                if mines:
                    removed = True
                    particles.DebugText(self.environment, "MINES REMOVED!", self.box.worldPosition.copy())
                    self.environment.remove_effect(neighbor_tile, "mines")

        if not removed:
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
        primary_ammo, secondary_ammo = self.get_stat("starting_ammo")
        current_primary = self.get_stat("primary_ammo")
        current_secondary = self.get_stat("secondary_ammo")

        new_primary = min(primary_ammo, current_primary + 50)
        new_secondary = min(secondary_ammo, current_secondary + 100)

        self.set_stat("primary_ammo", new_primary)
        self.set_stat("secondary_ammo", new_secondary)

    def load_in_to_transport(self):
        self.add_effect("LOADED", -1)
        self.clear_occupied()
        self.set_stat("free_actions", 0)

    def unload_from_transport(self, unloading_tile):
        self.clear_effect("LOADED")
        self.set_stat("position", unloading_tile)
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

    def show_damage(self, killed):
        if killed:
            effects.Smoke(self.environment, self.get_stat("team"), None, self.get_stat("position"), 0)
            particles.DummyDebris(self.environment, self.get_stat("position"), 1)
            self.add_effect("DYING", -1)

    def crew_critical(self):
        crew_save = bgeutils.d6(1)
        if crew_save == 1:
            self.add_effect("BAILED_OUT", -1)
            if self.get_stat("team") == 2:
                self.set_stat("team", 1)

    def drive_damage(self):
        drive_save = bgeutils.d6(1)

        if self.has_effect("UNRELIABLE"):
            drive_damage = 3
        elif self.has_effect("RELIABLE"):
            drive_damage = 1
        else:
            drive_damage = 2

        if drive_save <= drive_damage:
            self.set_stat("drive_damage", self.get_stat("drive_damage") + drive_damage)

        self.check_drive()

    def repair_damage(self):
        if self.get_stat("drive_damage") > 0:
            self.set_stat("drive_damage", self.get_stat("drive_damage") - 1)

        self.check_drive()


class Infantry(Agent):
    agent_type = "INFANTRY"

    def __init__(self, environment, position, team, load_key, load_dict):
        super().__init__(environment, position, team, load_key, load_dict)

    def add_model(self):
        return vehicle_model.InfantryModel(self, self.box)

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

        primary_base, secondary_base = self.get_stat("starting_ammo")
        primary_ammo_store = self.get_stat("primary_ammo")
        secondary_ammo_store = self.get_stat("secondary_ammo")
        position = self.get_stat("position")
        movement_cost = self.environment.pathfinder.get_movement_cost(position) * -1

        if primary_base > 0:
            primary_ammo_ratio = primary_ammo_store / primary_base
            if primary_ammo_ratio < 1.0:
                return ["REARM_AND_RELOAD", primary_ammo_ratio * 2.0, movement_cost, self]

        if secondary_base > 0:
            secondary_ammo_ratio = secondary_ammo_store / secondary_base
            if secondary_ammo_ratio < 1.0:
                return ["REARM_AND_RELOAD", secondary_ammo_ratio * 2.0, movement_cost, self]

        return ["NONE", 2.0, 1000, self]

    def get_mouse_over(self):
        agent_args = [self.get_stat("display_name"), self.get_stat("primary_ammo"), self.get_stat("secondary_ammo"),
                      self.get_stat("hps") - self.get_stat("hp_damage"),
                      self.get_stat("number")]

        agent_string = "{}\nGRENADES:{}\nBULLETS:{}\nHPs:{}\nSOLDIERS:{}".format(*agent_args)

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
        actions_strings = [action_string for action_string in base_stats["actions"]]

        weapon_stats = {"power": 1, "base_recharge": 0, "base_actions": 0, "name": "infantry_attack", "shots": 1,
                        "mount": "secondary", "jamming_chance": 0}

        basic_actions = ["THROW_GRENADE", "ENTER_BUILDING", "MOVE", "TOGGLE_STANCE",
                         "OVERWATCH", "FACE_TARGET", "REMOVE_MINES", "AMBUSH"]

        for adding_action in basic_actions:
            actions_strings.append(adding_action)

        actions = []

        for base_action in actions_strings:
            action_details = base_action_dict[base_action].copy()
            if action_details["action_type"] == "WEAPON":
                action_weapon_stats = weapon_stats.copy()

                if "EXPLOSION" in action_details["effect"]:
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

            if base_action == "FACE_TARGET":
                action_details["action_cost"] = 0

            actions.append(action_details)

        action_dict = {}

        for set_action in actions:
            action_id = self.environment.get_new_id()
            action_key = "{}_{}".format(set_action["action_name"], action_id)
            action_dict[action_key] = set_action

        base_stats["starting_ammo"] = [base_stats["primary_ammo"], base_stats["secondary_ammo"]]
        base_stats["on_road"] = 1
        base_stats["off_road"] = 1
        base_stats["handling"] = 6
        base_stats["turret"] = 0
        base_stats["drive_type"] = "infantry"
        base_stats["armor"] = [0, 0]
        base_stats["base_number"] = base_stats["number"]
        base_stats["hps"] = base_stats["toughness"] * base_stats["number"]

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
