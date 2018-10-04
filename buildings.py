import bge
import bgeutils
import mathutils
import math
import effects
import particles
import random


class Building(object):
    def __init__(self, environment, position, rotations, load_key, load_dict):

        self.building_type = "normal"
        self.environment = environment
        self.load_key = load_key
        self.mesh_name = "BLD_{}".format(self.load_key)
        self.base_mesh = "{}_base".format(self.mesh_name)
        self.damaged_mesh = "{}_damaged".format(self.mesh_name)
        self.destroyed_mesh = "{}_ruin".format(self.mesh_name)
        self.mesh = self.load_key

        self.stats = None

        if not load_dict:
            self.stats = self.add_stats(tuple(position), rotations)
        else:
            self.reload_from_dict(load_dict)

        self.box = self.add_box()

        self.environment.buildings[self.get_stat("agent_id")] = self
        self.set_position()
        self.set_occupied()

        self.collapsing = 0
        self.damage_applied = 0

    def add_box(self):

        if self.get_stat("destroyed"):
            box = self.environment.add_object(self.damaged_mesh)
        else:
            box = self.environment.add_object(self.base_mesh)

        return box

    def get_mouse_over(self):

        remaining_hps = max(0, self.get_stat("hps") - self.get_stat("damage"))

        building_args = [self.get_stat("building_label"), self.get_stat("height"), remaining_hps,
                         self.get_stat("armor")]

        building_string = "{}\nHEIGHT:{}\nHPs:{}\nARMOR:{}".format(*building_args)
        return building_string

    def set_position(self):
        rotations = self.get_stat("rotations")
        x, y = self.get_stat("position")

        array = (self.get_stat("x_size"), self.get_stat("y_size"))
        if self.get_stat("rotations") % 2 != 0:
            yo, xo = array
        else:
            xo, yo = array

        x_offset = (xo - 1) * 0.5
        y_offset = (yo - 1) * 0.5

        mat_loc = mathutils.Matrix.Translation((x + x_offset, y + y_offset, 0))
        mat_sca = mathutils.Matrix.Scale(1.0, 4)
        mat_rot = mathutils.Matrix.Rotation(math.radians(90 * rotations), 4, 'Z')

        mat_out = mat_loc * mat_rot * mat_sca

        self.box.worldTransform = mat_out

    def get_stat(self, stat_string):
        return self.stats[stat_string]

    def set_stat(self, stat_string, value):
        self.stats[stat_string] = value

    def set_occupied(self):
        self.occupy_setter(self.get_stat("agent_id"))

    def clear_occupied(self):
        self.occupy_setter(None)

    def occupy_setter(self, setting):
        array = (self.get_stat("x_size"), self.get_stat("y_size"))
        position = self.get_stat("position")

        if self.get_stat("rotations") % 2 != 0:
            y, x = array
        else:
            x, y = array

        for xo in range(x):
            for yo in range(y):
                set_tile = (position[0] + xo, position[1] + yo)
                self.environment.set_tile(set_tile, "building", setting)

    def reload_from_dict(self, load_dict):
        self.stats = load_dict
        self.set_stat("position", tuple(self.get_stat("position")))
        self.load_key = self.get_stat("building_name")

    def save_to_dict(self):
        self.clear_occupied()
        return self.stats

    def add_stats(self, position, rotations):

        building_dict = self.environment.building_dict.copy()
        base_stats = building_dict[self.load_key].copy()

        base_stats["destroyed"] = False
        base_stats["position"] = position
        base_stats["rotations"] = rotations
        base_stats["building_name"] = self.load_key
        base_stats["initial_damage"] = False
        id_number = self.environment.get_new_id()
        base_stats["agent_id"] = "{}_{}".format(self.load_key, id_number)

        return base_stats

    def update(self):
        self.process()

        if "f1" in self.environment.input_manager.keys:
            self.set_stat("damage", self.get_stat("damage") + 20)

    def process(self):

        if not self.get_stat("destroyed"):
            if self.damage_applied:
                self.set_stat("damage", self.get_stat("damage") + self.damage_applied)
                self.damage_applied = 0

            self.display_damage()

        print(self.collapsing)

    def display_damage(self):
        if self.get_stat("damage") > self.get_stat("hps"):
            self.destroy()
        elif self.get_stat("damage") > (self.get_stat("hps") * 0.5):
            if self.collapsing == 0:
                self.box.replaceMesh(self.damaged_mesh)
                self.add_partial_explosion()
                self.collapsing = 1

    def add_partial_explosion(self):
        array = (self.get_stat("x_size"), self.get_stat("y_size"))
        position = self.get_stat("position")
        particles.BuildingDestruction(self.environment, position, array, False)

    def add_full_explosion(self):
        array = (self.get_stat("x_size"), self.get_stat("y_size"))
        position = self.get_stat("position")

        particles.BuildingDestruction(self.environment, position, array, True)

        if self.get_stat("rotations") % 2 != 0:
            y, x = array
        else:
            x, y = array

        for xo in range(x):
            for yo in range(y):
                set_tile = [position[0] + xo, position[1] + yo]
                effects.Smoke(self.environment, 1, None, set_tile, 0)

    def destroy(self):

        if self.collapsing == 1 or self.collapsing == 0:
            self.add_full_explosion()

            # TODO add damage to occupiers

        elif self.collapsing > 12:
            self.set_stat("destroyed", True)
            self.box.replaceMesh(self.destroyed_mesh)
            particles.BuildingShell(self.environment, self.box, self.mesh_name)

        self.collapsing += 1

    def end(self):
        self.clear_occupied()
        self.box.endObject()


