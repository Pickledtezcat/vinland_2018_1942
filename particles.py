import bge
import mathutils
import random
import bgeutils


particle_ranges = {"chunk_1": 8,
                   "dirt_1": 8,
                   "gun_flash": 4,
                   "after_flash": 4,
                   "smoke_blast": 4,
                   "dirt_blast": 4,
                   "sparks": 8,
                   "explosion_1": 8,
                   "bang_1": 8,
                   "bang_2": 8,
                   "bang_3": 8,
                   "simple_dirt": 8,
                   "round_smoke": 8,
                   "bubble_smoke": 8,
                   "small_craters": 16,
                   "big_craters": 9,
                   "rubble": 6}


class Particle(object):
    def __init__(self, environment):
        self.environment = environment
        self.ended = False
        self.box = self.add_box()
        self.timer = 0.0
        self.environment.particles.append(self)

    def add_box(self):
        pass

    def terminate(self):
        if self.box:
            self.box.endObject()

    def update(self):
        self.process()

    def process(self):
        pass


class AnimatedParticle(Particle):

    mesh_name = None

    def __init__(self, environment):

        self.mesh_name = self.get_mesh_name()
        super().__init__(environment)

        self.max_frame = particle_ranges[self.mesh_name]
        self.max_sub_frame = 4

        self.sub_frame = 0
        self.frame = random.randint(1, self.max_frame)

        self.switch_frame()

    def get_mesh_name(self):
        return "chunk_1"

    def add_box(self):
        return self.environment.own.scene.addObject(self.mesh_name, self.environment.own, 0)

    def animation_update(self):
        if self.sub_frame < self.max_sub_frame:
            self.sub_frame += 1
        else:
            self.frame += 1
            self.sub_frame = 0
            self.switch_frame()

            if self.frame >= self.max_frame:
                self.frame = 1

    def switch_frame(self):

        if 0 < self.frame < self.max_frame:
            frame_name = "{}.{}".format(self.mesh_name, str(self.frame).zfill(3))
            self.box.replaceMesh(frame_name)

    def update(self):
        self.animation_update()
        self.process()


class DebugText(Particle):
    def __init__(self, environment, text, position):
        self.position = position
        super().__init__(environment)

        self.text_object = bgeutils.get_ob("text_object", self.box.children)
        self.text_object["Text"] = text
        spread = 0.002

        self.up_vector = mathutils.Vector([random.uniform(-spread, spread), random.uniform(-spread, spread),
                                           random.uniform(0.015, 0.02)])

    def add_box(self):
        box = self.environment.add_object("debug_text")
        box.worldPosition = self.position
        box.worldPosition.z += 1.0
        return box

    def process(self):

        if self.timer > 120:
            self.ended = True
        else:
            self.timer += 1

            if self.timer < 60:
                self.box.worldPosition += self.up_vector
            if self.timer > 60:
                self.text_object.color *= 0.95


class EnemyTarget(Particle):
    def __init__(self, envirnoment, position):
        self.position = [position[0], position[1], 0.0]

        super().__init__(envirnoment)

        self.start_scale = mathutils.Vector([0.0, 0.0, 0.0])
        self.end_scale = mathutils.Vector([1.0, 1.0, 1.0])

    def add_box(self):
        box = self.environment.add_object("enemy_target")
        box.worldPosition = self.position
        box.worldPosition.z += 0.1
        box.localScale = [0.01, 0.01, 0.01]
        box.color = [1.0, 0.0, 0.0, 1.0]
        return box

    def process(self):

        self.timer += 1

        if self.timer > 60:
            self.ended = True
        else:
            if self.timer > 40:
                self.box.localScale *= 0.9
            else:
                self.box.localScale *= 1.12


