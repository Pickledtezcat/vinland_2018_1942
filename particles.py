import bge
import mathutils
import random
import bgeutils
import math
import effects

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
                   "chunk_smoke": 8,
                   "rubble": 6,
                   "building_craters": 9,
                   "large_building_craters": 9,
                   "soft_rubble": 17,
                   "hard_rubble": 17}


class Decal(object):
    def __init__(self, environment, decal_name, position, scale, colored):
        self.environment = environment
        self.decal_name = decal_name
        self.colored = colored
        self.position = position
        self.scale = scale
        self.decal_object = None
        self.add_decal()

        self.environment.decals.append(self)

    def add_decal(self):
        self.decal_object = self.environment.add_object(self.decal_name)
        self.decal_object.worldPosition = self.position
        self.decal_object.localScale = self.scale
        if self.colored:
            self.decal_object.color = self.environment.dirt_color

    def save_decal(self):
        self.terminate()

        name = self.decal_name
        position = [round(axis, 3) for axis in list(self.position)]
        scale = [round(axis, 3) for axis in list(self.scale)]

        return name, position, scale, self.colored

    def terminate(self):
        self.decal_object.endObject()


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
        return self.environment.add_object(self.mesh_name)

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
    def __init__(self, environment, text, position, color=[1.0, 1.0, 1.0, 1.0], delay=0):
        self.position = position
        self.delay = delay
        super().__init__(environment)

        self.text_object = bgeutils.get_ob("text_object", self.box.children)
        self.text_object.color = color
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

        if self.delay > 0:
            self.delay -= 1
        else:
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


class DestroyedVehicle(Particle):
    def __init__(self, environment, position, size):
        super().__init__(environment)
        self.delay = random.randint(12, 120)
        self.position = position
        self.size = size

    def place_elements(self):
        for i in range(random.randint(8, 12)):
            chunk_size = 0.6 + (self.size * 0.05) + random.uniform(-0.3, 0.3)
            ArmorChunk(self.environment, chunk_size, self.position, delay=i * random.randint(1, 12))

        for i in range(random.randint(8, 12)):
            chunk_size = 2.0 + (self.size * 0.2) + random.uniform(-0.3, 0.3)
            MetalChunk(self.environment, chunk_size, self.position, delay=i * random.randint(1, 24))

        for i in range(random.randint(3, 8)):
            explosion_size = 1.5 + (self.size * 0.5) + random.uniform(-0.3, 0.3)
            ShellImpact(self.environment, self.position, explosion_size, delay=i * random.randint(1, 36))

        rubble_size = 0.5 + (self.size * 0.1)
        VehicleRubble(self.environment, self.position, rubble_size)
        self.ended = True

    def process(self):
        if self.delay < 0:
            self.place_elements()
        else:
            self.delay -= 1


class DummyAircraft(Particle):
    def __init__(self, environment, target, team):
        self.team = team

        super().__init__(environment)
        self.start = self.get_origin()
        self.target = target
        self.flight_path = self.get_flight_path()
        self.path_index = 0
        self.progress = 0.0

        self.box.worldPosition = mathutils.Vector(self.flight_path[0])
        self.add_sound()

    def add_sound(self):
        if self.team == 2:
            end_sound = "HRE"
        else:
            end_sound = "VIN"

        sound_name = "MOVE_PLANE_{}".format(end_sound)
        plane_pitch = random.uniform(1.0, 1.5)
        flight_len = len(self.flight_path)
        mid_point = self.flight_path[int(flight_len * 0.5)].copy()
        mid_point.z = 0.5

        SoundDummy(self.environment, mid_point, sound_name, volume=2.0, pitch=plane_pitch)

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
        if self.team == 2:
            box = self.environment.add_object("HRR_fighter")
        else:
            box = self.environment.add_object("VIN_fighter")

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


class DeadInfantry(Particle):
    def __init__(self, environment, mesh_name, position):
        self.mesh_name = mesh_name
        self.current_mesh = None
        self.position = position
        self.frame = 0
        self.frame_timer = 0
        super().__init__(environment)

    def add_box(self):
        mesh_name = "{}_{}".format(self.mesh_name, self.frame)
        box = self.environment.add_object(mesh_name)
        box.worldPosition = self.position
        return box

    def process(self):
        # TODO animate death sequence, add correct mesh add dead mesh to decal list

        if self.frame_timer > 1.0:
            if self.frame < 3:
                self.frame += 1
                self.frame_timer = 0.0
            else:
                self.add_decal()
                self.ended = True
        else:
            self.frame_timer += 0.1

        mesh_name = "{}_{}".format(self.mesh_name, self.frame)
        self.box.replaceMesh(mesh_name)

    def add_decal(self):
        Decal(self.environment, "{}_{}".format(self.mesh_name, 4), self.box.worldPosition.copy(),
              self.box.localScale.copy(), False)


class BaseExplosion(Particle):
    """the base explosion template"""

    def __init__(self, environment, position, rating, delay=12, is_hit=False):
        self.is_hit = is_hit
        self.position = position
        super().__init__(environment)
        self.delay = delay
        self.sound = "EXPLODE_1"
        self.volume = 1.0
        self.rating = rating
        self.variance = 0.5
        self.z_height = 0.02
        self.get_details()
        self.impact_position = self.get_variance()

    def add_box(self):
        return self.environment.add_object("dummy_object")

    def get_details(self):
        self.sound = "EXPLODE_1"
        self.variance = 0.5
        if self.is_hit:
            self.variance = None
        self.z_height = 0.02

    def get_variance(self):
        if not self.variance:
            target_position = self.position.copy()
        else:
            v = self.variance
            random_vector = mathutils.Vector([random.uniform(-v, v), random.uniform(-v, v), 0.02])
            target_position = mathutils.Vector(self.position).to_3d()
            target_position += random_vector

        target_position.z = self.z_height

        return target_position

    def trigger_explosion(self):
        self.explode()
        hit_pitch = random.uniform(0.8, 1.5)

        if self.sound:
            SoundDummy(self.environment, self.impact_position, self.sound, volume=self.volume, pitch=hit_pitch)

    def explode(self):
        pass

    def process(self):
        if self.timer > self.delay:
            self.trigger_explosion()
            self.ended = True
        else:
            self.timer += 1


class GrenadeExplosion(BaseExplosion):

    def get_details(self):
        self.delay = 0
        self.sound = "EXPLODE_1"
        self.variance = 0.5
        if self.is_hit:
            self.variance = None

    def explode(self):
        size = self.rating * 0.05
        size += random.uniform(-0.1, 0.1)

        ScorchMark(self.environment, self.impact_position, size)
        for i in range(3):
            SmallSmoke(self.environment, size * 5.0, self.impact_position, delay=12)
        for i in range(12):
            ExplosionSparks(self.environment, size * 0.7, self.impact_position)
            DirtBlast(self.environment, size * 2.0, self.impact_position)


