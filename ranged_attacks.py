import mathutils
import random
import particles
import bgeutils
import effects


class Projectile(object):
    def __init__(self, environment, hit_tile, owner, hits, team, rating):
        self.environment = environment
        self.owner = owner
        self.hit_tile = hit_tile
        self.hits = hits
        self.rating = rating
        self.team = team

        self.speed = random.uniform(0.2, 0.4)
        self.progress = 0.0

        self.origin = self.get_origin()
        self.path = self.generate_bomb_path()
        self.box = self.add_box()

    def add_box(self):
        box = self.environment.add_object("air_strike_bomb")
        return box

    def get_origin(self):
        return self.environment.enemy_air_strike_origin

    def generate_bomb_path(self):

        start = mathutils.Vector(self.origin).to_3d()
        end = mathutils.Vector(self.hit_tile).to_3d()

        handle_1 = end.copy()
        handle_2 = end.copy()
        start.z = 12
        handle_1.z = 4
        handle_2.z = 4

        return mathutils.geometry.interpolate_bezier(start, handle_1, handle_2, end, 40)

    def follow_bomb_path(self):
        current_index = int(self.progress)
        next_index = current_index + 1
        current_progress = self.progress - current_index

        current_node = self.path[current_index]
        next_node = self.path[next_index]
        target_vector = next_node - current_node
        orientation = bgeutils.track_vector(target_vector)

        current_position = current_node.lerp(next_node, current_progress)
        self.box.worldPosition = current_position
        self.box.worldOrientation = self.box.worldOrientation.lerp(orientation, 0.2)

    def update(self):

        if int(self.progress) >= 39.0:
            self.detonate()
            self.box.endObject()
            return True
        else:
            self.animate_shell()
            self.follow_bomb_path()
            self.progress += self.speed
            return False

    def get_particle_type(self):
        tile = self.environment.get_tile(self.hit_tile)
        hit_type = None
        if tile:
            hit_type = "MISS"

            if tile["occupied"]:
                occupier = self.environment.agents[tile["occupied"]]
                if occupier:
                    if occupier.agent_type == "VEHICLE":
                        hit_type = "HIT"

            if tile["building"]:
                hit_type = "HIT"

            if tile["water"]:
                hit_type = "WATER"

        return hit_type

    def add_particle(self):
        hit_position = self.box.worldPosition.copy()
        hit_position.z = 0

        hit_type = self.get_particle_type()
        if hit_type:
            if hit_type == "HIT":
                particles.ShellImpact(self.environment, hit_position, self.rating, is_hit=True)
            elif hit_type == "WATER":
                particles.WaterHit(self.environment, hit_position, self.rating)
            else:
                particles.ShellExplosion(self.environment, hit_position, self.rating, is_hit=True)

    def animate_shell(self):
        pass

    def detonate(self):
        for hit in self.hits:
            self.environment.message_list.append(hit)
        self.add_particle()


class Bomb(Projectile):
    def __init__(self, environment, hit_tile, owner, hits, team, rating):
        super().__init__(environment, hit_tile, owner, hits, team, rating)

    def get_origin(self):
        if self.team == 2:
            return self.environment.enemy_air_strike_origin
        else:
            return self.environment.player_air_strike_origin


class ArtilleryShell(Projectile):
    def __init__(self, environment, hit_tile, owner, hits, adder, smoke, team, rating):
        self.adder = adder
        self.smoke = smoke
        self.shell_speed = self.get_shell_speed()
        super().__init__(environment, hit_tile, owner, hits, team, rating)

    def get_shell_speed(self):
        return 6.0

    def add_box(self):
        box = self.environment.add_object("large_shell")
        return box

    def generate_bomb_path(self):

        start = self.adder.worldPosition.copy()
        end = mathutils.Vector(self.hit_tile).to_3d()

        target_vector = end - start
        distance = target_vector.length

        # speed * 3 for grenades, * 5 for artillery

        if distance > 0:
            self.speed = (1.0 / distance) * 3.0
        else:
            self.speed = 0.01

        handle_1 = start.lerp(end, 0.5)
        handle_2 = handle_1.copy()
        handle_1.z = distance * 0.25
        handle_2.z = distance * 0.25

        return mathutils.geometry.interpolate_bezier(start, handle_1, handle_2, end, 40)

    def detonate(self):
        if self.smoke:
            effects.Smoke(self.environment, self.team, None, self.hit_tile, 0)
        else:
            for hit in self.hits:
                self.environment.message_list.append(hit)
            self.add_particle()


