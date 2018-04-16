import bge
import mathutils
import bgeutils
import agent_actions
import vehicle_model
import particles


class Agent(object):
    def __init__(self, environment, position, team, load_key, load_dict):

        self.agent_type = "AGENT"
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

        self.hits = []
        self.hit_timer = 0

        if not load_dict:
            self.stats = self.add_stats(tuple(position), team)
        else:
            self.reload_from_dict(load_dict)

        self.model = self.add_model()
        self.set_position()
        self.movement = agent_actions.VehicleMovement(self)
        self.busy = False

        self.environment.agents[self.get_stat("agent_id")] = self
        self.set_occupied(self.get_stat("position"))

        self.set_starting_action()

    def set_starting_action(self):
        actions = self.get_stat("action_dict")
        for action_key in actions:
            action = actions[action_key]
            if action["action_name"] == "MOVE":
                self.active_action = action_key

    def add_model(self):
        return vehicle_model.VehicleModel(self, self.agent_hook)

    def get_stat(self, stat_string):
        return self.stats[stat_string]

    def set_stat(self, stat_string, value):
        self.stats[stat_string] = value

    def set_occupied(self, position):

        if self.occupied:
            self.clear_occupied()

        self.environment.set_tile(position, "occupied", self.get_stat("agent_id"))
        self.occupied = position

    def clear_occupied(self):
        if self.occupied:
            self.environment.set_tile(self.occupied, "occupied", None)
            self.occupied = None

    def update(self):
        self.process()

    def process(self):
        self.in_view()
        self.process_actions()
        if not self.busy:
            self.process_messages()

    def process_actions(self):

        if self.hits:
            self.process_hits()

        if not self.movement.done:
            self.movement.update()
            self.busy = True
            if self.movement.done:
                self.environment.pathfinder.update_graph()
                self.busy = False

        self.model.update()

        if not self.busy:
            if not self.model.animation_finished:
                self.busy = True
            else:
                self.busy = False

    def add_stats(self, position, team):

        vehicle_dict = self.environment.vehicle_dict.copy()
        weapon_dict = self.environment.weapons_dict.copy()
        base_action_dict = self.environment.action_dict.copy()

        actions = []

        base_stats = vehicle_dict[self.load_key].copy()
        weapon_locations = ["turret_primary", "turret_secondary", "hull_primary", "hull_secondary"]

        for location in weapon_locations:
            weapon_string = base_stats[location]

            if weapon_string:
                weapon = weapon_dict[weapon_string].copy()

                for action in weapon["actions"]:
                    invalid_choice = False

                    primary_actions = ["SHOOT", "BURST_FIRE", "AIMED_SHOT", "CALLED_SHOT"]
                    secondary_actions = ["COAXIAL_FIRE", "COAXIAL_BURST"]

                    if "secondary" in location:
                        if action in primary_actions:
                            invalid_choice = True
                    else:
                        if action in secondary_actions:
                            invalid_choice = True

                    if not invalid_choice:
                        action_details = base_action_dict[action].copy()
                        action_weapon_stats = weapon.copy()

                        modifiers = [["accuracy_multiplier", "accuracy"],
                                     ["armor_multiplier", "penetration"],
                                     ["damage_multiplier", "damage"],
                                     ["shock_multiplier", "shock"]]

                        for modifier in modifiers:
                            if modifier[0] == "accuracy_multiplier":
                                if "turret" in location:
                                    base = 8
                                else:
                                    base = 6
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

        basic_actions = ["OVERDRIVE", "TOGGLE_BUTTONED_UP", "BAIL_OUT", "QUICK_MARCH", "RECOVER_MORALE",
                         "REARM_AND_RELOAD", "DIRECT_ORDER", "MOVE", "FACE_TARGET", "OVERWATCH"]

        for basic_action in basic_actions:
            actions.append(base_action_dict[basic_action].copy())

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
        id_number = self.environment.get_new_id()
        base_stats["agent_id"] = "{}_{}".format(self.load_key, id_number)
        base_stats["hp_damage"] = 0
        base_stats["drive_damage"] = 0
        base_stats["shock"] = 0

        return base_stats

    def get_current_action(self):
        current_action = self.get_stat("action_dict")[self.active_action]
        return current_action

    def trigger_current_action(self):
        if self.busy:
            return False

        action_key = self.active_action
        current_action = self.get_stat("action_dict")[action_key]

        message = None
        action_cost = current_action["action_cost"]
        select = False
        triggered = False
        target_agent = None

        mouse_over_tile = self.environment.get_tile(self.environment.tile_over)

        target = mouse_over_tile["occupied"]

        if target:
            target_agent = self.environment.agents[target]
            if target_agent == self:
                target_type = "SELF"
            elif target_agent.get_stat("team") == self.get_stat("team"):
                target_type = "FRIEND"
            else:
                target_type = "ENEMY"
        else:
            target_type = "MAP"

        current_target = current_action["target"]
        valid_target = current_target == target_type or current_target == "MAP" and target_type == "ENEMY"

        if target_type == "FRIEND" and current_target != "FRIEND":
            self.environment.turn_manager.active_agent = target
            self.environment.pathfinder.update_graph()
            select = True

        elif current_target == "MOVE" and target_type == "MAP":
            if current_action["effect"] == "ROTATE":
                if self.get_stat("free_actions") > 0:
                    message = {"agent_id": self.get_stat("agent_id"), "header": "TARGET_LOCATION",
                               "contents": [self.environment.tile_over]}

                    triggered = True

            else:
                path = self.environment.pathfinder.current_path[1:]

                if path:
                    action_cost = self.environment.pathfinder.movement_cost
                    if action_cost <= self.get_stat("free_actions"):
                        message = {"agent_id": self.get_stat("agent_id"), "header": "FOLLOW_PATH",
                                   "contents": [path]}
                        triggered = True

        elif valid_target:
            current_cost = current_action["action_cost"]
            # TODO check for other validity variables

            free_actions = self.get_stat("free_actions") >= current_cost
            untriggered = not current_action["triggered"]

            if untriggered and free_actions:
                direct_targets = ["SELF", "FRIEND", "ENEMY"]
                if current_target in direct_targets:
                    header = "DIRECT_ACTION"
                else:
                    header = "MAP_ACTION"

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

        if not triggered and not select and self.get_stat("free_actions") < 1:
            self.environment.turn_manager.active_agent = None
            self.environment.turn_manager.check_valid_units()
            select = True

        if message:
            self.environment.message_list.append(message)

        if select:
            self.set_starting_action()
            return True

        if triggered:
            self.set_stat("free_actions", self.get_stat("free_actions") - action_cost)
            current_action["triggered"] = True
            current_action["recharged"] = current_action["recharge_time"]

            # use to debug action triggers
            # particles.DebugText(self.environment, "testing", self.box)

            self.set_starting_action()
            return True

        return False

    def trigger_explosion(self, message_contents):

        action_id, target_id, owner_id, origin, tile_over = message_contents

        current_action = self.get_stat("action_dict")[action_id]
        target_tile = self.environment.get_tile(tile_over)

        if target_tile:
            # TODO add modifiers for movement

            origin = self.get_stat("position")

            weapon = current_action["weapon_stats"]
            accuracy = weapon["accuracy"]
            penetration = weapon["penetration"]
            damage = weapon["damage"]
            shock = weapon["shock"]
            shots = weapon["shots"]

            location = tile_over

            target_vector = mathutils.Vector(origin) - mathutils.Vector(location)

            particles.DummyExplosion(self.environment, tile_over, 2)
            particles.DebugText(self.environment, "BOOM", self.box)

    def trigger_attack(self, message_contents):

        action_id, target_id, owner_id, origin, tile_over = message_contents

        current_action = self.get_stat("action_dict")[action_id]
        target_agent = self.environment.agents[target_id]

        if target_agent:

            # TODO add modifiers for movement and size

            weapon = current_action["weapon_stats"]
            accuracy = weapon["accuracy"]
            penetration = weapon["penetration"]
            damage = weapon["damage"]
            shock = weapon["shock"]
            shots = weapon["shots"]

            for s in range(shots):
                message = {"agent_id": target_id, "header": "HIT",
                           "contents": [origin, accuracy, penetration, damage, shock]}

                self.environment.message_list.append(message)

            print("FIRED")

    def process_hits(self):

        if not self.busy and self.hit_timer > 12:
            hit = self.hits.pop()
            self.hit_timer = 0
        else:
            self.hit_timer += 1
            hit = None

        if hit:
            print("HIT!")
            origin, accuracy, penetration, damage, shock = hit

            facing = self.get_stat("facing")
            location = self.get_stat("position")

            target_vector = mathutils.Vector(origin) - mathutils.Vector(location)
            facing_vector = mathutils.Vector(facing)
            angle = int(round(target_vector.angle(facing_vector) * 57.295779513))

            if angle > 85.0:
                flanked = "FLANKED"
            else:
                flanked = "*"

            cover_facing = tuple(bgeutils.get_facing(target_vector))
            cover_dict = {(0, 1): "NORTH",
                          (1, 0): "EAST",
                          (0, -1): "SOUTH",
                          (-1, 0): "WEST"}

            cover_key = cover_dict[cover_facing]
            tile = self.environment.pathfinder.graph[tuple(location)]

            if cover_key in tile.cover_directions:
                cover = "COVERED"
            else:
                cover = "*"

            attack_string = "{}\n{}".format(flanked, cover)
            particles.DebugText(self.environment, attack_string, self.box)

    def regenerate(self):
        self.set_stat("free_actions", self.get_stat("base_actions"))
        actions = self.get_stat("action_dict")
        for action_key in actions:
            action = actions[action_key]
            if action["triggered"]:
                action["recharged"] -= 1
                if action["recharged"] <= 0:
                    action["triggered"] = False

    def get_position(self):
        return self.get_stat("position")

    def in_view(self):
        position = self.box.worldPosition.copy()
        camera = self.box.scene.active_camera
        if camera.pointInsideFrustum(position):
            self.on_screen = True
        else:
            self.on_screen = False

    def get_movement_cost(self):
        on_road = self.get_stat("on_road") - self.get_stat("drive_damage")
        off_road = self.get_stat("off_road") - self.get_stat("drive_damage")

        if on_road > 0:
            on_road_cost = 1.0 / on_road
        else:
            return False

        if off_road > 0:
            off_road_cost = 1.0 / off_road
        else:
            return False

        return on_road_cost, off_road_cost

    def add_box(self):
        box = self.environment.add_object("agent")
        return box

    def set_position(self):
        self.box.worldPosition = mathutils.Vector(self.get_stat("position")).to_3d()
        facing = bgeutils.track_vector(self.get_stat("facing"))
        self.agent_hook.worldOrientation = facing

    def save_to_dict(self):
        self.clear_occupied()
        return self.stats

    def process_messages(self):

        messages = self.environment.get_messages(self.get_stat("agent_id"))

        for message in messages:
            if message["header"] == "FOLLOW_PATH":
                path = message["contents"][0]
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

            elif message["header"] == "HIT":
                self.hits.append(message["contents"])

            elif message["header"] == "DIRECT_ACTION":
                action_id = message["contents"][0]
                active_action = self.get_stat("action_dict")[action_id]

                if active_action["effect"] == "HIT":
                    self.trigger_attack(message["contents"])

                if "EXPLOSION" in active_action["effect"]:
                    self.trigger_explosion(message["contents"])

            elif message["header"] == "MAP_ACTION":
                action_id = message["contents"][0]
                active_action = self.get_stat("action_dict")[action_id]

                if "EXPLOSION" in active_action["effect"]:
                    self.trigger_explosion(message["contents"])

    def reload_from_dict(self, load_dict):
        self.stats = load_dict
        self.set_stat("position", tuple(self.get_stat("position")))
        self.set_stat("facing", tuple(self.get_stat("facing")))
        self.load_key = self.get_stat("agent_name")

    def end(self):
        self.clear_occupied()
        self.box.endObject()


