import bge
import bgeutils
import mathutils
from ai_states import *


class TurnManager(object):
    turn_type = "PROTOTYPE"

    def __init__(self, environment):

        self.team = -1
        self.environment = environment
        self.finished = False
        self.active_agent = None
        self.last_active_agent = None
        self.movement_icons = []
        self.turn_id = 0
        self.tile_over = None
        self.started = False
        self.busy = False
        self.busy_count = 0
        self.end_count = 0
        self.end_turn_allowed = False

        self.check_valid_units()
        self.valid_units = True
        self.canvas_type = "BLANK"
        self.environment.update_map()

    def set_canvas(self, canvas_type):
        if self.canvas_type != canvas_type:
            self.environment.terrain_canvas.set_update(canvas_type)
            self.canvas_type = canvas_type

    def check_valid_units(self):
        team_units = []
        busy = False
        all_units = False
        living_units = False
        reserve_units = []

        for effect_key in self.environment.effects:
            effect = self.environment.effects[effect_key]
            if effect.busy:
                self.busy = True
                return

        for agent_key in self.environment.agents:
            agent = self.environment.agents[agent_key]
            if agent.get_stat("team") == self.team:
                all_units = True

                if agent.busy:
                    busy = True

                is_active = not agent.has_effect("BAILED_OUT")
                free_actions = agent.get_stat("free_actions") > 0
                unloaded = not agent.has_effect("LOADED")
                alive = not agent.has_effect("DYING")

                if alive:
                    living_units = True

                if is_active and unloaded and alive:
                    if free_actions:
                        team_units.append(agent_key)
                    else:
                        reserve_units.append(agent_key)

        if not living_units and all_units:
            # TODO create game over mode
            if self.team == 1:
                self.environment.switch_modes("EDITOR")
                return

        if not team_units:
            if self.end_turn_allowed:
                self.active_agent = None
            else:
                if not self.active_agent:
                    if reserve_units:
                        self.active_agent = reserve_units[0]
                        self.update_pathfinder()
                    else:
                        self.active_agent = None
                else:
                    active_agent = self.environment.agents[self.active_agent]
                    bailed = active_agent.has_effect("BAILED_OUT")
                    loaded = active_agent.has_effect("LOADED")
                    dead = active_agent.has_effect("DYING")

                    if bailed or loaded or dead:
                        self.active_agent = None

        else:
            if not self.active_agent:
                self.active_agent = team_units[0]
                self.update_pathfinder()
            else:
                active_agent = self.environment.agents[self.active_agent]
                bailed = active_agent.has_effect("BAILED_OUT")
                loaded = active_agent.has_effect("LOADED")
                dead = active_agent.has_effect("DYING")

                if bailed or loaded or dead:
                    self.active_agent = team_units[0]
                    self.update_pathfinder()

        if self.active_agent:
            self.valid_units = True
        else:
            self.valid_units = False

        if not busy:
            self.busy_count += 1
            if self.busy_count > 20:
                self.busy = False
                self.busy_count = 0
        else:
            self.busy = True
            self.busy_count = 0

    def update_pathfinder(self):
        self.environment.pathfinder.update_graph()

    def update(self):
        if not self.started:
            self.started = True
            self.check_valid_units()
            self.update_pathfinder()
            self.environment.update_map()

        if self.end_check():
            self.finished = True
        else:
            self.process()

    def process(self):
        pass

    def end_check(self):
        self.check_valid_units()
        if not self.valid_units:
            if self.end_count > 60 and not self.busy:
                return True
            else:
                self.busy = True
                self.end_count += 1

        return False

    def clear_movement_icons(self):
        for icon in self.movement_icons:
            icon.endObject()
        self.movement_icons = []

    def update_buildings(self):
        for building_key in self.environment.buildings:
            building = self.environment.buildings[building_key]
            building.turn_cycle()

    def refresh_units(self):
        for agent_key in self.environment.agents:
            agent = self.environment.agents[agent_key]
            if agent.get_stat("team") != self.team:
                agent.regenerate()

    def get_target_data(self, origin_id, target_id, action_id, tile_over, target_type="NORMAL"):

        origin_agent = self.environment.agents[origin_id]
        target_agent = None

        if target_id in self.environment.agents:
            target_agent = self.environment.agents[target_id]

        current_action = origin_agent.get_stat("action_dict")[action_id]
        origin = origin_agent.get_stat("position")

        if current_action["action_type"] != "WEAPON":
            target_data = {"target_type": "INVALID"}
            return target_data

        weapon = current_action["weapon_stats"]
        accuracy = weapon["accuracy"]
        ammo_modifier = 1.0
        if origin_agent.has_effect("SPECIAL_AMMO"):
            ammo_modifier = 1.2

        penetration = int(weapon["penetration"] * ammo_modifier)
        damage = int(weapon["damage"] * ammo_modifier)
        shock = int(weapon["shock"] * ammo_modifier)
        distance_reduction = 0

        if "EXPLOSION" in current_action["effect"] or "SMOKE" in current_action["effect"]:
            if not tile_over:
                target_data = {"target_type": "INVALID"}
                return target_data
            else:
                accuracy += 3
                target_location = tile_over

                target_position = mathutils.Vector(target_location)
                origin_position = mathutils.Vector(origin)

                target_vector = origin_position - target_position

                distance = target_vector.length
                distance_reduction = int(round(distance * 0.333))

                # TODO add modifiers for movement and size
                accuracy -= distance_reduction

                if origin_agent.has_effect("MOVED"):
                    accuracy -= 2

                if origin_agent.has_effect("VISION"):
                    accuracy += 2

                if origin_agent.has_effect("STEADY_AIM"):
                    accuracy += 4

                base_target = accuracy

                target_data = {"target_type": "EXPLOSION", "contents": [damage, shock, base_target, penetration,
                                                                        distance_reduction]}
                return target_data

        elif target_type == "BUILDING":
            target_location = tile_over
            target_position = mathutils.Vector(target_location)
            origin_position = mathutils.Vector(origin)

            target_vector = origin_position - target_position

            distance = target_vector.length
            distance_reduction = int(round(distance * 0.333))

            building_tile = self.environment.get_tile(tile_over)
            armor_value = 0

            if building_tile:
                building_id = building_tile["building"]
                if building_id:
                    building = self.environment.buildings[building_id]
                    armor_value = building.get_stat("armor")
                    if armor_value > 0:
                        shock = int(shock * 0.5)

            if armor_value == 0:
                armor_target = 7
            else:
                armor_reduction = distance_reduction - 1
                penetration -= armor_reduction
                armor_target = penetration - armor_value

            target_data = {"target_type": "BUILDING", "contents": [damage, shock, 12, penetration, distance_reduction,
                                                                   armor_target]}
            return target_data

        else:
            if not target_agent:
                target_data = {"target_type": "INVALID"}
                return target_data

            else:
                if origin_agent.has_effect("MOVED"):
                    accuracy -= 2

                if origin_agent.has_effect("VISION"):
                    accuracy += 2

                if origin_agent.has_effect("STEADY_AIM"):
                    accuracy += 4

                # get target_info
                facing = target_agent.get_stat("facing")
                location = target_agent.get_stat("position")

                flanked, covered, reduction = self.check_cover(origin, facing, location)

                if target_agent.agent_type == "INFANTRY":
                    base_target = 3 + int(target_agent.get_stat("number") * 0.5)
                else:
                    base_target = target_agent.get_stat("size")

                if target_agent.check_immobile():
                    base_target += 1

                if reduction > 1:
                    if target_agent.has_effect("PRONE"):
                        base_target -= 1

                if covered:
                    base_target -= 2

                if target_agent.has_effect("MOVED"):
                    base_target -= 1
                if target_agent.has_effect("FAST"):
                    base_target -= 1

                if target_agent.has_effect("MARKED"):
                    base_target += 2

                if target_agent.has_effect("SPOTTED"):
                    base_target += 1

                base_target -= reduction
                base_target += accuracy

                armor = target_agent.get_stat("armor")

                building_tile = self.environment.get_tile(tile_over)
                armor_value = armor[0]

                if building_tile:
                    building_id = building_tile["building"]
                    if building_id:
                        building = self.environment.buildings[building_id]
                        armor_value = building.get_stat("armor")
                        if armor_value > 0:
                            shock = int(shock * 0.5)

                if flanked:
                    damage = int(damage * 1.5)
                    shock = int(shock * 1.5)
                    armor_value = armor[1]

                if target_agent.has_effect("RECOGNIZED"):
                    armor_value = max(0, armor_value - 1)

                if armor_value == 0:
                    armor_target = 7
                else:
                    armor_reduction = reduction - 1
                    penetration -= armor_reduction
                    armor_target = penetration - armor_value

                target_data = {"target_type": "DIRECT_ATTACK", "contents": [damage, shock, flanked, covered,
                                                                            base_target, armor_target]}
                return target_data

    def check_cover(self, origin, facing, target):

        flanked = False
        covered = False

        tile = self.environment.pathfinder.graph[tuple(target)]

        target_vector = mathutils.Vector(origin) - mathutils.Vector(target)

        distance = target_vector.length
        reduction = int(round(distance * 0.333))

        if origin == target:
            flanked = True
            covered = False
        else:
            facing_vector = mathutils.Vector(facing)
            angle = int(round(target_vector.angle(facing_vector) * 57.295779513))

            if angle > 85.0:
                flanked = True

            if reduction > 1:
                if tile.cover:
                    covered = True
                else:
                    cover_facing = tuple(bgeutils.get_facing(target_vector))
                    cover_dict = {(0, 1): ["NORTH"],
                                  (1, 0): ["EAST"],
                                  (0, -1): ["SOUTH"],
                                  (-1, 0): ["WEST"],
                                  (-1, -1): ["WEST", "SOUTH"],
                                  (-1, 1): ["WEST", "NORTH"],
                                  (1, 1): ["NORTH", "EAST"],
                                  (1, -1): ["SOUTH", "EAST"],
                                  (0, 0): []}

                    cover_keys = cover_dict[cover_facing]

                    for cover_key in cover_keys:
                        if cover_key in tile.cover_directions:
                            covered = True

        return flanked, covered, reduction

    def update_targeting_data(self):

        if self.active_agent:

            origin_id = self.active_agent
            origin_agent = self.environment.agents[self.active_agent]
            active_action_id = origin_agent.active_action

            for agent_key in self.environment.agents:
                agent = self.environment.agents[agent_key]
                if agent_key != self.team:
                    position = agent.get_stat("position")
                    agent.target_data = self.get_target_data(origin_id, agent_key, active_action_id, position)

    def end(self):
        self.update_buildings()
        self.refresh_units()
        self.environment.cycle_effects(self.team)
        self.clear_movement_icons()