class WaterHit(Particle):
    def __init__(self, environment, position, rating):
        self.position = position
        super().__init__(environment)
        self.rating = rating
        self.variance = 0.2
        self.dropped = False

    def get_variance(self, variance):
        if self.variance:
            v = variance
            random_vector = mathutils.Vector([random.uniform(-v, v), random.uniform(-v, v), 0.02])
            target_position = mathutils.Vector(self.position).to_3d()
            target_position += random_vector

            return target_position
        else:
            return self.position.copy()

    def trigger_blasts(self):

        sub_blasts = 1
        if self.rating > 3:
            sub_blasts = 3
        if self.rating > 6:
            sub_blasts = 5
        if self.rating > 9:
            sub_blasts = 7
        if self.rating > 12:
            sub_blasts = 9

        for b in range(sub_blasts):
            sub_rating = random.uniform(self.rating * 0.25, self.rating * 1.0)
            sub_delay = random.randint(0, 24)
            WaterImpact(self.environment, self.get_variance(0.5), int(sub_rating), delay=sub_delay)

    def initial_splash(self):
        WaterImpact(self.environment, self.get_variance(0.2), int(self.rating * 0.2))

    def process(self):
        self.timer += 1

        if not self.dropped:
            self.initial_splash()
            self.dropped = True

        if self.timer > 30:
            self.trigger_blasts()
            self.ended = True


class WaterImpact(BaseExplosion):
    def get_details(self):
        self.sound = "EXPLODE_1"
        self.variance = None
        self.z_height = -0.1

    def trigger_explosion(self):
        self.explode()
        if self.sound:
            SoundDummy(self.environment, self.impact_position, self.sound, volume=0.2)

    def explode(self):
        self.sound = None
        amount = 3

        if self.rating > 2:
            amount = 6
            self.sound = "EXPLODE_1"

        if self.rating > 5:
            amount = 9
            self.sound = "EXPLODE_2"

        elif self.rating > 10:
            amount = 12
            self.sound = "EXPLODE_3"

        elif self.rating > 15:
            amount = 9
            self.sound = "EXPLODE_4"

        size = 0.3 + (self.rating * 0.015)
        size += random.uniform(-0.03, 0.03)

        for i in range(amount):
            WaterSpout(self.environment, size * 4.0, self.impact_position, i)

        WaterRipple(self.environment, size * 4.0, self.impact_position)

        hit_pitch = random.uniform(0.8, 1.5)

        if self.rating < 10:
            SoundDummy(self.environment, self.impact_position, "SMALL_SPLASH", volume=1.5, pitch=hit_pitch,
                       delay=12)
        else:
            SoundDummy(self.environment, self.impact_position, "BIG_SPLASH", volume=1.5, pitch=hit_pitch,
                       delay=12)


class ShellImpact(BaseExplosion):

    def get_details(self):
        self.sound = "EXPLODE_1"
        self.variance = 0.25
        self.z_height = 0.25

    def explode(self):
        size = 0.015 + (self.rating * 0.1)
        size += random.uniform(-0.03, 0.03)

        self.sound = None
        amount = 3

        if self.rating > 2:
            amount = 6
            self.sound = "EXPLODE_1"

        if self.rating > 5:
            amount = 9
            self.sound = "EXPLODE_2"

        elif self.rating > 10:
            amount = 12
            self.sound = "EXPLODE_3"

        elif self.rating > 15:
            amount = 9
            self.sound = "EXPLODE_4"

        hit_pitch = random.uniform(0.8, 1.5)

        if self.rating < 10:
            SoundDummy(self.environment, self.impact_position, "RICOCHET", volume=0.25, pitch=hit_pitch, delay=12)
        else:
            SoundDummy(self.environment, self.impact_position, "CRITICAL_HIT", volume=0.25, pitch=hit_pitch, delay=12)

        for i in range(amount):
            ArmorSparks(self.environment, size * 0.6, self.impact_position, i)
            SmallBlast(self.environment, size * 1.5, self.impact_position, i)
            ArmorChunk(self.environment, size * 0.5, self.impact_position, i)
            ArmorBlast(self.environment, size * 0.5, self.impact_position)
            SmallSmoke(self.environment, size * 1.0, self.impact_position, i)


class BrickImpact(BaseExplosion):

    def get_details(self):
        self.sound = "BRICK_{}".format(random.randint(1, 8))
        self.variance = 0.25
        self.z_height = 0.25

    def explode(self):
        size = 0.015 + (self.rating * 0.1)
        size += random.uniform(-0.03, 0.03)

        amount = 3

        if self.rating > 2:
            amount = 6
            self.volume = 1.2

        if self.rating > 5:
            amount = 9
            self.volume = 2.0

        elif self.rating > 10:
            amount = 12
            self.volume = 3.0

        elif self.rating > 15:
            amount = 9
            self.volume = 3.0

        for i in range(amount):
            SmallBlast(self.environment, size * 1.5, self.impact_position, i * 2)
            ArmorChunk(self.environment, size * 0.5, self.impact_position, i * 3)
            ArmorBlast(self.environment, size * 0.5, self.impact_position)
            SmallSmoke(self.environment, size * 1.0, self.impact_position, i * 2)


class ShellDeflection(BaseExplosion):

    def get_details(self):
        self.sound = "EXPLODE_1"
        self.variance = 0.25
        self.z_height = 0.25

    def trigger_explosion(self):
        self.explode()
        if self.sound:
            SoundDummy(self.environment, self.impact_position, self.sound, volume=0.5)

    def explode(self):
        size = 0.015 + (self.rating * 0.05)
        size += random.uniform(-0.03, 0.03)

        self.sound = None
        amount = 3

        if self.rating > 2:
            amount = 6
            self.sound = "EXPLODE_1"

        if self.rating > 5:
            amount = 9
            self.sound = "EXPLODE_2"

        elif self.rating > 10:
            amount = 12
            self.sound = "EXPLODE_3"

        elif self.rating > 15:
            amount = 9
            self.sound = "EXPLODE_4"

        hit_pitch = random.uniform(0.8, 1.5)

        if self.rating < 10:
            SoundDummy(self.environment, self.impact_position, "RICOCHET", volume=0.5, pitch=hit_pitch, delay=12)
        else:
            SoundDummy(self.environment, self.impact_position, "CRITICAL_HIT", volume=0.5, pitch=hit_pitch, delay=12)

        SmallSmoke(self.environment, size * 3.0, self.impact_position, 12)

        for i in range(amount):
            SmallBlast(self.environment, size * 1.5, self.impact_position, 12)

        for i in range(amount * 4):
            ArmorSparks(self.environment, size * 0.3, self.impact_position, i)


