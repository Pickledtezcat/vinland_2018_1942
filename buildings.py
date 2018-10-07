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

        self.damage_applied = 0

        self.box = self.add_box()
        self.set_display_mesh()

        self.environment.buildings[self.get_stat("agent_id")] = self
        self.set_position()
        self.set_occupied()

    def add_box(self):

        box = self.environment.add_object(self.base_mesh)
        return box

    def set_display_mesh(self):
        damage_stage = self.get_stat("damage_stage")

        if damage_stage == 0:
            self.box.replaceMesh(self.base_mesh)

        else:
            self.box.replaceMesh(self.damaged_mesh)

        if self.get_stat("destroyed"):
            self.box.replaceMesh(self.destroyed_mesh)

    def get_mouse_over(self):

        remaining_hps = max(0, self.get_stat("hps") - self.get_stat("damage"))

        building_args = [self.get_stat("building_label"), self.get_stat("height"), remaining_hps,
                         self.get_stat("armor")]

        building_string = "{}\nHEIGHT:{}\nHPs:{}\nARMOR:{}".format(*building_args)
        return building_string

    def set_position(self):
        rotations = self.get_stat("rotations")
        x, y = self.get_stat("position")

        array = self.get_array()
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
        array = self.get_array()
        x, y = array
        position = self.get_stat("position")

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

        new_messages = self.environment.get_messages(self.get_stat("agent_id"))
        for message in new_messages:
            if message["header"] == "HIT":
                self.process_hit(message)

        if not self.get_stat("destroyed"):
            if self.damage_applied:
                self.set_stat("damage", self.get_stat("damage") + self.damage_applied)
                self.damage_applied = 0

            self.display_damage()

    def get_variance(self, variance, position):
        v = variance
        random_vector = mathutils.Vector([random.uniform(-v, v), random.uniform(-v, v), 0.02])
        target_position = position.copy()
        target_position += random_vector

        return target_position

    def process_hit(self, hit_message):

        hit = hit_message["contents"]
        penetrated = False
        damage = 3
        special = []
        area_effect = "SPLASH" in special or "RANGED_ATTACK" in special or "GRENADE" in special

        if hit:
            origin, base_target, armor_target, damage, shock, special, hit_location = hit
            if area_effect:
                damage = int(damage * 0.5)

            if damage > 0:
                hit_position = mathutils.Vector(hit_location).to_3d()
                hit_variance = self.get_variance(0.5, hit_position)

                attack_roll = bgeutils.d6(2)
                critical = attack_roll == 2

                visual_effect = damage
                penetration_roll = bgeutils.d6(1)

                if critical:
                    armor_target += 2

                if penetration_roll <= armor_target:
                    penetrated = True
                    if critical:
                        damage *= 2

                    particles.DebugText(self.environment, damage, hit_variance)
                    self.damage_applied += damage

                if penetrated:
                    particles.ShellImpact(self.environment, hit_position, visual_effect)
                else:
                    particles.ShellDeflection(self.environment, hit_position, visual_effect)

    def check_valid_target(self):
        if self.get_stat("destroyed"):
            return False

        return True

    def display_damage(self):

        if self.get_stat("damage") >= self.get_stat("hps"):
            damage_state = 2
        elif self.get_stat("damage") >= int((self.get_stat("hps") * 0.5)):
            damage_state = 1
        else:
            damage_state = 0

        if self.get_stat("damage_stage") != damage_state:
            self.set_stat("damage_stage", damage_state)
            self.set_display_mesh()
            self.add_partial_explosion()

    def get_array(self):
        if self.get_stat("rotations") % 2 == 0:
            return self.get_stat("x_size"), self.get_stat("y_size")
        else:
            return self.get_stat("y_size"), self.get_stat("x_size")

    def add_partial_explosion(self):
        array = self.get_array()
        position = self.get_stat("position")
        particles.BuildingDestruction(self.environment, position, array, False)

    def add_full_explosion(self):
        array = self.get_array()
        position = self.get_stat("position")
        particles.BuildingDestruction(self.environment, position, array, True)

    def destroy(self):
        self.add_full_explosion()
        self.set_stat("destroyed", True)
        self.crush_occupiers()
        self.set_display_mesh()
        particles.BuildingShell(self.environment, self.box, self.mesh_name)

    def crush_occupiers(self):
        array = self.get_array()
        x, y = array
        position = self.get_stat("position")

        for xo in range(x):
            for yo in range(y):
                check_tile = (position[0] + xo, position[1] + yo)
                tile = self.environment.get_tile(check_tile)
                if tile:
                    if tile["occupied"]:
                        crush_target = self.environment.agents[tile["occupied"]]
                        crush_target.crush_kill()

    def turn_cycle(self):
        if not self.get_stat("destroyed"):
            if self.get_stat("damage_stage") == 2:
                self.destroy()

    def end(self):
        self.clear_occupied()
        self.box.endObject()