movement_color = [0.59, 1.0, 0.9, 1.0]


class PlayerTurn(TurnManager):

    def __init__(self, environment):
        super().__init__(environment)
        self.team = 1
        self.timer = 0

        self.path = None
        self.max_actions = 0
        self.moved = 0.0
        self.current_path = None

    def process_path(self):

        new_path = self.environment.pathfinder.current_path

        if self.active_agent:
            if new_path != self.current_path:
                self.current_path = new_path
                self.draw_path()

    def get_cover_icon(self, position):
        tile = self.environment.pathfinder.graph[position]
        if tile.cover:
            return 15

        x, y = position

        search_array = [(0, -1, 1), (1, 0, 2), (0, 1, 4), (-1, 0, 8)]
        cover_string = 0

        for i in range(len(search_array)):
            n = search_array[i]
            neighbor_key = (x + n[0], y + n[1])
            nx, ny = neighbor_key
            if 0 <= nx < self.environment.max_x:
                if 0 <= ny < self.environment.max_y:
                    neighbor_tile = self.environment.pathfinder.graph[neighbor_key]
                    if neighbor_tile.cover:
                        cover_string += n[2]

        return cover_string

    def draw_path(self):
        self.clear_movement_icons()

        # selected = self.environment.agents[self.active_agent]
        # origin = selected.get_position()
        # origin_position = mathutils.Vector(origin).to_3d()
        # highlight = self.environment.add_object("highlight")
        # highlight.worldPosition = origin_position
        # highlight.color = movement_color
        # self.movement_icons.append(highlight)

        path = self.environment.pathfinder.current_path
        length = len(path)

        movement_cost = self.environment.pathfinder.movement_cost
        within_range = movement_cost <= self.max_actions

        if path and within_range:
            self.path = path[1:]

            for i in range(1, length):

                if i <= length:
                    current_node = path[i]
                    last_node = path[i - 1]
                    cover = -1

                    if i == length - 1:
                        marker_type = "movement_{}".format(int(movement_cost))
                        cover = self.get_cover_icon(current_node)
                    else:
                        marker_type = "movement_0"

                    last = mathutils.Vector(last_node).to_3d()
                    current = mathutils.Vector(current_node).to_3d()

                    if cover >= 0:
                        cover_string = "map_cover_icon.{}".format(str(cover).zfill(3))
                        cover_icon = self.environment.add_object(cover_string)
                        cover_icon.color = movement_color
                        cover_icon.worldPosition = current
                        self.movement_icons.append(cover_icon)

                    target_vector = current - last
                    marker = self.environment.add_object(marker_type)
                    marker.color = movement_color
                    if marker_type == "movement_0":
                        marker.localScale.y = target_vector.length

                    track = target_vector.to_track_quat("Y", "Z").to_matrix().to_3x3()
                    marker.worldPosition = last
                    marker.worldOrientation = track

                    self.movement_icons.append(marker)

        else:
            self.path = []

    def find_path(self):
        if not self.environment.pathfinder.flooded:
            selected = self.environment.agents[self.active_agent]
            origin = selected.get_position()

            movement_cost = selected.get_movement_cost()
            if movement_cost:
                on_road_cost, off_road_cost = movement_cost
            else:
                on_road_cost, off_road_cost = 100.0, 100.0

            self.environment.pathfinder.generate_paths(origin, on_road_cost, off_road_cost)
            self.environment.update_map()

        self.environment.pathfinder.find_path(self.environment.tile_over)

    def process(self):

        if "space" in self.environment.input_manager.keys:
            self.finished = True

        if self.busy:
            self.set_canvas("INACTIVE")
            self.clear_movement_icons()
        else:
            if self.active_agent:
                current_agent = self.environment.agents[self.active_agent]
                immobile = current_agent.check_immobile()
                self.max_actions = current_agent.get_stat("free_actions")

                self.check_input()
                current_action = current_agent.get_current_action()
                if current_action["target"] == "MOVE":
                    if immobile or current_action["effect"] == "ROTATE":
                        self.max_actions = 0
                        self.set_canvas("INACTIVE")
                    else:
                        self.set_canvas("MOVE")
                    self.find_path()
                    self.process_path()
                elif current_action["target"] == "BUILDING":
                    if immobile:
                        self.set_canvas("INACTIVE")
                    else:
                        self.set_canvas("FRIEND")
                    self.max_actions = 0
                    self.find_path()
                    self.process_path()
                elif current_action["target"] == "AIRCRAFT":
                    self.max_actions = 0
                    self.set_canvas("INACTIVE")
                    self.find_path()
                    self.process_path()
                elif current_action["target"] == "ALLIES":
                    self.max_actions = 0
                    self.set_canvas("INACTIVE")
                    self.find_path()
                    self.process_path()
                elif current_action["target"] == "FRIEND":
                    self.max_actions = 0
                    self.set_canvas("FRIEND")
                    self.find_path()
                    self.process_path()
                elif current_action["target"] == "MAP":
                    self.max_actions = 0
                    self.set_canvas("INACTIVE")
                    self.find_path()
                    self.process_path()
                else:
                    self.max_actions = 0
                    self.set_canvas("SHOOTING")
                    self.find_path()
                    self.process_path()
            else:
                self.set_canvas("INACTIVE")

        self.environment.debug_text = "{} {}".format(self.active_agent, self.busy)

    def reset_ui(self):
        self.environment.switch_ui("PLAYER")
        self.environment.update_map()

    def check_input(self):

        if not self.environment.ui.focus and not self.busy:
            mouse_over_tile = self.environment.get_tile(self.environment.tile_over)

            if "left_button" in self.environment.input_manager.buttons and self.active_agent:
                active_agent = self.environment.agents[self.active_agent]
                current_action = active_agent.active_action

                action_trigger = active_agent.trigger_action(current_action, self.environment.tile_over)

                if not action_trigger:
                    active_agent.set_starting_action()

                self.reset_ui()

            if "right_button" in self.environment.input_manager.buttons:
                target = mouse_over_tile["occupied"]
                if target:
                    target_agent = self.environment.agents[target]
                    valid_selection = target_agent.check_valid_selection()

                    if valid_selection:
                        self.active_agent = target
                        self.reset_ui()
                        self.update_pathfinder()

            if "escape" in self.environment.input_manager.keys:
                active_agent = self.environment.agents[self.active_agent]
                active_agent.set_starting_action()
                self.reset_ui()