class ShellExplosion(BaseExplosion):

    def get_details(self):
        self.sound = "EXPLODE_1"
        self.variance = 0.5

    def explode(self):
        size = 0.008 + (self.rating * 0.05)
        size += random.uniform(-0.03, 0.03)

        self.sound = "EXPLODE_0"
        amount = 9

        if self.rating > 19:
            if self.rating > 9:
                self.sound = "EXPLODE_4"
                amount = 8
                BigScorchMark(self.environment, self.impact_position, size * 0.6)

            for i in range(amount):
                LargeSmoke(self.environment, size * 2.5, self.impact_position, i)
                RockChunk(self.environment, size * 1.0, self.impact_position, i)
                LargeBlast(self.environment, size * 3.0, self.impact_position, i)
                ExplosionSparks(self.environment, size * 0.6, self.impact_position, i)
                DirtClods(self.environment, size * 2.0, self.impact_position, i)

        else:
            self.sound = None
            amount = 3

            if self.rating > 2:
                amount = 6
                self.sound = "EXPLODE_1"

            if self.rating > 3:
                self.sound = "EXPLODE_1"
                amount = 12
                LargeSmoke(self.environment, size * 3.0, self.impact_position)
                LargeSmoke(self.environment, size * 8.0, self.impact_position, delay=12)

            if self.rating > 6:
                self.sound = "EXPLODE_2"
                amount = 18
                LargeSmoke(self.environment, size * 4.0, self.impact_position, delay=18)

            if self.rating > 9:
                self.sound = "EXPLODE_3"
                amount = 20
                LargeSmoke(self.environment, size * 6.0, self.impact_position, delay=18)

            if self.rating > 4:
                BigScorchMark(self.environment, self.impact_position, size * 1.0)
            elif self.rating > 2:
                ScorchMark(self.environment, self.impact_position, size * 1.3)
                SmallSmoke(self.environment, 0.5, self.impact_position)
            else:
                SmallSmoke(self.environment, 0.5, self.impact_position)

            for i in range(amount):
                if self.rating > 4:
                    RockChunk(self.environment, size * 1.0, self.impact_position, i)
                    LargeBlast(self.environment, size * 3.0, self.impact_position, i)
                else:
                    SmallBlast(self.environment, size * 1.5, self.impact_position, i)

                ExplosionSparks(self.environment, size * 0.6, self.impact_position, i)
                DirtBlast(self.environment, size * 2.0, self.impact_position, i)


class MuzzleBlast(Particle):
    def __init__(self, environment, adder, rating):
        super().__init__(environment)
        self.adder = adder
        self.rating = rating
        self.add_flash()
        self.ended = True

    def add_box(self):
        return self.environment.add_object("dummy_object")

    def add_flash(self):

        sound = "I_RIFLE"
        speed = 0.1

        if self.rating > 1:
            sound = "I_HEAVY_RIFLE"
            speed = 0.08

        if self.rating > 2:
            sound = "I_ANTI_TANK"
            speed = 0.08

        if self.rating > 3:
            sound = "SHELL_1"
            speed = 0.06

        if self.rating > 5:
            sound = "SHELL_2"
            speed = 0.05

        if self.rating > 7:
            sound = "SHELL_3"
            speed = 0.05

        if self.rating > 10:
            sound = "SHELL_4"
            speed = 0.04

        if self.rating > 15:
            sound = "SHELL_5"
            speed = 0.04

        hit_pitch = random.uniform(0.9, 1.1)
        adding_position = self.adder.worldPosition.copy()

        SoundDummy(self.environment, adding_position, sound, pitch=hit_pitch)

        size = 0.015 + (self.rating * 0.15)
        size += random.uniform(-0.05, 0.05)

        GunFlash(self.environment, self.adder, size, speed, False)
        delay = int(1.0 / speed)

        GunFlash(self.environment, self.adder, size * 1.3, speed, True)
        SmallSmoke(self.environment, size, adding_position, delay * 2)

        for i in range(4):
            ExplosionSparks(self.environment, size * 0.2, adding_position, delay=i)


class RocketFlash(Particle):
    def __init__(self, environment, adder, rating):
        super().__init__(environment)
        self.adder = adder
        self.rating = rating
        self.add_flash()
        self.ended = True

    def add_box(self):
        return self.environment.add_object("dummy_object")

    def add_flash(self):

        sound = "ROCKET"
        speed = 0.04
        hit_pitch = 1.2

        if self.rating > 4:
            speed = 0.03
            hit_pitch = 1.0

        if self.rating > 6:
            speed = 0.025
            hit_pitch = 0.8

        if self.rating > 9:
            speed = 0.02
            hit_pitch = 0.6

        hit_pitch += random.uniform(- 0.1, 0.1)
        adding_position = self.adder.worldPosition.copy()

        SoundDummy(self.environment, adding_position, sound, pitch=hit_pitch)

        size = 0.015 + (self.rating * 0.15)
        size += random.uniform(-0.05, 0.05)

        GunFlash(self.environment, self.adder, size, speed, False)
        delay = int(1.0 / speed)

        GunFlash(self.environment, self.adder, size * 1.3, speed, True)
        SmallSmoke(self.environment, size, adding_position, delay * 2)

        for i in range(6):
            SmallSmoke(self.environment, size * 1.5, adding_position, delay=i * 8)


class DirtTrail(Particle):
    def __init__(self, environment, position, size, ground_type):
        self.delay = random.randint(4, 24)
        self.ground_type = ground_type
        self.position = position
        super().__init__(environment)
        self.size = size

    def add_box(self):
        box = self.environment.add_object("dummy_object")
        box.worldPosition = self.position.copy()
        return box

    def get_variance(self, variance):
        v = variance
        random_vector = mathutils.Vector([random.uniform(-v, v), random.uniform(-v, v), 0.02])
        target_position = mathutils.Vector(self.position)
        target_position += random_vector

        return target_position

    def process(self):
        if self.delay > 0:
            self.delay -= 1
            self.box.localScale = [0.0, 0.0, 0.0]
        else:
            if self.ground_type == "SOFT":
                chunks = random.randint(3, 6)
            else:
                chunks = random.randint(1, 3)

            for i in range(chunks):
                position = self.get_variance(0.25)
                size = 0.015 + (self.size * 0.15)
                size += random.uniform(-0.05, 0.05)

                if self.ground_type == "SOFT":
                    DirtClods(self.environment, self.size, position, delay=i * 4)
                else:
                    SmokeClods(self.environment, self.size, position, delay=i * 4)

            self.ended = True


class GunFlash(Particle):
    def __init__(self, environment, adder, size, speed, after_flash, delay=0):
        self.after_flash = after_flash
        self.delay = delay
        super().__init__(environment)
        self.speed = speed
        self.adder = adder
        self.size = size
        self.align_box()

    def align_box(self):
        self.box.worldTransform = self.adder.worldTransform

    def add_box(self):
        if self.after_flash:
            base_mesh = "after_flash"
        else:
            base_mesh = "gun_flash"

        mesh = "{}.{}".format(base_mesh, str(random.randint(1, 4)).zfill(3))
        return self.environment.add_object(mesh)

    def process(self):
        if self.delay > 0:
            self.delay -= 1
            self.box.localScale = [0.0, 0.0, 0.0]
        else:
            if self.timer < 1.0:
                self.timer += self.speed

                c = 1.0 - self.timer
                if self.after_flash:
                    c *= 0.25

                color = [c, c * c, c * c * c, 1.0]
                self.box.color = color

                s = self.timer
                half_scale = (s * s) * self.size
                scale = s * self.size

                scale = [half_scale, scale, half_scale]
                self.box.localScale = scale
            else:
                self.box.localScale = [0.0, 0.0, 0.0]
                self.ended = True


