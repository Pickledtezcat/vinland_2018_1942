import bge
import mathutils
import bgeutils
import agent_actions


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
        self.selected_action = None
        self.visible = True
        self.update_health_bar = True
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

    def get_stat(self, stat_string):
        return self.stats[stat_string]

    def set_stat(self, stat_string, value):
        self.stats[stat_string] = value
        self.update_health_bar = True

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
        self.process_messages()
        self.process_actions()

    def process_actions(self):

        if not self.movement.done:
            self.movement.update()
            self.busy = True
            if self.movement.done:
                self.environment.pathfinder.update_graph()
                self.busy = False

    def add_stats(self, position, team):

        vehicle_dict = self.environment.vehicle_dict
        weapon_dict = self.environment.weapons_dict
        action_dict = self.environment.action_dict

        actions = []

        base_stats = vehicle_dict[self.load_key]
        weapon_locations = ["turret_primary", "turret_secondary", "hull_primary", "hull_secondary"]

        for location in weapon_locations:
            weapon_string = base_stats[location]

            if weapon_string:
                weapon = weapon_dict[weapon_string]

                for action in weapon["actions"]:
                    action_details = action_dict[action]
                    action_details["action_cost"] += weapon["base_actions"]
                    action_details["recharge_time"] += weapon["base_recharge"]
                    action_details["weapon_name"] = weapon["name"]
                    action_details["weapon_stats"] = weapon
                    action_details["weapon_location"] = location

                    actions.append(action_details)

            else:
                base_stats[location] = None

        actions.append(action_dict["MOVE"])
        actions.append(action_dict["FACE_TARGET"])

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

    def add_model(self):

        model = self.agent_hook.scene.addObject(self.load_key, self.agent_hook, 0)
        model.setParent(self.agent_hook)

        return model

    def get_position(self):
        return self.get_stat("position")

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
                    path, action_cost = message["contents"]
                    if not self.busy:
                        if self.movement.done:
                            self.movement.set_path(path)
                            self.set_stat("free_actions", self.get_stat("free_actions") - action_cost)

                if message["header"] == "TARGET_LOCATION":
                    position = self.get_stat("position")
                    target_position = message["contents"][0]
                    target_vector = mathutils.Vector(target_position) - mathutils.Vector(position)
                    best_vector = bgeutils.get_facing(target_vector)
                    if best_vector and not self.busy:
                        if self.movement.done:
                            self.movement.set_target_facing(tuple(best_vector))
                            self.set_stat("free_actions", self.get_stat("free_actions") - 1)

    def reload_from_dict(self, load_dict):
        self.stats = load_dict
        self.set_stat("position", tuple(self.get_stat("position")))
        self.set_stat("facing", tuple(self.get_stat("facing")))
        self.load_key = self.get_stat("agent_name")

    def end(self):
        self.clear_occupied()
        self.box.endObject()
        




