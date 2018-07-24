import bge
import mathutils
import random
import bgeutils
import math

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
                   "rubble": 6}


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


class DestroyedVehicle(Particle):
    def __init__(self, environment, position, size):
        super().__init__(environment)
        self.position = position
        self.size = size
        self.place_elements()
        self.ended = True

    def place_elements(self):
        ShellImpact(self.environment, self.position, self.size * 3, is_hit=True)
        VehicleRubble(self.environment, self.position, self.size * 0.3)


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
        Decal(self.environment, "{}_{}".format(self.mesh_name, 3), self.box.worldPosition.copy(),
              self.box.localScale.copy(), False)


class BaseExplosion(Particle):
    """the base explosion template"""

    def __init__(self, environment, position, rating, delay=0, is_hit=False):
        self.is_hit = is_hit
        self.position = position
        super().__init__(environment)
        self.delay = delay
        self.sound = "EXPLODE_1"
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
        if self.sound:
            SoundDummy(self.environment, self.impact_position, self.sound)

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
        self.delay = 12
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


class ShellDeflection(BaseExplosion):

    def get_details(self):
        self.delay = 12
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
        self.delay = 12
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
        adding_position =  self.adder.worldPosition.copy()

        SoundDummy(self.environment, adding_position, sound, pitch=hit_pitch)

        size = 0.015 + (self.rating * 0.15)
        size += random.uniform(-0.05, 0.05)

        GunFlash(self.environment, self.adder, size, speed, False)
        delay = int(1.0 / speed)

        GunFlash(self.environment, self.adder, size * 2.0, speed, True)
        SmallSmoke(self.environment, size, adding_position, delay * 2)

        for i in range(4):
            ExplosionSparks(self.environment, size * 0.2, adding_position, delay=i)


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
        self.mesh = "{}.{}".format("rubble", str(random.randint(1, 6)).zfill(3))
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


class RockChunk(Particle):
    """a chunk of rock that flies out from the center"""

    def __init__(self, environment, growth, position, delay=0):
        self.delay = delay
        super().__init__(environment)

        self.grow = 1.002 * growth
        self.rotation = [random.uniform(-0.03, 0.03) for _ in range(3)]
        s = 0.1 * growth
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), s * 0.5])
        self.down_force = mathutils.Vector([0.0, 0.0, -0.01])

        self.box.worldPosition = position.copy()
        self.box.color = mathutils.Vector(self.environment.dirt_color)
        self.box.applyRotation([random.uniform(-1.0, 1.0) for _ in range(3)])
        self.max_scale = random.uniform(0.1, 0.2)

    def add_box(self):
        mesh = "{}.{}".format("chunk_1", str(random.randint(1, 8)).zfill(3))
        return self.environment.add_object(mesh)

    def process(self):
        if self.delay > 0:
            self.box.color = mathutils.Vector([0.0, 0.0, 0.0, 0.0])
            self.delay -= 1

        else:
            self.box.color = mathutils.Vector(self.environment.dirt_color)
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


class ArmorChunk(Particle):
    """ a smaller chunk of armor particle"""

    def __init__(self, environment, growth, position, delay=0):
        self.delay = delay
        super().__init__(environment)

        self.grow = 1.002 * growth
        self.rotation = [random.uniform(-0.1, 0.1) for _ in range(3)]
        s = 0.05 * growth
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), s * 0.5])
        self.down_force = mathutils.Vector([0.0, 0.0, -0.02])

        self.box.worldPosition = position.copy()
        self.box.color[3] = 0.0
        self.box.applyRotation([random.uniform(-1.0, 1.0) for _ in range(3)])
        self.max_scale = random.uniform(0.1, 0.2)

    def add_box(self):
        mesh = "{}.{}".format("chunk_1", str(random.randint(1, 8)).zfill(3))
        return self.environment.add_object(mesh)

    def process(self):
        if self.delay > 0:
            self.box.color[3] = 0.0
            self.delay -= 1

        else:
            self.box.color = mathutils.Vector(self.environment.dirt_color)
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
        self.box.color = mathutils.Vector(self.environment.dirt_color) * 0.5

    def add_box(self):
        mesh = "{}.{}".format("dirt_1", str(random.randint(1, 8)).zfill(3))
        return self.environment.add_object(mesh)

    def process(self):

        if self.delay > 0:
            self.box.color = [0.0, 0.0, 0.0, 0.0]
            self.delay -= 1

        else:
            self.box.color = mathutils.Vector(self.environment.dirt_color) * 0.5
            if self.timer >= 1.0:
                self.ended = True

            else:
                self.timer += 0.02
                self.box.color[3] = 1.0 - (self.timer * 0.5)

                up_force = self.up_force.lerp(self.down_force, self.timer)
                self.box.worldPosition += up_force
                scale = self.grow * self.timer

                self.box.localScale = [scale, scale, scale]


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
        self.down_force = self.up_force.copy() * 0.5

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
                # c = 1.0 - self.timer
                #
                # self.box.color[0] += 0.002
                # self.box.color[1] = c

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
        self.up_force = mathutils.Vector([random.uniform(-s, s), random.uniform(-s, s), random.uniform(s * 3.0, s * 5.0)])
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

