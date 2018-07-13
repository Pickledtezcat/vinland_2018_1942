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
        self.number = self.model.number
        self.formation = []
        self.get_formation()
        self.dummies = []
        self.get_dummies()

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

    def update(self):
        if self.number != self.model.number:
            self.number = self.model.number
            self.get_formation()

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
        self.speed = 0.04
        self.moving = False
        self.prone = False
        self.hidden = False
        self.placed = False

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

        if self.squad.model.prone:
            if not self.prone:
                self.box.replaceMesh("prone_infantry_dummy")
                self.prone = True
        else:
            if self.prone:
                self.box.replaceMesh("infantry_dummy")
                self.prone = False

        visible = True

        if self.hidden:
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

        if self.squad.model.loaded or self.squad.model.in_building:
            location = [0, 0]
            self.hidden = True
        else:
            location = self.squad.formation[self.index]
            self.hidden = False

        position = mathutils.Vector(location).to_3d()

        if self.prone:
            position *= 0.1
        else:
            position *= 0.07

        origin_position = self.squad.agent.agent_hook.worldPosition.copy()
        position.rotate(self.squad.agent.agent_hook.worldOrientation.copy())

        destination = origin_position + position

        return destination

    def terminate(self):
        particles.DeadInfantry(self.environment, self.load_name, self.box.worldPosition.copy())
        self.box.endObject()