class Vehicle(Agent):

    def __init__(self, environment, position, team, load_key, load_dict):
        super().__init__(environment, position, team, load_key, load_dict)


class Infantry(Agent):

    def __init__(self, environment, position, team, load_key, load_dict):
        super().__init__(environment, position, team, load_key, load_dict)

    def add_model(self):
        return vehicle_model.InfantryModel(self, self.box)

    def add_stats(self, position, team):
        infantry_dict = self.environment.infantry_dict.copy()
        base_action_dict = self.environment.action_dict.copy()

        base_stats = infantry_dict[self.load_key].copy()
        actions = base_stats["actions"]
        weapon_stats = {"power": 1, "base_recharge": 0, "base_actions": 0, "name": "infantry_attack", "shots": 1,
                        "mount": None}

        action_dict = {}
        for base_action in actions:
            action_details = base_action_dict[base_action].copy()
            action_weapon_stats = weapon_stats.copy()

            modifiers = [["accuracy_multiplier", "accuracy"],
                         ["armor_multiplier", "penetration"],
                         ["damage_multiplier", "damage"],
                         ["shock_multiplier", "shock"]]

            for modifier in modifiers:

                if modifier[0] == "accuracy_multiplier":
                    base = base_stats["accuracy"]
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

            action_id = self.environment.get_new_id()
            action_key = "{}_{}".format(action_details["action_name"], action_id)
            action_dict[action_key] = action_details

        base_stats["on_road"] = 1
        base_stats["off_road"] = 1
        base_stats["handling"] = 6
        base_stats["turret"] = 0
        base_stats["drive_type"] = "infantry"
        base_stats["armor"] = [0, 0, 0]
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