class InfantryBullet(Particle):
    """a particle used for infantry bullets"""

    def __init__(self, environment, position, target, action):
        self.position = position
        self.target = target
        super().__init__(environment)
        self.action = action
        self.sound = "I_PISTOL"
        self.bullet_size = 1
        self.bullet_color = None
        self.triggered = False
        self.delay = random.randint(2, 8)
        self.box.worldPosition = self.position.copy()

    def add_box(self):
        return self.environment.add_object("dummy_object")

    def trigger_action(self):
        if not self.triggered:
            weapon_dict = {"RIFLE_GRENADE": ["I_GRENADE", None, None],
                           "RIFLES": ["I_RIFLE", 0.4, None],
                           "SNIPER_RIFLES": ["I_ANTI_TANK", 0.6, [0.1, 0.1, 0.0, 1.0]],
                           "ASSAULT_RIFLES": ["I_RIFLE", 0.4, None],
                           "HEAVY_RIFLES": ["I_ANTI_TANK", 0.6, [1.0, 0.2, 0.0, 1.0]],
                           "SMG": ["I_SMG", 0.3, None],
                           "SIDE_ARMS": ["I_PISTOL", 0.3, None],
                           "SUPPORT_FIRE": ["I_LIGHT_MG", 0.6, [1.0, 0.2, 0.0, 1.0]],
                           "HEAVY_SUPPORT_FIRE": ["I_MG", 0.6, [1.0, 1.0, 0.6, 1.0]],
                           "DAMAGE_TRACKS": ["I_HEAVY_RIFLE", 0.6, [1.0, 1.0, 0.6, 1.0]]}

            if self.action in weapon_dict:
                self.sound, self.bullet_size, self.bullet_color = weapon_dict[self.action]

            SoundDummy(self.environment, self.position, self.sound)

            variance = 0.5
            random_vector = mathutils.Vector(
                [random.uniform(-variance, variance), random.uniform(-variance, variance), 0.02])
            target_position = mathutils.Vector(self.target).to_3d()
            target_position += random_vector
            origin = self.position.copy()
            origin.z += 0.25

            if self.bullet_size:
                SmallSmoke(self.environment, self.bullet_size, target_position)
            else:
                size = random.uniform(0.08, 0.3)

                ScorchMark(self.environment, target_position, size)
                LargeSmoke(self.environment, size * 10.0, target_position, delay=12)
                for i in range(12):
                    ExplosionSparks(self.environment, size * 0.7, target_position)
                    ArmorBlast(self.environment, size * 2.0, target_position)

            if self.bullet_color:
                InfantryBulletStreak(self.environment, origin, target_position, self.bullet_color)

            self.triggered = True

    def process(self):
        if self.timer > 120:
            self.ended = True
        else:
            self.timer += 1

        if self.timer > self.delay:
            self.trigger_action()


class ScorchMark(Particle):
    """a particle used to show permanent craters and damage such as destroyed vehicles"""

    def __init__(self, environment, position, scale):
        self.mesh = None
        self.scale = scale

        super().__init__(environment)

        self.color = mathutils.Vector(self.environment.dirt_color)
        self.box.worldPosition = position
        self.box.worldPosition.z = random.uniform(0.01, 0.04)
        self.box.color = self.color

    def process(self):
        if self.timer < 1.0:
            self.timer += 0.05
            s = self.scale * self.timer
            self.box.localScale = [s, s, s]
        else:
            self.add_decal()
            self.ended = True

    def add_box(self):
        self.mesh = "{}.{}".format("small_craters", str(random.randint(1, 16)).zfill(3))
        return self.environment.add_object(self.mesh)

    def add_decal(self):
        Decal(self.environment, self.mesh, self.box.worldPosition.copy(), self.box.localScale.copy(), True)


class BigScorchMark(ScorchMark):
    """a particle used to show permanent craters and damage such as destroyed vehicles
    big craters are used for bigger explosions"""

    def add_box(self):
        self.mesh = "{}.{}".format("big_craters", str(random.randint(1, 9)).zfill(3))
        return self.environment.add_object(self.mesh)


class VehicleRubble(ScorchMark):
    """a particle used to show permanent craters and damage such as destroyed vehicles
    rubble is used for destroyed vehicles and artillery"""

    def add_box(self):
        self.mesh = "{}.{}".format("rubble", str(random.randint(1, 12)).zfill(3))
        return self.environment.add_object(self.mesh)


class BuildingRubble(ScorchMark):
    """a particle used to show permanent craters and damage such as destroyed vehicles
    rubble is used for destroyed vehicles and artillery"""

    def add_box(self):
        self.mesh = "{}.{}".format("large_building_craters", str(random.randint(1, 9)).zfill(3))
        return self.environment.add_object(self.mesh)


class SmallRubble(ScorchMark):
    """a particle used to show permanent craters and damage such as destroyed vehicles
    rubble is used for destroyed vehicles and artillery"""

    def add_box(self):
        self.mesh = "{}.{}".format("building_craters", str(random.randint(1, 9)).zfill(3))
        return self.environment.add_object(self.mesh)


class SoundDummy(Particle):
    """a particle used for adding sound effects"""

    def __init__(self, environment, position, sound_name, timer=120, volume=1.0, attenuation=1.0, pitch=1.0, delay=0):
        self.delay = delay
        super().__init__(environment)
        self.position = position
        self.box.worldPosition = position.copy()
        self.timer = timer
        self.sound_dict = {"sound": sound_name,
                           "owner": self.box,
                           "volume": volume,
                           "attenuation": attenuation,
                           "pitch": pitch}
        self.triggered = False

    def trigger_sound(self):
        if not self.triggered:
            self.environment.sound_effect(self.sound_dict)
            self.triggered = True

    def process(self):
        if self.delay > 0:
            self.delay -= 1
        else:
            self.trigger_sound()

            if self.timer > 120:
                self.ended = True
            else:
                self.timer += 1

    def add_box(self):
        return self.environment.add_object("dummy_object")


class InfantryBulletStreak(Particle):
    """ a small bullet tracer, can be used for vehicle weapons"""

    def __init__(self, environment, position, target, bullet_color):
        super().__init__(environment)

        self.position = position
        self.target = target
        self.bullet_color = bullet_color
        self.place_particle()

    def add_box(self):
        return self.environment.add_object("bullet_streak")

    def place_particle(self):

        position = self.position
        self.box.worldPosition = position

        target = self.target
        target_vector = target - position
        self.box.worldOrientation = target_vector.to_track_quat("Y", "Z").to_matrix().to_3x3()
        self.box.localScale.y = target_vector.length

    def process(self):

        self.timer += 0.4
        color = 1.0 - self.timer

        if self.bullet_color:
            r, g, b, a = self.bullet_color
            self.box.color = [r * color, g * color, b * color, a]

        if self.timer >= 1.0:
            self.ended = True


class SmallSmoke(AnimatedParticle):
    """a small smoke particle used for small arms hits on the ground
    or small arms muzzle smoke"""

    def __init__(self, environment, growth, position, delay=0):
        super().__init__(environment)
        self.max_sub_frame = 24
        self.grow = 1.002 * growth
        self.up_force = mathutils.Vector([0.0, 0.0, 0.01])
        self.position = position
        self.box.worldPosition = position.copy()
        self.delay = delay

    def get_mesh_name(self):
        return "bubble_smoke"

    def process(self):

        if self.delay > 0:
            self.box.color = [0.0, 0.0, 0.0, 0.0]
            self.delay -= 1

        else:
            if self.timer >= 1.0:
                self.ended = True

            else:
                self.timer += 0.01
                c = (1.0 - (self.timer * 0.5)) + 0.75
                a = (1.0 - self.timer) * 0.5
                self.box.color = [c, c, c, a]
                up_force = self.up_force * (0.9999 * self.timer)
                self.box.worldPosition += up_force
                scale = self.grow * self.timer

                self.box.localScale = [scale, scale, scale]


