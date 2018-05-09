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
        self.set_occupied(self.get_stat("position"), rebuild_graph=False)

        self.set_starting_action()

    def set_active_action(self, new_action):
        self.active_action = new_action
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

        # search_array = [[0, 1, "NORTH"], [1, 0, "EAST"], [0, -1, "SOUTH"], [-1, 0, "WEST"]]

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

    def in_view(self):
        position = self.box.worldPosition.copy()
        camera = self.box.scene.active_camera
        if camera.pointInsideFrustum(position):
            self.on_screen = True
        else:
            self.on_screen = False

    def check_visible(self):
        self.in_view()

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

    def get_position(self):
        return self.get_stat("position")

    def add_box(self):
        box = self.environment.add_object("agent")
        return box

    def set_position(self):
        self.movement.set_starting_position()

    def regenerate(self):
        self.set_stat("free_actions", self.get_stat("base_actions"))
        actions = self.get_stat("action_dict")
        for action_key in actions:
            action = actions[action_key]
            if action["triggered"]:
                action["recharged"] -= 1
                if action["recharged"] <= 0:
                    action["triggered"] = False

        # TODO trigger secondary effects

        if self.has_effect("OVERWATCH"):
            self.set_stat("free_actions", self.get_stat("base_actions") + 1)

        shock = self.get_stat("shock")
        shock = max(0, shock - 10)
        self.set_stat("shock", shock)

        self.set_starting_action()
        self.process_effects()

    def get_movement_cost(self):
        on_road = self.get_stat("on_road") - self.get_stat("drive_damage")
        off_road = self.get_stat("off_road") - self.get_stat("drive_damage")

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
                          "RAPID_FIRE", "SPECIAL_AMMO"]

        for action_string in action_strings:
            actions.append(base_action_dict[action_string].copy())

        # TODO add some special abilities

        for special in base_stats["special"]:
            if special == "STORAGE":
                actions.append(base_action_dict["REARM_AND_RELOAD"].copy())
                actions.append(base_action_dict["LOAD_TROOPS"].copy())
                actions.append(base_action_dict["UNLOAD_TROOPS"].copy())
            if special == "RADIO" or special == "COMMAND_RADIO":
                base_stats["effects"]["HAS_RADIO"] = -1
            if special == "COMMAND_RADIO":
                command_actions = ["QUICK_MARCH", "DIRECT_ORDER", "MARK_TARGET"]
                for command_action in command_actions:
                    actions.append(base_action_dict[command_action].copy())

        weapon_locations = ["turret_primary", "turret_secondary", "hull_primary", "hull_secondary"]

        for location in weapon_locations:
            weapon_string = base_stats[location]

            if weapon_string:
                weapon = weapon_dict[weapon_string].copy()

                for action in weapon["actions"]:
                    # TODO make valid choices based on special tags (sights etc...)
                    # TODO make sure rapid fire isn't added twice, reduce rate of supporting fire,
                    # TODO use quick burst or burst fire only,
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
                        action_details["action_cost"] += min(3, weapon["base_actions"])
                        if action_details["recharge_time"] > 0:
                            action_details["recharge_time"] += weapon["base_recharge"]

                        action_details["weapon_name"] = weapon["name"]
                        action_details["weapon_stats"] = action_weapon_stats
                        action_details["weapon_location"] = location
                        actions.append(action_details)

            else:
                base_stats[location] = None

        action_dict = {}
        for base_action in actions:
            action_id = self.environment.get_new_id()
            action_key = "{}_{}".format(base_action["action_name"], action_id)
            action_dict[action_key] = base_action

        base_stats["action_dict"] = action_dict
        base_stats["position"] = position
        base_stats["facing"] = (0, 1)
        base_stats["team"] = team
        base_stats["agent_name"] = self.load_key
        base_stats["shock"] = 0
        base_stats["level"] = 1
        base_stats["base_actions"] = 3
        base_stats["free_actions"] = 3
        base_stats["loaded_troops"] = []
        base_stats["max_load"] = 4
        id_number = self.environment.get_new_id()
        base_stats["agent_id"] = "{}_{}".format(self.load_key, id_number)
        base_stats["hp_damage"] = 0
        base_stats["drive_damage"] = 0
        base_stats["shock"] = 0

        return base_stats

    def trigger_current_action(self, target_tile=None):
        # TODO set trigger to only allow right click for select friendly unit

        if self.busy:
            return False

        action_key = self.active_action
        current_action = self.get_stat("action_dict")[action_key]
        if current_action["radio_points"] > 0 and not self.has_effect("HAS_RADIO_CONTACT"):
            return False

        current_cost = current_action["action_cost"]
        current_target = current_action["target"]

        message = None
        action_cost = current_action["action_cost"]
        select = False
        triggered = False
        target_agent = None

        if not target_tile:
            target_tile = self.environment.tile_over

        mouse_over_tile = self.environment.get_tile(target_tile)
        adjacent = tuple(self.environment.tile_over) in self.environment.pathfinder.adjacent_tiles
        free_actions = self.get_stat("free_actions") >= current_cost
        untriggered = not current_action["triggered"]
        mobile = not self.check_immobile()

        target = mouse_over_tile["occupied"]

        if target:
            target_agent = self.environment.agents[target]

            if target_agent == self:
                target_type = "SELF"
            elif target_agent.get_stat("team") == self.get_stat("team"):
                if adjacent and current_target == "FRIEND":
                    target_type = "FRIEND"
                elif target_agent.has_effect("HAS_RADIO"):
                    target_type = "ALLIES"
                else:
                    target_type = "FRIENDLY"
            else:
                target_type = "ENEMY"
        else:
            building = tuple(self.environment.tile_over) in self.environment.pathfinder.building_tiles
            if current_target == "BUILDING" and building:
                target_type = "BUILDING"
            else:
                target_type = "MAP"

        valid_target = current_target == target_type or current_target == "MAP" and target_type == "ENEMY"
        allies = ["FRIEND", "ALLIES", "FRIENDLY"]
        friend_or_ally = target_type == "FRIENDLY" or target_type == "ALLIES"

        if target_type == "BUILDING":
            if free_actions and untriggered and mobile:
                message = {"agent_id": self.get_stat("agent_id"), "header": "ENTER_BUILDING",
                           "contents": [self.environment.tile_over]}

                triggered = True

        elif current_target == "FRIEND" and friend_or_ally:
            self.environment.turn_manager.active_agent = target
            self.environment.pathfinder.update_graph()
            select = True

        elif current_target not in allies and target_type in allies:
            self.environment.turn_manager.active_agent = target
            self.environment.pathfinder.update_graph()
            select = True

        elif current_target == "MOVE":
            if mobile:
                if current_action["effect"] == "ROTATE":
                    if free_actions:
                        message = {"agent_id": self.get_stat("agent_id"), "header": "TARGET_LOCATION",
                                   "contents": [target_tile]}

                        triggered = True

                elif target_type == "MAP":
                    path = self.environment.pathfinder.current_path[1:]

                    if path:
                        action_cost = self.environment.pathfinder.movement_cost
                        if action_cost <= self.get_stat("free_actions"):

                            self.add_effect("MOVED", 1)
                            if len(path) > 4:
                                self.add_effect("FAST", 1)

                            message = {"agent_id": self.get_stat("agent_id"), "header": "FOLLOW_PATH",
                                       "contents": [path]}
                            triggered = True

        elif valid_target:
            # TODO check for other validity variables

            visibility = self.environment.player_visibility.lit(*target_tile)
            if target_type == "ENEMY" and visibility < 2:
                visible = False
            elif visibility == 0:
                visible = False
            else:
                visible = True

            if untriggered and free_actions and visible:
                header = "PROCESS_ACTION"
                message = {"agent_id": self.get_stat("agent_id"), "header": header,
                           "contents": [self.active_action, target, self.get_stat("agent_id"),
                                        self.get_stat("position"), self.environment.tile_over]}

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

                # action, target, origin, tile_over
                triggered = True

        if not triggered and not select and (
                not free_actions or not untriggered):
            self.environment.turn_manager.active_agent = None
            self.environment.turn_manager.check_valid_units()
            select = True

        if message:
            self.environment.message_list.append(message)

        if select:
            # self.set_starting_action()
            self.environment.turn_manager.update_pathfinder()
            return True

        if triggered:
            self.set_stat("free_actions", self.get_stat("free_actions") - action_cost)
            if current_action["recharge_time"] > 0:
                current_action["triggered"] = True
                current_action["recharged"] = current_action["recharge_time"]

            # use to debug action triggers
            # particles.DebugText(self.environment, "testing", self.box)

            # self.set_starting_action()
            return True

        return False

    def trigger_explosion(self, message_contents, smoke):

        action_id, target_id, owner_id, origin, tile_over = message_contents
        current_action = self.get_stat("action_dict")[action_id]
        location = current_action["weapon_location"]

        if "turret" in location:
            self.model.set_animation("TURRET_SHOOT")

        if "hull" in location:
            self.model.set_animation("HULL_SHOOT")

        origin_id = self.get_stat("agent_id")
        target_check = self.environment.turn_manager.get_target_data(origin_id, target_id, action_id, tile_over)

        target_type = target_check["target_type"]
        contents = target_check["contents"]

        if target_type == "INVALID":
            print("invalid action, no target")
        else:
            damage, shock, base_target, penetration, reduction = contents

            target_position = mathutils.Vector(tile_over)

            hit_list = []

            scatter = reduction
            roll = bgeutils.d6(2)
            effective_scatter = scatter
            status = "MISS!"

            if roll <= base_target:
                status = "ON TARGET"
                effective_scatter = scatter * 0.5

            particles.DebugText(self.environment, status, self.box)

            scatter_roll = [random.uniform(-effective_scatter, effective_scatter) for _ in range(2)]
            hit_position = target_position + mathutils.Vector(scatter_roll)
            hit_position = bgeutils.position_to_location(hit_position)
            hit_tile = self.environment.get_tile(hit_position)

            if hit_tile:
                if smoke:
                    effects.Smoke(self.environment, None, hit_position, 0)
                    self.environment.turn_manager.update_pathfinder()
                    self.environment.player_visibility.update()
                else:
                    particles.DummyExplosion(self.environment, hit_position, 1)
                    explosion_chart = [0, 8, 16, 32, 64, 126, 256, 1024, 4096]

                    for x in range(-2, 3):
                        for y in range(-2, 3):
                            reduction_index = max(x, y)
                            reduction = explosion_chart[reduction_index]

                            effective_penetration = max(0, penetration - reduction)
                            effective_damage = max(0, damage - reduction)
                            effective_shock = max(0, shock - reduction)

                            if effective_damage > 0:
                                blast_location = (hit_position[0] + x, hit_position[1] + y)
                                blast_tile = self.environment.get_tile(blast_location)
                                if blast_tile:
                                    occupied = blast_tile["occupied"]
                                    if occupied:
                                        effective_accuracy = int(effective_damage * 0.5)
                                        effective_origin = hit_position

                                        target_agent = self.environment.agents[occupied]

                                        facing = target_agent.get_stat("facing")
                                        location = target_agent.get_stat("position")

                                        cover_check = self.environment.turn_manager.check_cover(facing, origin,
                                                                                                location)

                                        flanked, covered, reduction = cover_check
                                        armor = target_agent.get_stat("armor")

                                        if flanked:
                                            armor_value = armor[1]
                                        else:
                                            armor_value = armor[0]

                                        if armor_value == 0:
                                            armor_target = 7
                                        else:
                                            armor_target = max(0, effective_penetration - armor_value)

                                        if target_agent.agent_type == "INFANTRY":
                                            base_target = target_agent.get_stat("number")
                                        else:
                                            base_target = target_agent.get_stat("size")

                                        if target_agent.has_effect("PRONE"):
                                            effective_accuracy -= 2
                                        if covered:
                                            effective_accuracy -= 2

                                        base_target += effective_accuracy
                                        message = {"agent_id": occupied, "header": "HIT",
                                                   "contents": [effective_origin, base_target,
                                                                armor_target, effective_damage,
                                                                effective_shock]}
                                        hit_list.append(message)

            for hit_message in hit_list:
                self.environment.message_list.append(hit_message)

    def trigger_attack(self, message_contents):

        action_id, target_id, owner_id, origin, tile_over = message_contents
        origin_id = self.get_stat("agent_id")

        target_check = self.environment.turn_manager.get_target_data(origin_id, target_id, action_id, tile_over)
        target_type = target_check["target_type"]
        contents = target_check["contents"]

        current_action = self.get_stat("action_dict")[action_id]
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
                       "contents": [origin, base_target, armor_target, damage, shock]}
            self.environment.message_list.append(message)

    def process_hit(self, hit_message):

        hit = hit_message["contents"]
        if hit:
            origin, base_target, armor_target, damage, shock = hit

            self.model.set_animation("HIT")
            attack_roll = bgeutils.d6(2)

            if attack_roll > base_target or attack_roll == 12:
                # TODO add effect to show misses
                particles.DebugText(self.environment, "MISSED", self.box)
            else:
                penetration_roll = bgeutils.d6(1)
                if penetration_roll > armor_target:
                    particles.DebugText(self.environment, "DEFLECTION", self.box)

                else:
                    critical = attack_roll == 2
                    # TODO add critical hit effects

                    if critical:
                        damage = int(damage * 2)
                        shock = int(shock * 2)

                    self.set_stat("hp_damage", self.get_stat("hp_damage") + damage)
                    self.set_stat("shock", self.get_stat("shock") + shock)

                    if self.get_stat("hp_damage") > self.get_stat("hps"):
                        message = {"agent_id": self.get_stat("agent_id"), "header": "DESTROYED",
                                   "contents": None}

                        effects.Smoke(self.environment, None, self.get_stat("position"), 0)
                        self.environment.message_list.append(message)

                    particles.DebugText(self.environment, "{}".format(damage), self.box)

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
                        message = {"agent_id": message["agent_id"], "header": "TRIGGER_SMOKE",
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
                particles.DebugText(self.environment, action_id, self.box)

            elif message["header"] == "HIT":
                self.process_hit(message)

            elif message["header"] == "TRIGGER_ATTACK":
                self.trigger_attack(message["contents"])

            elif message["header"] == "TRIGGER_EXPLOSION":
                self.trigger_explosion(message["contents"], False)

            elif message["header"] == "TRIGGER_SMOKE":
                self.trigger_explosion(message["contents"], True)

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

    def add_effect(self, adding_effect, effect_duration):
        agent_effects = self.get_stat("effects")
        agent_effects[adding_effect] = effect_duration
        self.set_stat("effects", agent_effects)

    def trigger_instant_effect(self, message):

        secondary_actions = ["AMBUSH", "ANTI_AIR_FIRE", "BAILED_OUT", "BUTTONED_UP", "OVERWATCH", "PLACING_MINES",
                             "PRONE", "REMOVING_MINES", "JAMMED", "CRIPPLED", "MOVED", "FAST"]

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
            if "AMBUSH" not in agent_effects:
                agent_effects["AMBUSH"] = -1
                triggered = True

        if active_action["effect"] == "TRIGGER_ANTI_AIRCRAFT":
            if "ANTI_AIR_FIRE" not in agent_effects:
                agent_effects["ANTI_AIR_FIRE"] = 1
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
            particles.DebugText(self.environment, "DIRECT ORDER!", target_agent.box)

        if target_agent and active_action["effect"] == "SET_QUICK_MARCH":
            if target_agent.has_effect("HAS_RADIO"):
                target_agent.add_effect("QUICK_MARCH", 1)

            triggered = True
            particles.DebugText(self.environment, "QUICK MARCH!", target_agent.box)

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
                particles.DebugText(self.environment, "NOT LOADED!", target_agent.box)

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
            agent_effects["OVERWATCH"] = 1
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
            # TODO handle reloading friendly troops
            triggered = True

        if active_action["effect"] == "REMOVE_MINE":
            agent_effects["REMOVING_MINES"] = 1
            triggered = True

        if active_action["effect"] == "REPAIR":
            # TODO handle repairing friendly troops
            triggered = True

        if active_action["effect"] == "SPOTTING":
            # TODO handle revealing ambush troops
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
            # TODO handle marking enemy troops
            target_agent.add_effect("MARKED", 1)
            triggered = True
            particles.DebugText(self.environment, "MARKED", target_agent.box)

        if active_action["effect"] == "CLEAR_JAM":
            # TODO handle clear jam
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

                    particles.DebugText(self.environment, "RADIO CONTACT!", target_agent.box)

    def load_in_to_transport(self):
        self.add_effect("LOADED", -1)
        self.clear_occupied()
        self.set_stat("free_actions", 0)

    def unload_from_transport(self, unloading_tile):
        agent_effects = self.get_stat("effects")
        if "LOADED" in agent_effects:
            del agent_effects["LOADED"]
        self.set_stat("effects", agent_effects)
        self.set_stat("position", unloading_tile)
        self.set_occupied(unloading_tile, rebuild_graph=False)
        self.set_position()
        return True

    def end(self):
        self.clear_occupied()
        self.box.endObject()


class Vehicle(Agent):
    agent_type = "VEHICLE"

    def __init__(self, environment, position, team, load_key, load_dict):
        super().__init__(environment, position, team, load_key, load_dict)


class Infantry(Agent):
    agent_type = "INFANTRY"

    def __init__(self, environment, position, team, load_key, load_dict):
        super().__init__(environment, position, team, load_key, load_dict)

    def add_model(self):
        return vehicle_model.InfantryModel(self, self.box)

    def add_stats(self, position, team):
        infantry_dict = self.environment.infantry_dict.copy()
        base_action_dict = self.environment.action_dict.copy()

        base_stats = infantry_dict[self.load_key].copy()
        base_stats["effects"] = {}

        actions_strings = base_stats["actions"]
        weapon_stats = {"power": 1, "base_recharge": 0, "base_actions": 0, "name": "infantry_attack", "shots": 1,
                        "mount": None}

        basic_actions = ["THROW_GRENADE", "ENTER_BUILDING", "MOVE", "TOGGLE_STANCE",
                         "OVERWATCH", "FACE_TARGET", "REMOVE_MINES"]

        for basic_action in basic_actions:
            actions_strings.append(basic_action)

        actions = []

        for base_action in actions_strings:
            action_details = base_action_dict[base_action].copy()
            action_weapon_stats = weapon_stats.copy()

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

            if base_action == "FACE_TARGET":
                action_details["action_cost"] = 0

            action_details["weapon_name"] = "infantry_attack"
            action_details["weapon_stats"] = action_weapon_stats
            action_details["weapon_location"] = "INFANTRY"

            actions.append(action_details)

        action_dict = {}
        for base_action in actions:
            action_id = self.environment.get_new_id()
            action_key = "{}_{}".format(base_action["action_name"], action_id)
            action_dict[action_key] = base_action

        base_stats["on_road"] = 1
        base_stats["off_road"] = 1
        base_stats["handling"] = 6
        base_stats["turret"] = 0
        base_stats["drive_type"] = "infantry"
        base_stats["armor"] = [0, 0]
        base_stats["hps"] = base_stats["toughness"] * base_stats["number"]

        base_stats["action_dict"] = action_dict
        base_stats["position"] = position
        base_stats["facing"] = (0, 1)
        base_stats["team"] = team
        base_stats["agent_name"] = self.load_key
        base_stats["shock"] = 0
        base_stats["level"] = 1
        base_stats["base_actions"] = 3
        base_stats["free_actions"] = 3
        id_number = self.environment.get_new_id()
        base_stats["agent_id"] = "{}_{}".format(self.load_key, id_number)
        base_stats["hp_damage"] = 0
        base_stats["drive_damage"] = 0
        base_stats["shock"] = 0

        return base_stats
