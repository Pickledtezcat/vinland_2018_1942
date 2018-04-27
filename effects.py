import bge
import mathutils
import bgeutils
import random


class Effect(object):

    effect_type = "NONE"

    def __init__(self, environment, effect_id, position=None, turn_timer=0):
        self.environment = environment
        self.position = position
        self.box = self.add_box()

        self.ended = False
        self.turn_timer = turn_timer
        self.max_turns = 1

        if not effect_id:
            self.effect_id = self.set_id()
        else:
            self.effect_id = effect_id

        self.environment.effects[self.effect_id] = self

    def add_box(self):
        return None

    def set_id(self):
        effect_id = "effect_{}".format(self.environment.get_new_id())
        return effect_id

    def terminate(self):
        if self.box:
            self.box.endObject()

    def update(self):

        self.process()

    def process(self):
        pass

    def save_to_dict(self):
        self.terminate()
        return [self.effect_type, self.effect_id, self.position, self.turn_timer]

    def cycle(self):
        self.turn_timer += 1

        if self.max_turns > 0:
            if self.turn_timer >= self.max_turns:
                self.ended = True


class Smoke(Effect):

    effect_type = "SMOKE"

    def __init__(self, environment, effect_id, position, turn_timer):
        smoke_tile = self.environment.get_tile(position)

        if not smoke_tile["smoke"]:
            super().__init__(environment, effect_id, position, turn_timer)

            self.environment.set_tile(self.position, "smoke", True)
            self.max_turns = 10

            self.max_target = 1.0
            self.max_size = 0.0

            self.deploy = random.uniform(0.0005, 0.0015)

            self.pulse_timer = 0.0
            self.pulsing = True
        else:
            # add an effect to show the explosion
            pass

    def add_box(self):
        box = self.environment.add_object("smoke")
        box.worldPosition = mathutils.Vector(self.position).to_3d()
        return box

    def process(self):

        self.max_target = 1.0 - (0.09 * self.turn_timer)
        self.max_size = bgeutils.interpolate_float(self.max_size, self.max_target, 0.02)

        if self.pulsing:
            if self.pulse_timer < 1.0:
                self.pulse_timer += 0.01
            else:
                self.pulsing = False
        else:
            if self.pulse_timer > 0.0:
                self.pulse_timer -= 0.01
            else:
                self.pulsing = True

        min_size = self.max_size * 0.7

        min_size = mathutils.Vector([min_size, min_size, min_size])
        max_size = mathutils.Vector([self.max_size, self.max_size, self.max_size])

        self.box.localScale = max_size.lerp(min_size, bgeutils.smoothstep(self.pulse_timer))

    def terminate(self):
        self.environment.set_tile(self.position, "smoke", False)

        if self.box:
            self.box.endObject()

    def cycle(self):
        super().cycle()