class SmallBlast(AnimatedParticle):
    """ small explosion, good for grenades and the like"""

    def __init__(self, environment, growth, position, delay=0):
        # growth 1.0 = approx grenade size
        # always growth, position, delay
        self.delay = delay
        super().__init__(environment)
        self.max_sub_frame = 4
        self.grow = 1.002 * growth
        s = 0.006
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), s])
        self.position = position
        self.box.worldPosition = position.copy()

    def get_mesh_name(self):
        return "bang_2"

    def process(self):
        if self.delay > 0:
            self.box.color = [0.0, 0.0, 0.0, 0.0]
            self.delay -= 1

        else:
            if self.timer >= 1.0:
                self.ended = True

            else:
                self.timer += 0.02
                c = 1.0 - self.timer
                a = 1.0

                c = c * c

                self.box.color = [c, c * c, c * c * c, a]

                up_force = self.up_force * (0.9999 * self.timer)
                self.box.worldPosition += up_force
                scale = self.grow * self.timer

                self.box.localScale = [scale, scale, scale]


class LargeSmoke(AnimatedParticle):
    """ large floating smoke for after an explosion"""

    def __init__(self, environment, growth, position, delay=0):
        super().__init__(environment)

        self.max_sub_frame = 4000

        self.grow = 1.003 * growth
        s = 0.0015 * growth

        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), s * 3.0])
        self.down_force = mathutils.Vector([0.0, 0.0, -0.02])

        self.box.worldPosition = position.copy()
        self.delay = delay

    def get_mesh_name(self):
        return "bubble_smoke"

    def process(self):

        if self.delay > 0:
            self.box.color = [0.0, 0.0, 0.0, 0.0]
            self.delay -= 1

        else:
            if self.timer >= 1.0:
                self.ended = True

            else:
                self.timer += 0.004
                c = 1.0 - self.timer
                a = 1.0 - self.timer
                a = a * a

                self.box.color = [c * c, c * c, c * c, a]

                up_force = self.up_force.lerp(self.down_force, self.timer)

                self.box.worldPosition += up_force
                scale = self.grow * self.timer

                self.box.localScale = [scale, scale, scale]


class DirectionalSmoke(AnimatedParticle):
    """ large floating smoke for after an explosion"""

    def __init__(self, environment, growth, position, direction, delay=0):
        self.direction = direction
        super().__init__(environment)

        self.max_sub_frame = 4000

        self.grow = 1.003 * growth
        s = 0.0015 * growth

        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), s * 3.0])
        self.up_force += direction

        self.down_force = mathutils.Vector([0.0, 0.0, -0.02])

        self.box.worldPosition = position.copy()
        self.delay = delay

    def get_mesh_name(self):
        return "bubble_smoke"

    def process(self):

        if self.delay > 0:
            self.box.color = [0.0, 0.0, 0.0, 0.0]
            self.delay -= 1

        else:
            if self.timer >= 1.0:
                self.ended = True

            else:
                self.timer += 0.012
                c = 1.0 - self.timer
                a = 1.0 - self.timer
                a = a * a

                self.box.color = [c * c, c * c, c * c, a]

                self.up_force.z *= 0.99

                self.box.worldPosition += self.up_force
                scale = self.grow * self.timer

                self.box.localScale = [scale, scale, scale]


class RockChunk(Particle):
    """a chunk of rock that flies out from the center"""

    def __init__(self, environment, growth, position, delay=0, direction=None):
        self.delay = delay
        self.color = None
        self.down_force = mathutils.Vector([0.0, 0.0, -0.01])
        self.grow = 1.002 * growth
        self.up_force = None
        self.direction = direction
        self.max_scale = random.uniform(0.1, 0.2)
        super().__init__(environment)

        self.rotation = [random.uniform(-0.03, 0.03) for _ in range(3)]

        self.box.worldPosition = position.copy()
        self.box.color = self.color
        self.box.applyRotation([random.uniform(-1.0, 1.0) for _ in range(3)])

    def add_box(self):
        s = 0.1 * self.grow
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), s * 0.5])
        self.color = mathutils.Vector(self.environment.dirt_color)

        mesh = "{}.{}".format("chunk_1", str(random.randint(1, 8)).zfill(3))
        return self.environment.add_object(mesh)

    def process(self):
        if self.delay > 0:
            self.box.color[3] = 0.0
            self.delay -= 1
        else:
            if self.timer >= 1.0:
                self.ended = True
            else:
                self.timer += 0.008
                self.box.color[3] = 1.0 - (self.timer * 0.5)
                self.box.applyRotation(self.rotation)

                up_force = self.up_force.lerp(self.down_force, self.timer)
                self.box.worldPosition += up_force

                scale = self.grow * min(self.max_scale, self.timer)
                self.box.localScale = [scale, scale, scale]


class ArmorChunk(RockChunk):
    """ a smaller chunk of armor particle"""

    def add_box(self):
        s = 0.05 * self.grow
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), s * 0.5])
        gray = random.uniform(0.2, 0.5)
        self.color = mathutils.Vector([gray, gray, gray, 0.0])

        mesh = "{}.{}".format("chunk_1", str(random.randint(1, 8)).zfill(3))
        return self.environment.add_object(mesh)


class MetalChunk(RockChunk):
    """ a large chunk of destroyed vehicle"""

    def add_box(self):
        s = 0.006 * self.grow
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), s * 0.8])
        gray = random.uniform(0.2, 0.5)
        self.color = mathutils.Vector([gray, gray, gray, 0.0])

        mesh = "{}.{}".format("metal_chunks", str(random.randint(1, 14)).zfill(3))
        return self.environment.add_object(mesh)


class FlyingRubble(Particle):
    """some rubble that flies out of a damaged house"""

    def __init__(self, environment, size, position, delay=0, direction=None):
        self.delay = delay
        self.direction = direction.copy()
        self.size = size
        self.start = position.copy()
        self.path = self.get_curve()
        self.grow = 0.0
        super().__init__(environment)
        self.progress = 1
        self.rotation = [random.uniform(-0.03, 0.03) for _ in range(3)]
        self.box.worldPosition = position.copy()
        self.box.applyRotation([random.uniform(-1.0, 1.0) for _ in range(3)])

    def get_curve(self):
        start_point = self.start.copy()
        end_point = self.start.copy() + (self.direction.copy() * random.uniform(30.0, 40.0))
        v = 0.5
        random_vector = mathutils.Vector([random.uniform(-v, v), random.uniform(-v, v), 0.0])
        end_point += random_vector
        end_point.z = 0.0

        mid_point = start_point.copy().lerp(end_point.copy(), 0.5)
        mid_point.z = random.uniform(0.5, 1.0)

        knot1 = start_point.copy()
        handle1 = mid_point.copy()
        handle2 = mid_point.copy()
        knot2 = end_point.copy()
        resolution = 16

        flight_path = mathutils.geometry.interpolate_bezier(knot1, handle1, handle2, knot2, resolution)
        return flight_path

    def add_box(self):
        mesh = "{}.{}".format("soft_rubble", str(random.randint(1, 16)).zfill(3))
        return self.environment.add_object(mesh)

    def process(self):
        if self.delay > 0:
            self.box.localScale = [0.0, 0.0, 0.0]
            self.delay -= 1
        else:
            if self.progress == 16:
                self.ground_impact()
            else:
                self.grow = min(1.0, self.grow + 0.1)
                self.box.applyRotation(self.rotation)

                current_point = self.path[self.progress - 1].copy()
                next_point = self.path[self.progress].copy()

                self.box.worldPosition = current_point.lerp(next_point, self.timer)

                scale = self.size * (self.grow * self.grow)
                self.box.localScale = [scale, scale, scale]

                self.timer += 0.15
                if self.timer >= 1.0:
                    self.timer = 0.0
                    self.progress += 1

    def ground_impact(self):
        self.ended = True
        hit_point = self.box.worldPosition.copy()
        hit_point[2] = random.uniform(0.02, 0.06)

        size = self.size * 2.0

        DirtClods(self.environment, size * 2.0, hit_point)

        hit_type = random.randint(0, 5)

        if self.size > 0.2:
            if hit_type > 2:
                SmallRubble(self.environment, hit_point, size)
            else:
                if self.size > 0.3:
                    BigScorchMark(self.environment, hit_point, size)
                else:
                    ScorchMark(self.environment, hit_point, size)

        elif self.size > 0.1:
            ScorchMark(self.environment, hit_point, size)