class GrenadeShell(ArtilleryShell):

    def get_shell_speed(self):
        return 3.0

    def add_box(self):
        box = self.environment.add_object("grenade_shell")
        return box

    def animate_shell(self):
        grenade_shell = bgeutils.get_ob("shell", self.box.children)
        grenade_shell.applyRotation([0.2, 0.1, 0.05])

    def add_particle(self):
        hit_position = self.box.worldPosition.copy()
        hit_position.z = 0

        hit_type = self.get_particle_type()
        if hit_type:
            if hit_type == "HIT":
                particles.ShellImpact(self.environment, hit_position, self.rating, is_hit=True)
            elif hit_type == "WATER":
                particles.WaterHit(self.environment, hit_position, self.rating)
            else:
                particles.GrenadeExplosion(self.environment, hit_position, self.rating, is_hit=True)


class RocketShell(ArtilleryShell):

    def get_shell_speed(self):
        return 3.0

    def add_box(self):
        box = self.environment.add_object("rocket_shell")
        return box

    def animate_shell(self):
        grenade_shell = bgeutils.get_ob("shell", self.box.children)
        grenade_shell.applyRotation([0.0, 0.2, 0.0], True)


def ranged_attack(environment, contents):
    accuracy, damage, target_position, scatter, special = contents

    base_target = accuracy

    roll = bgeutils.d6(2)
    effective_scatter = scatter
    on_target = False
    direct_hit = False

    if roll <= base_target:
        effective_scatter = scatter * 0.5
        on_target = True

    scatter_roll = [random.uniform(-effective_scatter, effective_scatter) for _ in range(2)]
    hit_location = mathutils.Vector(target_position) + mathutils.Vector(scatter_roll)
    effective_origin = bgeutils.position_to_location(hit_location)
    hit_tile = environment.get_tile(effective_origin)

    hit_list = []
    if hit_tile:
        if "SMOKE" in special:
            projectile = {"projectile_type": "SMOKE", "hit_position": effective_origin, "hit_list": hit_list}
            return projectile

        special.append("TRACKS")

        current_explosion = damage
        explosion_chart = []

        for i in range(6):
            explosion_chart.append(current_explosion)
            current_explosion = int(current_explosion * 0.5)

        for x in range(-3, 4):
            for y in range(-3, 4):

                blast_location = (effective_origin[0] + x, effective_origin[1] + y)
                reduction_vector = int((hit_location - mathutils.Vector(blast_location)).length)

                effective_damage = effective_shock = explosion_chart[reduction_vector]

                if effective_damage > 0:
                    blast_tile = environment.get_tile(blast_location)
                    if blast_tile:
                        occupied = blast_tile["occupied"]
                        if occupied:
                            effective_accuracy = effective_damage
                            building_tile = environment.get_tile(blast_location)
                            building = None
                            building_armor = 0

                            if building_tile:
                                building_id = building_tile["building"]
                                if building_id:
                                    # TODO building damage
                                    building = environment.buildings[building_id]
                                    building_armor = building.get_stat("armor")

                            target_agent = environment.agents[occupied]

                            if blast_location == effective_origin and on_target:
                                direct_hit = True
                                special.append("DIRECT_HIT")
                                flanked = True
                                covered = False
                            else:
                                facing = target_agent.get_stat("facing")
                                location = target_agent.get_stat("position")
                                cover_check = environment.turn_manager.check_cover(facing, effective_origin,
                                                                                   location)
                                flanked, covered, reduction = cover_check

                            armor = target_agent.get_stat("armor")
                            armor_value = armor[0]

                            if building:
                                armor_value = building_armor
                                if armor_value > 0:
                                    effective_shock = int(effective_shock * 0.5)

                            elif flanked:
                                armor_value = armor[1]

                            if armor_value == 0:
                                armor_target = 7
                            else:
                                if direct_hit:
                                    armor_penetration = int(round(effective_damage * 0.5))
                                else:
                                    armor_penetration = int(round(effective_damage * 0.25))

                                armor_target = max(0, armor_penetration - armor_value)

                            if target_agent.agent_type == "INFANTRY":
                                base_target = 3 + int(target_agent.get_stat("number") * 0.5)
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
                                                    effective_shock, special]}

                            hit_list.append(message)

        projectile = {"projectile_type": "EXPLOSION", "hit_position": effective_origin, "hit_list": hit_list}
        return projectile

    return None