class DummyExplosion(Particle):
    def __init__(self, environment, starting_position, size):
        self.starting_position = starting_position

        super().__init__(environment)

        if size == 1:
            self.scale = 0.6
        else:
            self.scale = 0.7

        self.box.localScale *= 0.01

    def add_box(self):
        box = self.environment.add_object("explosion")
        box.worldPosition = mathutils.Vector(self.starting_position).to_3d()
        box.worldPosition.z += 0.01
        return box

    def process(self):

        if self.timer > 60:
            self.ended = True
        else:
            self.timer += 1

            self.box.worldPosition.z += 0.001
            if self.timer > 50:
                self.box.color[3] *= 0.75

            self.scale *= 0.9
            self.box.localScale *= (1.0 + self.scale)


class DummyDebris(Particle):
    def __init__(self, environment, starting_position, size):
        self.starting_position = starting_position

        super().__init__(environment)

        if size == 1:
            self.scale = 0.6
        else:
            self.scale = 0.7

        self.box.localScale *= 0.01

    def add_box(self):
        box = self.environment.add_object("debris")
        box.worldPosition = mathutils.Vector(self.starting_position).to_3d()
        return box

    def process(self):

        if self.timer < 60:
            self.timer += 1

            if self.timer > 50:
                self.box.color *= 0.75

            self.scale *= 0.9
            self.box.localScale *= (1.0 + self.scale)


class DummyGunFlash(Particle):
    def __init__(self, environment, object_adder, size):
        self.object_adder = object_adder
        super().__init__(environment)

        if size == 1:
            self.scale = 2.6
        else:
            self.scale = 4.7

        self.box.localScale *= 0.01

    def add_box(self):
        box = self.environment.add_object("gun_flash")
        box.worldTransform = self.object_adder.worldTransform.copy()
        box.localScale *= 0.2
        return box

    def process(self):

        if self.timer > 12:
            self.ended = True
        else:
            self.timer += 1

            if self.timer > 8:
                self.box.color[3] *= 0.75

            self.scale *= 0.8
            self.box.localScale *= (1.0 + self.scale)


class DeadInfantry(Particle):
    def __init__(self, environment, load_name, position):
        self.load_name = load_name
        self.position = position
        super().__init__(environment)
        self.dummy = self.add_dummy()

    def add_dummy(self):
        dummy = self.environment.add_object("dead_infantry_dummy")
        dummy.worldPosition = self.position
        return dummy

    def update(self):
        # TODO animate death sequence, add correct mesh add dead mesh to decal list
        if self.timer > 30:
            self.ended = True
        else:
            self.timer += 1

    def terminate(self):
        self.dummy.endObject()


class DummyAircraft(Particle):
    def __init__(self, environment, target, team):
        super().__init__(environment)
        self.team = team
        self.start = self.get_origin()

        self.target = target
        self.flight_path = self.get_flight_path()
        self.path_index = 0
        self.progress = 0.0
        self.box.worldPosition = mathutils.Vector(self.flight_path[0])

    def get_origin(self):
        if self.team == 2:
            return self.environment.enemy_air_strike_origin
        else:
            return self.environment.player_air_strike_origin

    def get_flight_path(self):
        start_point = mathutils.Vector(self.start).to_3d()
        target = mathutils.Vector(self.target).to_3d()

        start_point.z = 18.0
        target.z = 0.5

        flight_vector = target - start_point

        over_flight = flight_vector.copy()
        over_flight.length *= 2.0
        end_point = target + over_flight
        end_point.z = 22.0

        knot1 = start_point
        handle1 = target
        handle2 = target
        knot2 = end_point
        resolution = 32

        flight_path = mathutils.geometry.interpolate_bezier(knot1, handle1, handle2, knot2, resolution)
        return flight_path

    def add_box(self):
        box = self.environment.add_object("dummy_aircraft")
        return box

    def process(self):

        if self.progress > 1.0:
            self.path_index += 1
            self.progress -= 1.0

        speed = 0.12
        self.progress += speed

        target_point = mathutils.Vector(self.flight_path[self.path_index + 1])
        current_point = mathutils.Vector(self.flight_path[self.path_index])

        target_vector = target_point - current_point
        tracking = bgeutils.track_vector(target_vector)

        self.box.worldOrientation = tracking
        self.box.worldPosition = current_point.lerp(target_point, self.progress)

        if self.path_index == len(self.flight_path) - 2:
            self.ended = True