class DirtBlast(Particle):
    """ medium dirt particle, rises and falls back down again
    1.0 growth is good for small explosion or vehicle tracks
    3.0 makes big blast for big explosion"""

    def __init__(self, environment, growth, position, delay=0):
        self.delay = delay
        super().__init__(environment)

        self.grow = 1.002 * growth

        s = 0.012 * growth
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), s * 2.5])
        self.down_force = mathutils.Vector([0.0, 0.0, -0.05])

        self.box.worldPosition = position.copy()
        self.box.color = mathutils.Vector(self.environment.dirt_color) * 0.5

    def add_box(self):
        mesh = "{}.{}".format("dirt_1", str(random.randint(1, 8)).zfill(3))
        return self.environment.add_object(mesh)

    def process(self):
        if self.delay > 0:
            self.box.color = mathutils.Vector([0.0, 0.0, 0.0, 0.0])
            self.delay -= 1

        else:
            self.box.color = mathutils.Vector(self.environment.dirt_color) * 0.5
            if self.timer >= 1.0:
                self.ended = True
            else:
                self.timer += 0.008
                self.box.color[3] = 1.0 - (self.timer * 0.5)

                up_force = self.up_force.lerp(self.down_force, self.timer)
                self.box.worldPosition += up_force
                scale = self.grow * self.timer

                self.box.localScale = [scale, scale, scale]


class DirtClods(Particle):
    """ large dirt particle, doesn't rise very high
    3.0  growth good for normal explosion"""

    def __init__(self, environment, grow, position, delay=0):
        self.delay = delay
        super().__init__(environment)

        self.grow = grow

        s = 0.001 * grow
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), s * 5.0])
        self.down_force = mathutils.Vector([0.0, 0.0, -0.02])

        self.box.worldPosition = position.copy()
        self.alpha_scale = 0.5
        self.color = self.get_color()
        self.box.color = self.color

    def get_color(self):
        return mathutils.Vector(self.environment.dirt_color) * 0.5

    def add_box(self):
        mesh = "{}.{}".format("dirt_1", str(random.randint(1, 8)).zfill(3))
        return self.environment.add_object(mesh)

    def process(self):

        if self.delay > 0:
            self.box.color[3] = 0.0
            self.delay -= 1

        else:
            if self.timer >= 1.0:
                self.ended = True

            else:
                self.timer += 0.02
                c = 1.0 - (self.timer * self.alpha_scale)
                self.box.color[3] = c

                up_force = self.up_force.lerp(self.down_force, self.timer)
                self.box.worldPosition += up_force
                scale = self.grow * self.timer

                self.box.localScale = [scale, scale, scale]


class SmokeClods(DirtClods):
    """ large dirt particle, doesn't rise very high
    based on dirt clods"""

    def add_box(self):
        if random.randint(0, 1) == 1:
            mesh = "bubble_smoke"
        else:
            mesh = "round_smoke"

        mesh = "{}.{}".format(mesh, str(random.randint(1, 8)).zfill(3))
        return self.environment.add_object(mesh)

    def get_color(self):
        self.alpha_scale = 1.0
        return mathutils.Vector(self.environment.dirt_color)


class LargeBlast(AnimatedParticle):
    """ large random explosion particle
    to be added in a group using for in range"""

    def __init__(self, environment, growth, position, delay=0):
        self.delay = delay
        super().__init__(environment)
        self.max_sub_frame = 4

        self.grow = 1.004 * growth
        s = 0.008 * growth
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), s * 2.5])
        self.down_force = mathutils.Vector([0.0, 0.0, -0.01])

        self.box.worldPosition = position.copy()
        self.scale = (1.0 * self.grow) * self.timer

    def get_mesh_name(self):

        meshes = ["bang_1", "bang_3", "explosion_1"]
        return random.choice(meshes)

    def process(self):

        if self.delay > 0:
            self.box.color = [0.0, 0.0, 0.0, 0.0]
            self.delay -= 1

        else:
            if self.timer >= 1.0:
                self.ended = True

            else:
                self.timer += 0.02
                c = 1.0 - self.timer
                c = c * c * c

                a = 1.0
                self.box.color = [c, c * c, c * c * c, a]

                up_force = self.up_force.lerp(self.down_force, self.timer)
                self.box.worldPosition += up_force
                self.scale = self.grow * self.timer
                self.box.localScale = [self.scale, self.scale, self.scale]


class TowerSmoke(Particle):
    def __init__(self, environment, position):
        self.position = position
        self.position.x -= 0.15
        self.position.y -= 0.15

        super().__init__(environment)
        self.count = 0
        self.box.worldPosition = self.position
        self.interval = 24
        self.active = False
        self.get_interval()

    def add_box(self):
        return self.environment.add_object("dummy_object")

    def get_interval(self):
        self.interval = random.randint(4, 24)

    def get_variance(self, variance):
        v = variance
        random_vector = mathutils.Vector([random.uniform(-v, v), random.uniform(-v, v), 0.02])
        target_position = mathutils.Vector(self.position).to_3d()
        target_position += random_vector

        return target_position

    def add_smoke(self):
        DarkSmoke(self.environment, 2.5, self.get_variance(0.25))

        for i in range(3):
            SmallBlast(self.environment, 0.7, self.get_variance(0.15), i * 3)
            ExplosionSparks(self.environment, 0.2, self.get_variance(0.15), i * 3)

        self.count += 1

    def shut_down(self):
        self.ended = True

    def process(self):

        if self.active:
            self.timer += 1

            if self.timer > self.interval:
                self.get_interval()
                self.add_smoke()
                self.timer = 0


