import bge
import mathutils
import bgeutils
import agent_actions
import vehicle_model


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

        # TODO always set update_health bar on finishing an action or taking damage

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
        self.process_messages()
        self.process_actions()

    def process_actions(self):

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
                    action_details = base_action_dict[action].copy()
                    action_details["action_cost"] += weapon["base_actions"]
                    action_details["recharge_time"] += weapon["base_recharge"]
                    action_details["weapon_name"] = weapon["name"]
                    action_details["weapon_stats"] = weapon
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
        current_action = self.get_stat("action_dict")[self.active_action]

        message = None
        action_cost = current_action["action_cost"]
        triggered = False

        mouse_over_tile = self.environment.get_tile(self.environment.tile_over)

        target = mouse_over_tile["occupied"]
        if target:
            if target == self:
                target_type = "SELF"
            elif target.get_stat("team") == self.get_stat("team"):
                target_type = "FRIEND"
            else:
                target_type = "ENEMY"
        else:
            target_type = "MAP"

        current_target = current_action["target"]
        if current_target == "MOVE" and target_type == "MAP":
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

        elif current_target == target_type:
            current_cost = current_action["action_cost"]
            if self.get_stat("free_actions") >= current_cost:
                direct_targets = ["SELF", "FRIEND", "ENEMY"]
                if current_target in direct_targets:
                    header = "DIRECT_ACTION"
                else:
                    header = "MAP_ACTION"

                message = {"agent_id": None, "header": header,
                           "contents": [self.active_action, target, self.get_stat("agent_id"),
                                        self.environment.tile_over]}

                # action, target, origin, tile_over
                triggered = True

        if message:
            self.environment.message_list.append(message)

        if triggered:
            self.set_stat("free_actions", self.get_stat("free_actions") - action_cost)
            self.set_starting_action()
            current_action["triggered"] = True
            current_action["recharged"] = current_action["recharge_time"]

            return True

        return False

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

        if not self.busy:
            for message in messages:
                if message["header"] == "FOLLOW_PATH":
                    path = message["contents"][0]
                    if not self.busy:
                        if self.movement.done:
                            self.movement.set_path(path)

                if message["header"] == "TARGET_LOCATION":
                    position = self.get_stat("position")
                    target_position = message["contents"][0]
                    target_vector = mathutils.Vector(target_position) - mathutils.Vector(position)
                    best_vector = bgeutils.get_facing(target_vector)
                    if best_vector and not self.busy:
                        if self.movement.done:
                            self.movement.set_target_facing(tuple(best_vector))

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
            action_details["weapon_name"] = "infantry_attack"
            action_details["weapon_stats"] = weapon_stats.copy()
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
