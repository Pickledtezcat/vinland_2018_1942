import bge
import mathutils
from agent_states import *
import json
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

        if not load_dict:
            self.stats = self.add_stats(position, team)
        else:
            self.reload_from_dict(load_dict)

        self.model = self.add_model()
        self.set_position()
        self.movement = agent_actions.VehicleMovement(self)
        self.busy = False

        self.set_starting_state()

    def set_starting_state(self):
        self.load_state("AgentStartUp", 0)

    def set_occupied(self):
        position = self.stats["position"]

        if self.occupied:
            self.clear_occupied()

        self.environment.set_tile(position, "occupied", self.stats["agent_id"])
        self.occupied = position

    def clear_occupied(self):
        if self.occupied:
            self.environment.set_tile(self.occupied, "occupied", None)
            self.occupied = None

    def state_machine(self):
        self.state.update()

        next_state = self.state.transition
        if next_state:
            self.state.end()
            self.state = next_state(self)

    def load_state(self, state_name, state_count):
        state_class = globals()[state_name]

        self.state = state_class(self)
        self.state.count = state_count

    def update(self):
        self.state_machine()
        self.process()
        self.movement.update()

    def process(self):
        self.process_messages()

    def add_stats(self, position, team):
        vehicle_path = "D:/projects/vinland_1942/game_folder/saves/test_vehicles.txt"
        with open(vehicle_path, "r") as infile:
            vehicles = json.load(infile)

        weapons_path = "D:/projects/vinland_1942/game_folder/saves/weapons.txt"
        with open(weapons_path, "r") as infile:
            weapons = json.load(infile)

        base_stats = vehicles[self.load_key]

        weapon_locations = ["turret_primary", "turret_secondary", "hull_primary", "hull_secondary"]

        for location in weapon_locations:
            if base_stats[location]:
                weapon = weapons[base_stats[location]]
                base_stats[location] = weapon
            else:
                base_stats[location] = None

        base_stats["position"] = position
        base_stats["facing"] = [0, 1]
        base_stats["team"] = team
        base_stats["agent_name"] = self.load_key
        base_stats["agent_id"] = "{}_{}".format(self.agent_type, self.environment.get_new_id())
        base_stats["drive_damage"] = 0
        base_stats["shock"] = 0

        return base_stats

    def add_model(self):

        model = self.agent_hook.scene.addObject(self.load_key, self.agent_hook, 0)
        model.setParent(self.agent_hook)

        return model

    def get_position(self):
        return self.stats["position"]

    def get_movement_cost(self):
        on_road = self.stats["on_road"] - self.stats["drive_damage"]
        off_road = self.stats["off_road"] - self.stats["drive_damage"]

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
        self.box.worldPosition = mathutils.Vector(self.stats["position"]).to_3d()
        facing = bgeutils.track_vector(self.stats["facing"])
        self.agent_hook.worldOrientation = facing

    def save_to_dict(self):
        self.clear_occupied()
        save_dict = {"stats": self.stats, "state": self.state.name, "state_count": self.state.count,
                     }

        return save_dict

    def process_messages(self):

        messages = self.environment.get_messages(self.stats["agent_id"])

        if not self.busy:
            for message in messages:
                if message["header"] == "FOLLOW_PATH":
                    path, action_cost = message["contents"]
                    if self.state.name == "AgentIdle":
                        if self.movement.done:
                            self.movement.set_path(path)

    def reload_from_dict(self, load_dict):

        self.stats = load_dict["stats"]
        state_name = load_dict["state"]
        state_count = load_dict["state_count"]
        self.load_state(state_name, state_count)

        self.load_key = self.stats["agent_name"]

    def end(self):
        self.clear_occupied()
        self.box.endObject()
        