class DarkSmoke(Particle):
    """ smoke from a burning vehicle or smoke shells"""

    def __init__(self, environment, growth, position, delay=0):
        self.delay = delay
        super().__init__(environment)
        self.grow = 1.004 * growth
        s = 0.0005 * growth
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), s * 8.0])

        self.down_force = self.up_force.copy()
        self.down_force *= 0.5

        self.box.worldPosition = position.copy()
        self.scale = (1.0 * self.grow) * self.timer

    def add_box(self):
        if random.randint(0, 1) == 1:
            mesh = "{}.{}".format("bubble_smoke", str(random.randint(1, 8)).zfill(3))
        else:
            mesh = "{}.{}".format("round_smoke", str(random.randint(1, 8)).zfill(3))
        return self.environment.add_object(mesh)

    def process(self):

        if self.delay > 0:
            self.box.color = [0.0, 0.0, 0.0, 0.0]
            self.delay -= 1

        else:
            if self.timer >= 1.0:
                self.ended = True

            else:
                self.timer += 0.008

                a = 1.0 - self.timer
                c = (a * a)

                self.box.color = [c, c, c, a]

                up_force = self.up_force.lerp(self.down_force, self.timer)
                self.box.worldPosition += up_force
                s = 1.0 - self.timer
                inverse_scale = (s * s * s)
                self.scale = 1.0 - inverse_scale

                self.box.localScale = [self.scale, self.scale, self.scale]


class ArmorSparks(Particle):
    """a spark particle used to show deflection or non penetration"""

    def __init__(self, environment, growth, position, delay=0):
        self.delay = delay
        super().__init__(environment)

        self.grow = 1.002 * growth
        s = 0.03
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), random.uniform(0.0, s * 2.0)])
        self.box.worldPosition = position.copy()

    def add_box(self):
        mesh = "{}.{}".format("sparks", str(random.randint(1, 8)).zfill(3))
        return self.environment.add_object(mesh)

    def process(self):

        if self.delay > 0:
            self.box.color = [0.0, 0.0, 0.0, 0.0]
            self.delay -= 1

        else:
            if self.timer >= 1.0:
                self.ended = True
            else:
                self.timer += 0.04
                c = 1.0 - self.timer
                a = 1.0

                self.box.color = [c, c, c, a]

                self.box.worldPosition += self.up_force
                scale = (1.0 * self.grow) * self.timer

                self.box.localScale = [scale, scale, scale]


class WaterRipple(Particle):
    def __init__(self, environment, growth, position, delay=0):
        self.delay = delay
        super().__init__(environment)

        self.grow = 1.002 * growth

        self.box.worldPosition = position.copy()
        self.box.color = mathutils.Vector(self.environment.water_color)

    def add_box(self):
        mesh = "{}.{}".format("ground_hit", str(random.randint(1, 4)).zfill(3))
        return self.environment.add_object(mesh)

    def process(self):

        if self.delay > 0:
            self.box.color[3] = 0.0
            self.delay -= 1
        else:
            if self.timer >= 1.0:
                self.ended = True
            else:
                self.timer += 0.005
                a = 1.0 - self.timer

                self.box.color[3] = a

                ripple_1 = math.sin(self.timer * 20.0) * 0.2
                ripple_2 = math.sin(self.timer * 30.0) * 0.1

                scale = ((1.0 * self.grow) + ripple_1 - ripple_2) * self.timer
                self.box.localScale = [scale, scale, scale]


class WaterSpout(Particle):
    def __init__(self, environment, growth, position, delay=0):
        self.delay = delay
        super().__init__(environment)

        self.grow = 1.002 * growth
        s = 0.002
        self.up_force = mathutils.Vector(
            [random.uniform(-s, s), random.uniform(-s, s), random.uniform(s * 3.0, s * 5.0)])
        self.down_force = mathutils.Vector([0.0, 0.0, -0.01])
        self.box.worldPosition = position.copy()
        self.box.worldOrientation = bgeutils.up_vector(self.up_force)
        color_blend = random.uniform(0.2, 1.0)
        white = mathutils.Vector([1.0, 1.0, 1.0, 1.0])
        water = mathutils.Vector(self.environment.water_color)
        self.box.color = white.lerp(water, color_blend)
        self.z_scale = random.uniform(0.8, 1.4)
        self.speed = random.uniform(0.01, 0.02)

    def add_box(self):
        mesh = "{}.{}".format("smoke_blast", str(random.randint(1, 4)).zfill(3))
        return self.environment.add_object(mesh)

    def process(self):

        if self.delay > 0:
            self.box.color[3] = 0.0
            self.delay -= 1

        else:
            if self.timer >= 1.0:
                self.ended = True
            else:
                self.timer += self.speed
                a = 1.0 - self.timer

                self.box.color[3] = a

                up_force = self.up_force.lerp(self.down_force, self.timer)
                self.box.worldPosition += up_force
                scale = (1.0 * self.grow) * self.timer

                z_scale = scale * self.z_scale
                other_scale = (scale * scale) * 0.3

                self.box.localScale = [other_scale, z_scale, other_scale]


class ExplosionSparks(Particle):
    """a spark particle used to show deflection or non penetration"""

    def __init__(self, environment, growth, position, delay=0):
        self.delay = delay
        super().__init__(environment)

        self.grow = 1.002 * growth
        s = growth * 0.1
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), random.uniform(-s, s)])

        self.box.worldPosition = position.copy()

    def add_box(self):
        mesh = "{}.{}".format("sparks", str(random.randint(1, 8)).zfill(3))
        return self.environment.add_object(mesh)

    def process(self):

        if self.delay > 0:
            self.box.color = [0.0, 0.0, 0.0, 0.0]
            self.delay -= 1

        else:
            if self.timer >= 1.0:
                self.ended = True
            else:
                self.timer += 0.02
                c = 1.0 - self.timer
                a = 1.0

                self.box.color = [c, c * c, c * c * c, a]

                self.box.worldPosition += self.up_force
                scale = (1.0 * self.grow) * self.timer

                self.box.localScale = [scale, scale, scale]


class ArmorBlast(Particle):
    """a particle used to show shedding armor from a critical hit"""

    def __init__(self, environment, growth, position):
        super().__init__(environment)

        self.grow = 1.002 * growth

        s = 0.01
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), random.uniform(-s, s * 3.0)])
        self.down_force = mathutils.Vector([0.0, 0.0, -0.01])

        self.box.worldPosition = position.copy()
        self.box.color *= 0.5
        self.box.color[3] = 1.0

    def add_box(self):
        mesh = "{}.{}".format("simple_dirt", str(random.randint(1, 8)).zfill(3))
        return self.environment.add_object(mesh)

    def process(self):

        if self.timer >= 1.0:
            self.ended = True

        else:
            self.timer += 0.008
            c = 1.0 - self.timer
            a = 1.0 - (self.timer * 0.5)

            self.box.color = [c, c, c, a]

            up_force = self.up_force.lerp(self.down_force, self.timer)
            self.box.worldPosition += up_force
            scale = (1.0 * self.grow) * self.timer

            self.box.localScale = [scale, scale, scale]


