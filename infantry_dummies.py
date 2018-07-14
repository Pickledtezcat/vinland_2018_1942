import bge
import mathutils
import particles
import bgeutils
import random

infantry_formations = {"0": [[-6.0, 0.0]],
                       "1": [[0.0, 0.0]],
                       "2": [[-3.0, 0.0], [3.0, 0.0]],
                       "3": [[-4.0, -2.0], [0.0, 2.0], [4.0, -2.0]],
                       "4": [[-2.0, 2.0], [2.0, 2.0], [-2.0, -2.0], [2.0, -2.0]],
                       "5": [[-2.5, 2.0], [2.5, 2.0], [-5.0, -2.0], [0.0, -2.5], [5.0, -2.0]],
                       "6": [[-4.0, 2.0], [0.0, 2.0], [4.0, 2.0], [-5.0, -2.0], [0.0, -2.0], [5.0, -2.0]]}

directions_dict = {(-1, -1): "W",
                   (-1, 0): "NW",
                   (-1, 1): None,
                   (0, 1): "NE",
                   (1, 1): "E",
                   (1, 0): "SE",
                   (1, -1): "S",
                   (0, -1): "SW"}


class InfantrySquad(object):
    def __init__(self, model):
        self.model = model
        self.environment = self.model.environment
        self.agent = self.model.agent
        self.load_name = self.agent.get_stat("mesh")
        self.number = self.agent.get_stat("number")
        self.formation = []
        self.get_formation()
        self.dummies = []
        self.get_dummies()

        self.loaded = False
        self.in_building = False
        self.prone = False
        self.hidden = False

    def get_formation(self):
        base_formation = infantry_formations[str(self.number)]
        new_formation = []

        for position in base_formation:
            new_position = []
            for axis in position:
                axis += random.uniform(-0.03, 0.03)
                new_position.append(axis)
            new_formation.append(new_position)

        self.formation = new_formation

    def get_dummies(self):
        for i in range(self.number):
            dummy = InfantryDummy(self, i)
            self.dummies.append(dummy)

    def set_position(self):
        for dummy in self.dummies:
            dummy.set_position()

    def set_conditions(self):

        if self.agent.has_effect("LOADED"):
            if not self.loaded:
                self.loaded = True
        else:
            if self.loaded:
                self.set_position()
                self.loaded = False

        if self.agent.has_effect("IN_BUILDING"):
            if not self.in_building:
                self.in_building = True
        else:
            if self.in_building:
                self.in_building = False

        if self.in_building or self.loaded:
            self.hidden = True
        else:
            self.hidden = False

        if self.agent.has_effect("PRONE"):
            if not self.prone:
                self.prone = True
                particles.DebugText(self.environment, "GOING PRONE", self.agent.box.worldPosition.copy())
        else:
            if self.prone:
                self.prone = False
                particles.DebugText(self.environment, "GETTING UP", self.agent.box.worldPosition.copy())

        number = self.agent.get_stat("number")
        if self.number != number:
            self.number = number
            self.get_formation()
            particles.DebugText(self.environment, "MAN DOWN!!", self.agent.box.worldPosition.copy())

    def update(self):
        self.set_conditions()

        next_generation = []
        for i in range(len(self.dummies)):
            dummy = self.dummies[i]

            if i >= self.number:
                dummy.terminate()
            else:
                dummy.update()
                next_generation.append(dummy)

        self.dummies = next_generation

    def terminate(self):
        for dummy in self.dummies:
            dummy.terminate()


class InfantryDummy(object):
    def __init__(self, squad, index):
        self.squad = squad
        self.environment = self.squad.environment
        self.load_name = self.squad.load_name
        self.index = index
        self.direction = [0, 1]
        self.box = self.add_box()
        self.speed = 0.02
        self.moving = False
        self.placed = False
        self.prone = False

    def set_index(self, index):
        self.index = index

    def add_box(self):
        # TODO add real mesh

        box = self.environment.add_object("infantry_dummy")
        box.visible = False
        return box

    def update(self):
        if not self.placed:
            self.set_position()
            self.placed = True

        self.move_to_position()
        self.animate_sprite()

    def animate_sprite(self):
        # TODO add animations

        if self.squad.prone:
            if not self.prone:
                self.box.replaceMesh("prone_infantry_dummy")
                self.prone = True
        else:
            if self.prone:
                self.box.replaceMesh("infantry_dummy")
                self.prone = False

        visible = True

        if self.squad.hidden:
            if not self.moving:
                visible = False

        self.box.visible = visible

    def set_position(self):
        position = self.get_position()
        self.box.worldPosition = position

    def move_to_position(self):
        position = self.get_position()
        origin = self.box.worldPosition.copy()

        target_vector = position - origin
        if target_vector.length <= self.speed:
            self.moving = False
        else:
            target_vector.length = self.speed
            self.box.worldPosition += target_vector
            self.moving = True

    def get_position(self):

        if self.squad.hidden:
            location = [0, 0]
        else:
            location = self.squad.formation[self.index]

        position = mathutils.Vector(location).to_3d()

        if self.prone:
            position *= 0.12
        else:
            position *= 0.07

        origin_position = self.squad.agent.agent_hook.worldPosition.copy()
        position.rotate(self.squad.agent.agent_hook.worldOrientation.copy())

        destination = origin_position + position

        return destination

    def terminate(self):
        particles.DeadInfantry(self.environment, self.load_name, self.box.worldPosition.copy())
        self.box.endObject()