import bge
import mathutils
import agent_states
import json
import bgeutils


class Agent(object):
    def __init__(self, environment, position, load_key):
        self.environment = environment
        self.load_key = load_key
        self.state = None

        self.position = position
        self.box = self.add_box()
        self.agent_hook = bgeutils.get_ob("agent_hook", self.box.children)

        self.stats = self.add_stats()
        self.model = self.add_model()

        self.set_starting_state()

    def set_starting_state(self):
        self.state = "AgentStartUp"

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

    def process(self):
        pass

    def add_stats(self):
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

        print(base_stats)
        return base_stats

    def add_model(self):
        model = self.agent_hook.scene.addObject(self.load_key, self.agent_hook, 0)
        model.setParent(self.agent_hook)

        return model

    def add_box(self):
        box = self.environment.scene.addObject("agent", self.environment.game_object, 0)
        box.worldPosition = mathutils.Vector(self.position).to_3d()
        return box

        