class BuildingShell(Particle):

    def __init__(self, environment, adder, mesh):
        self.adder = adder
        self.mesh = "{}_collapse".format(mesh)
        super().__init__(environment)
        self.step = 0.0
        self.target = self.set_target()
        self.start = self.box.worldPosition.copy()
        self.end = self.start.copy()
        self.end.z = - 2.0
        self.start_scale = mathutils.Vector([1.0, 1.0, 1.0])
        self.end_scale = mathutils.Vector([1.2, 1.2, 0.0])

    def add_box(self):
        box = self.adder.scene.addObject(self.mesh, self.adder, 0)
        return box

    def set_target(self):
        target_point = mathutils.Vector([random.uniform(-0.03, 0.03), 1.0, random.uniform(-0.03, 0.03)])
        target_point.rotate(self.box.worldOrientation.copy())

        target = bgeutils.up_vector(target_point)

        return target

    def animate_box(self):
        self.box.worldOrientation = self.box.worldOrientation.lerp(self.target, bgeutils.smoothstep(self.step))

        inverted_square = 1.0 - (self.timer * self.timer)
        self.box.worldPosition = self.end.lerp(self.start, inverted_square)
        self.box.localScale = self.end_scale.lerp(self.start_scale, inverted_square)

    def process(self):

        if self.timer >= 1.0:
            self.ended = True
        else:
            self.timer += 0.002

            if self.step >= 1.0:
                self.step = 0.0
                self.target = self.set_target()
            else:
                self.step += random.uniform(0.01, 0.1)

        self.animate_box()


class BuildingExplosion(Particle):

    def __init__(self, environment, position, size, delay=0):
        self.position = self.get_variance(0.5, position)
        self.size = size
        self.delay = delay
        super().__init__(environment)

    def get_variance(self, variance, position):
        v = variance
        random_vector = mathutils.Vector([random.uniform(-v, v), random.uniform(-v, v), random.uniform(0.2, 1.0)])
        target_position = position.copy()
        target_position += random_vector

        return target_position

    def process(self):
        if self.delay > 0:
            self.delay -= 1
        else:
            self.ended = True

            explosion_pitch = random.uniform(0.7, 1.3)
            explosion_sound = "COLLAPSE_{}".format(random.randint(1, 7))

            SoundDummy(self.environment, self.position, explosion_sound, volume=0.25, pitch=explosion_pitch, delay=12)

            size = random.uniform(self.size, self.size * 2.0)
            amount = random.randint(1, 3)

            for i in range(amount):
                ArmorSparks(self.environment, size * 0.6, self.position, i)
                SmallBlast(self.environment, size * 1.5, self.position, i)
                ArmorChunk(self.environment, size * 0.5, self.position, i)
                ArmorBlast(self.environment, size * 0.5, self.position)


class SmokeEmitter(object):
    def __init__(self, environment, position, direction, size):
        self.environment = environment
        self.position = position.copy()
        self.direction = direction

        self.size = size

        self.timer = 0
        self.interval = 0
        self.average = 2
        self.get_interval()

    def get_interval(self):
        self.average *= 1.2
        self.interval = random.randint(int(self.average), int(self.average) * 2)

    def get_variance(self, variance, position):
        v = variance
        random_vector = mathutils.Vector([random.uniform(-v, v), random.uniform(-v, v), 0.02])
        target_position = position.copy()
        target_position += random_vector

        return target_position

    def update(self):
        if self.timer >= self.interval:

            if not self.direction:
                direction = self.get_variance(0.02, mathutils.Vector([0.0, 0.0, 0.0]))
            else:
                direction = self.direction

            DirectionalSmoke(self.environment, self.size * 2.0, self.get_variance(0.5, self.position),
                             direction)
            self.get_interval()
            self.timer = 0
        else:
            self.timer += 1


class ExplosionEmitter(object):
    def __init__(self, environment, position, direction, size, final):
        self.environment = environment
        self.position = position.copy()
        self.direction = direction
        self.final = final

        self.timer = 0
        self.interval = 0
        self.average = 10
        self.size = size
        self.get_interval()
        self.initial_explosion()

    def get_interval(self):
        self.average *= 1.5
        self.size *= 0.8
        self.interval = random.randint(int(self.average), int(self.average) * 2)

    def get_variance(self, variance, position):
        v = variance
        random_vector = mathutils.Vector([random.uniform(-v, v), random.uniform(-v, v), 0.02])
        target_position = mathutils.Vector(position)
        target_position += random_vector

        return target_position

    def initial_explosion(self):

        amount = random.randint(1, 3)

        for i in range(amount):
            position = self.get_variance(0.5, self.position.copy())
            BuildingExplosion(self.environment, position, self.size, delay=i * random.randint(1, 12))

    def update(self):
        if self.timer >= self.interval:

            if self.final:
                if not self.direction:
                    v = 0.01
                    random_vector = mathutils.Vector([random.uniform(-v, v), random.uniform(-v, v), 0.02])
                    direction = random_vector
                else:
                    direction = self.direction

                chunk_size = self.size * random.uniform(0.2, 0.4)
                FlyingRubble(self.environment, chunk_size, self.position, random.randint(1, 12),
                            direction=direction)

            blast_size = self.size * random.uniform(0.6, 1.2)
            BuildingExplosion(self.environment, self.position, blast_size)

            self.get_interval()
            self.timer = 0
        else:
            self.timer += 1


class BuildingDestruction(Particle):
    def __init__(self, environment, position, array, final):
        self.position = position
        self.final = final
        self.array = array

        self.array_size = array[0] * array[1]

        if self.array_size > 6:
            self.size = 0.5
        elif self.array_size > 1:
            self.size = 0.35
        else:
            self.size = 0.2

        self.increment = 0.002
        if not self.final:
            self.increment = 0.008

        super().__init__(environment)
        self.emitters = []

    def get_variance(self, variance, position):
        v = variance
        random_vector = mathutils.Vector([random.uniform(-v, v), random.uniform(-v, v), 0.02])
        target_position = position.copy()
        target_position += random_vector

        return target_position

    def place_elements(self):
        x, y = self.array
        base_position = mathutils.Vector(self.position).to_3d()

        center_offset = mathutils.Vector([self.array[0] * 0.5, self.array[1] * 0.5]).to_3d()
        offset_center = base_position.copy() + center_offset.copy()

        for xo in range(x):
            for yo in range(y):
                if xo == 0 or xo == x - 1 or yo == 0 or yo == y - 1:
                    tile_position = [self.position[0] + xo, self.position[1] + yo]
                    local_position = mathutils.Vector(tile_position).to_3d()

                    if self.array_size == 1:
                        direction_vector = None
                    else:
                        direction_vector = local_position.copy() - offset_center.copy()
                        direction_vector.length = 0.01

                    if self.final:
                        smoke_size = self.size * 4.0
                        explosion_size = self.size * 3.0
                    else:
                        smoke_size = self.size * 2.5
                        explosion_size = self.size

                    self.emitters.append(SmokeEmitter(self.environment, local_position, direction_vector, smoke_size))
                    if direction_vector:
                        direction_vector = direction_vector.copy()

                    self.emitters.append(
                        ExplosionEmitter(self.environment, local_position, direction_vector, explosion_size, self.final))

                    if self.final:
                        set_tile = [self.position[0] + xo, self.position[1] + yo]
                        effects.Smoke(self.environment, 1, None, set_tile, 0)
                        if random.randint(0, 1) and self.array_size > 1:

                            rubble_size = random.uniform(0.5, 1.0)
                            BuildingRubble(self.environment, self.get_variance(0.5, local_position), rubble_size)

    def process(self):
        if not self.emitters:
            self.place_elements()
        else:
            if self.timer >= 1.0:
                self.ended = True
            else:
                self.timer += self.increment
                for emitter in self.emitters:
                    emitter.update()
