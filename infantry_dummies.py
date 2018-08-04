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


artillery_formations = {"0": [[-4.0, -3.0]],
                        "1": [[-4.0, -3.0]],
                        "2": [[-4.0, -2.0], [3.0, -2.0]],
                        "3": [[-4.0, -2.0], [0.0, -5.0], [4.0, -2.0]],
                        "4": [[-4.0, -2.0], [4.0, -2.0], [-2.0, -5.0], [2.0, -5.0]],
                        "5": [[-2.5, -2.0], [2.5, -2.0], [-5.0, -4.0], [0.0, -4.5], [5.0, -4.0]],
                        "6": [[-4.0, -2.0], [0.0, -2.0], [4.0, -2.0], [-5.0, -4.0], [0.0, -4.0], [5.0, -4.0]]}


directions_dict = {(1, 1): None,
                   (1, 0): "NE",
                   (1, -1): "E",
                   (0, -1): "SE",
                   (-1, -1): "S",
                   (-1, 0): "SW",
                   (-1, 1): "W",
                   (0, 1): "NW"}


class InfantrySquad(object):
    def __init__(self, model):
        self.model = model
        self.environment = self.model.environment
        self.agent = self.model.agent
        self.load_name = self.agent.get_stat("mesh")
        self.number = self.agent.get_stat("number")
        self.formation = []
        self.dummies = []
        self.get_dummies()
        self.get_formation()

        self.rapid = False
        self.shooting = False
        self.loaded = False
        self.in_building = False
        self.prone = False
        self.hidden = False
        self.team = self.agent.get_stat("team")

    def get_formation(self):
        if self.agent.agent_type == "INFANTRY":
            base_formation = infantry_formations[str(self.number)]
        else:
            base_formation = artillery_formations[str(self.number)]

        new_formation = []

        for position in base_formation:
            new_position = []
            for axis in position:
                axis += random.uniform(-0.08, 0.08)
                new_position.append(axis)
            new_formation.append(new_position)

        random.shuffle(self.dummies)
        for i in range(len(self.dummies)):
            dummy = self.dummies[i]
            dummy.index = i

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
        visible = self.model.currently_visible

        next_generation = []
        for i in range(len(self.dummies)):
            dummy = self.dummies[i]

            if i >= self.number:
                dummy.terminate()
            else:
                if visible:
                    dummy.update()
                else:
                    dummy.set_position()

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
        self.shooting = False
        self.weapon_triggered = False
        self.placed = False
        self.prone = False
        self.switching_stance = False
        self.current_mesh = None
        self.frame = random.randint(0, 3)
        self.frame_timer = 0.0
        self.fidget = False
        self.animation_speed = 0.02
        self.north = random.choice(["NE", "NW"])
        self.direction = (0, -1)
        self.switching_direction = 0.0

    def add_box(self):
        # TODO add real mesh

        box = self.environment.add_object("2_ENGINEER_shoot$S_2")
        box.visible = False
        return box

    def update(self):
        if not self.placed:
            self.set_position()
            self.placed = True

        self.move_to_position()
        self.animate_sprite()

    def get_cardinal(self):
        cardinal = directions_dict[self.direction]
        if cardinal:
            return cardinal
        else:
            return self.north

    def shoot_bullet(self):
        if not self.weapon_triggered:
            self.weapon_triggered = True
            if self.squad.model.target_location:
                particles.InfantryBullet(self.environment, self.box.worldPosition, self.squad.model.target_location,
                                         self.squad.model.action["action_name"])

    def animate_sprite(self):
        if self.squad.prone:
            if not self.prone:
                self.switching_stance = True
                self.frame = 0
                self.prone = True
        else:
            if self.prone:
                self.switching_stance = True
                self.frame = 0
                self.prone = False

        team = self.squad.team
        cardinal = self.get_cardinal()
        load_name = self.load_name
        frame = self.frame

        self.animation_speed = 0.2

        if self.shooting:
            if self.squad.rapid:
                self.animation_speed = 0.2
            else:
                self.animation_speed = 0.08

        elif self.switching_stance:
            self.animation_speed = 0.08

        self.frame_timer += self.animation_speed

        if self.squad.shooting:
            if not self.shooting:
                self.shoot_bullet()
                self.shooting = True
                self.frame = 0

        if self.frame_timer > 1.0:
            if self.frame == 3:
                self.shoot_bullet()
                self.weapon_triggered = False
                self.frame = 0

                if self.switching_stance:
                    self.switching_stance = False
                if self.squad.shooting:
                    if not self.shooting:
                        self.shooting = True
                        self.frame = 0
                else:
                    if self.shooting:
                        self.shooting = False
                if self.fidget:
                    self.frame = random.randint(0, 3)

                if self.squad.model.playing:
                    self.fidget = True
                else:
                    self.fidget = random.choice([True, False, False])
            else:
                self.frame += 1
            self.frame_timer = 0

        if self.switching_stance:
            if not self.prone:
                stance = "get_up"
            else:
                stance = "go_prone"

        elif self.moving:
            if self.prone:
                stance = "prone_crawl"
            else:
                stance = "walk"

        elif self.shooting:
            if self.prone:
                stance = "prone_shoot"
            else:
                stance = "shoot"

        else:
            if self.prone:
                stance = "get_up"
                frame = 0
            else:
                if not self.fidget:
                    frame = 0
                stance = "default"

        mesh_name = "{}_{}_{}${}_{}".format(team, load_name, stance, cardinal, frame)

        if self.current_mesh != mesh_name:
            self.box.replaceMesh(mesh_name)

        visible = True

        if self.squad.hidden:
            if not self.moving:
                visible = False

        self.box.visible = visible

    def set_position(self):
        position = self.get_position()
        self.box.worldPosition = position

    def get_direction(self, vector):

        if vector:
            direction = tuple(bgeutils.get_facing(vector))
            if self.direction != direction:
                if self.switching_direction >= 1.0:
                    self.direction = direction
                    self.switching_direction = 0.0
                else:
                    self.switching_direction += 0.2

    def move_to_position(self):
        position = self.get_position()
        origin = self.box.worldPosition.copy()

        target_vector = position - origin
        if target_vector.length <= self.speed:
            self.get_direction(self.squad.agent.agent_hook.getAxisVect([0.0, 1.0, 0.0]))
            self.moving = False
        else:
            target_vector.length = self.speed
            self.get_direction(target_vector)
            self.box.worldPosition += target_vector
            self.moving = True

    def get_position(self):

        if self.squad.hidden:
            location = [0, 0]
        else:
            location = self.squad.formation[self.index]

        position = mathutils.Vector(location).to_3d()

        if self.prone:
            position *= 0.09
        else:
            position *= 0.06

        origin_position = self.squad.agent.agent_hook.worldPosition.copy()
        position.rotate(self.squad.agent.agent_hook.worldOrientation.copy())

        destination = origin_position + position

        return destination

    def terminate(self):

        team = self.squad.team
        if self.prone:
            stance = "prone_death"
        else:
            stance = "death"

        load_name = self.load_name

        cardinal_choices = ["NE", "E", "SE", "S", "SW", "W", "NW"]
        cardinal = random.choice(cardinal_choices)

        mesh_name = "{}_{}_{}${}".format(team, load_name, stance, cardinal)

        particles.DeadInfantry(self.environment, mesh_name, self.box.worldPosition.copy())
        self.box.endObject()