class EnemyTurn(TurnManager):

    def __init__(self, environment):
        super().__init__(environment)
        self.team = 2
        self.timer = 0
        self.max_actions = 0
        self.set_canvas("INACTIVE")
        self.viewing_agent = None
        self.ai_state = None
        self.end_turn_allowed = True

    def reset_ui(self):
        pass

    def prep_pathfinder(self):
        selected = self.environment.agents[self.active_agent]
        origin = selected.get_position()

        movement_cost = selected.get_movement_cost()
        if movement_cost:
            on_road_cost, off_road_cost = movement_cost

            self.environment.pathfinder.generate_paths(origin, on_road_cost, off_road_cost)
            self.environment.update_map()

    def process(self):

        behavior_types = ["ATTACK",
                          "DEFEND",
                          "HOLD",
                          "GO_TO",
                          "SCOUT",
                          "SUPPORT",
                          "ARTILLERY",
                          "AMBUSH",
                          "AIR_SUPPORT",
                          "SUPPLY",
                          "JAMMER",
                          "ANTI_AIR",
                          "CLEAR_MINES",
                          "ADVANCE",
                          "AGGRESSIVE",
                          "FLANKING"]

        remaining_behavior_types = []

        extra_variables = ["STAY_PRONE",
                           "STAY_BUTTONED_UP",
                           "VETERANS",
                           "RAW_RECRUITS"]

        if self.active_agent:
            agent = self.environment.agents[self.active_agent]

            if agent.check_visible():
                if self.viewing_agent != self.active_agent:
                    self.viewing_agent = self.active_agent
                    position = agent.get_stat("position")
                    self.environment.camera_control.camera_action(position)

            if not self.ai_state:
                agent_behavior = agent.get_behavior()

                behavior_dict = {"GO_TO": "GoTo",
                                 "ATTACK": "Attack",
                                 "ADVANCE": "Advance",
                                 "AGGRESSIVE": "Aggressive",
                                 "ARTILLERY": "Artillery",
                                 "AMBUSH": "Ambush",
                                 "ANTI_AIR": "AntiAir",
                                 "DEFEND": "Defend",
                                 "SUPPORT": "Support",
                                 "SCOUT": "Scout",
                                 "SUPPLY": "Supply",
                                 "JAMMER": "Jammer",
                                 "FLANKING": "Flanking",
                                 "AIR_SUPPORT": "AirSupport",
                                 "CLEAR_MINES": "ClearMines",
                                 "RETREATING": "Retreating",
                                 "HOLD": "Hold"}

                if agent_behavior in behavior_dict:
                    behavior_class = behavior_dict[agent_behavior]
                    self.ai_state = globals()[behavior_class](self.environment, self, self.active_agent)

                else:
                    self.ai_state = Hold(self.environment, self, self.active_agent)

                self.update_pathfinder()
                self.prep_pathfinder()
            else:
                if not self.busy:
                    # find a cheaper_way
                    self.ai_state.update()
                    if self.ai_state.finished:
                        self.ai_state.terminate()
                        self.active_agent = None
                        self.ai_state = None
