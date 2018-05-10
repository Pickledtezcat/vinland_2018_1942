import bge
import mathutils
import bgeutils
import random
import particles


class Effect(object):

    effect_type = "NONE"

    def __init__(self, environment, team, effect_id, position=None, turn_timer=0):
        self.environment = environment
        self.team = team
        self.position = position
        self.box = self.add_box()
        self.delay = 1

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
        return [self.effect_type, self.team, self.effect_id, self.position, self.turn_timer]

    def cycle(self):
        self.turn_timer += 1

        if self.max_turns > 0:
            if self.turn_timer >= self.max_turns:
                self.ended = True


class Smoke(Effect):

    effect_type = "SMOKE"

    def __init__(self, environment, team, effect_id, position, turn_timer):
        smoke_tile = environment.get_tile(position)

        if not smoke_tile["smoke"]:
            super().__init__(environment, team, effect_id, position, turn_timer)

            self.environment.set_tile(self.position, "smoke", True)
            self.max_turns = 5

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

        min_size_vector = mathutils.Vector([min_size, min_size, min_size])
        max_size_vector = mathutils.Vector([self.max_size, self.max_size, self.max_size])

        self.box.localScale = max_size_vector.lerp(min_size_vector, bgeutils.smoothstep(self.pulse_timer))

    def terminate(self):
        self.environment.set_tile(self.position, "smoke", False)

        if self.box:
            self.box.endObject()


class AirSupport(Effect):
    effect_type = "GENERAL_AIR_SUPPORT"

    def __init__(self, environment, team, effect_id, position, turn_timer):

        super().__init__(environment, team, effect_id, position, turn_timer)

        self.pulse_timer = 0.0
        self.pulsing = True
        self.max_turns = 6

        self.min_size = 0.0
        self.max_size = 0.0

        self.box.localScale = [0.0, 0.0, 0.0]
        self.delay = 1
        self.radius = 4

    def add_box(self):
        box = self.environment.add_object("aircraft_icon")
        box.worldPosition = mathutils.Vector(self.position).to_3d()
        return box

    def process(self):

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

        if self.turn_timer > self.max_turns - 2:
            self.min_size -= 0.01
            self.max_size -= 0.01
        else:
            self.min_size = min(0.7, self.min_size + 0.01)
            self.max_size = min(1.0, self.max_size + 0.01)

        min_size_vector = mathutils.Vector([self.min_size, self.min_size, self.min_size])
        max_size_vector = mathutils.Vector([self.max_size, self.max_size, self.max_size])

        self.box.localScale = max_size_vector.lerp(min_size_vector, bgeutils.smoothstep(self.pulse_timer))


class SpotterPlane(AirSupport):

    effect_type = "SPOTTER_PLANE"

    def __init__(self, environment, team, effect_id, position, turn_timer):

        super().__init__(environment, team, effect_id, position, turn_timer)

        self.max_turns = 6
        self.delay = 1
        self.radius = 4

    def add_box(self):
        box = self.environment.add_object("aircraft_icon")
        box.worldPosition = mathutils.Vector(self.position).to_3d()
        return box


class AirStrike(AirSupport):
    effect_type = "AIR_STRIKE"

    def __init__(self, environment, team, effect_id, position, turn_timer):
        super().__init__(environment, team, effect_id, position, turn_timer)

        self.max_turns = 3
        self.triggered = False

        self.delay = 1
        self.power = 25
        self.shots = 12
        self.scatter = 4
        self.radius = 2

    def cycle(self):
        super().cycle()

        if self.turn_timer == self.delay:
            if not self.triggered:
                self.triggered = True
                self.detonate()

    def detonate(self):

        for s in range(self.shots):

            damage = self.power
            shock = self.power
            base_target = 3
            penetration = int(self.power * 0.5)

            target_position = mathutils.Vector(self.position)

            hit_list = []

            scatter = self.scatter
            roll = bgeutils.d6(2)
            effective_scatter = scatter
            status = "MISS!"

            if roll <= base_target:
                status = "ON TARGET"
                effective_scatter = scatter * 0.5

            scatter_roll = [random.uniform(-effective_scatter, effective_scatter) for _ in range(2)]
            hit_position = target_position + mathutils.Vector(scatter_roll)
            hit_position = bgeutils.position_to_location(hit_position)
            hit_tile = self.environment.get_tile(hit_position)

            if hit_tile:
                explosion = particles.DummyExplosion(self.environment, hit_position, 1)
                particles.DebugText(self.environment, status, explosion.box)

                explosion_chart = [0, 8, 16, 32, 64, 126, 256, 1024, 4096]

                for x in range(-2, 3):
                    for y in range(-2, 3):
                        reduction_index = max(x, y)
                        reduction = explosion_chart[reduction_index]

                        effective_penetration = max(0, penetration - reduction)
                        effective_damage = max(0, damage - reduction)
                        effective_shock = max(0, shock - reduction)

                        if effective_damage > 0:
                            blast_location = (hit_position[0] + x, hit_position[1] + y)
                            blast_tile = self.environment.get_tile(blast_location)
                            if blast_tile:
                                occupied = blast_tile["occupied"]
                                if occupied:
                                    effective_accuracy = int(effective_damage * 0.5)
                                    effective_origin = hit_position

                                    target_agent = self.environment.agents[occupied]

                                    facing = target_agent.get_stat("facing")
                                    location = target_agent.get_stat("position")

                                    cover_check = self.environment.turn_manager.check_cover(facing, effective_origin,
                                                                                            location)

                                    flanked, covered, reduction = cover_check
                                    armor = target_agent.get_stat("armor")

                                    if flanked:
                                        armor_value = armor[1]
                                    else:
                                        armor_value = armor[0]

                                    if armor_value == 0:
                                        armor_target = 7
                                    else:
                                        armor_target = max(0, effective_penetration - armor_value)

                                    if target_agent.agent_type == "INFANTRY":
                                        base_target = target_agent.get_stat("number") + 2
                                    else:
                                        base_target = target_agent.get_stat("size")

                                    if target_agent.has_effect("PRONE"):
                                        effective_accuracy -= 2
                                    if covered:
                                        effective_accuracy -= 2

                                    base_target += effective_accuracy
                                    message = {"agent_id": occupied, "header": "HIT",
                                               "contents": [effective_origin, base_target,
                                                            armor_target, effective_damage,
                                                            effective_shock]}
                                    hit_list.append(message)

            for hit_message in hit_list:
                self.environment.message_list.append(hit_message)


