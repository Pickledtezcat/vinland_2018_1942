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
    def __init__(self, environment, text, add_object):
        self.add_object = add_object
        super().__init__(environment)

        self.text_object = bgeutils.get_ob("text_object", self.box.children)
        self.text_object["Text"] = text

    def add_box(self):
        box = self.environment.add_object("debug_text")
        box.worldPosition = self.add_object.worldPosition.copy()
        box.worldPosition.z += 1.0
        return box

    def process(self):

        if self.timer > 120:
            self.ended = True
        else:
            self.timer += 1

            self.box.worldPosition.z += 0.015
            if self.timer > 60:
                self.text_object.color *= 0.95


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








