import bge
import bgeutils
import mathutils


class TurnManager(object):
    turn_type = "PROTOTYPE"

    def __init__(self, environment):

        self.team = -1
        self.environment = environment
        self.finished = False
        self.active_agent = None
        self.last_active_agent = None
        self.valid_agents = []
        self.movement_icons = []
        self.turn_id = 0
        self.tile_over = None
        self.started = False
        self.busy = False
        self.busy_count = 0
        self.end_count = 0

        self.check_valid_units()
        self.canvas_type = "BLANK"

    def set_canvas(self, canvas_type):
        if self.canvas_type != canvas_type:
            self.environment.terrain_canvas.set_update(canvas_type)
            self.canvas_type = canvas_type

    def check_valid_units(self):
        team_units = []
        busy = False

        for agent_key in self.environment.agents:
            agent = self.environment.agents[agent_key]
            if agent.get_stat("team") == self.team:
                if agent.busy:
                    busy = True

                active_agent = not agent.has_effect("BAILED_OUT")
                free_actions = agent.get_stat("free_actions") > 0
                unloaded = not agent.has_effect("LOADED")
                alive = not agent.has_effect("DYING")

                if active_agent and free_actions and unloaded and alive:
                    # TODO add more checks for validity of agents, actions remaining etc...
                    team_units.append(agent_key)

        if not team_units:
            self.active_agent = None
        else:
            if not self.active_agent:
                self.active_agent = team_units[0]

        self.valid_agents = team_units

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
            self.environment.pathfinder.update_graph()
            self.environment.update_map()

        if self.end_check():
            self.finished = True
        else:
            self.process()

    def process(self):
        pass

    def end_check(self):
        self.check_valid_units()
        if not self.valid_agents:
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

    def refresh_units(self):
        for agent_key in self.environment.agents:
            agent = self.environment.agents[agent_key]
            if agent.get_stat("team") != self.team:
                agent.regenerate()

    def get_target_data(self, origin_id, target_id, action_id, tile_over):

        origin_agent = self.environment.agents[origin_id]
        target_agent = None

        if target_id:
            target_agent = self.environment.agents[target_id]

        current_action = origin_agent.get_stat("action_dict")[action_id]
        origin = origin_agent.get_stat("position")

        if current_action["action_type"] != "WEAPON":
            target_data = {"target_type": "INVALID"}
            return target_data

        weapon = current_action["weapon_stats"]
        accuracy = weapon["accuracy"]
        ammo_modifier = 1
        if origin_agent.has_effect("SPECIAL_AMMO"):
            ammo_modifier = 2

        penetration = weapon["penetration"] * ammo_modifier
        damage = weapon["damage"] * ammo_modifier
        shock = weapon["shock"] * ammo_modifier

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
                explosion_reduction = int(round(distance * 0.333))

                # TODO add modifiers for movement and size
                accuracy -= explosion_reduction

                if origin_agent.has_effect("MOVED"):
                    accuracy -= 2

                if not origin_agent.has_effect("BUTTONED_UP"):
                    accuracy += 2

                if origin_agent.has_effect("STEADY_AIM"):
                    accuracy += 4

                base_target = accuracy

                target_data = {"target_type": "EXPLOSION", "contents": [damage, shock, base_target, penetration,
                                                                        explosion_reduction]}
                return target_data

        else:
            if not target_agent:
                target_data = {"target_type": "INVALID"}
                return target_data

            else:
                if origin_agent.has_effect("MOVED"):
                    accuracy -= 2

                if not origin_agent.has_effect("BUTTONED_UP"):
                    accuracy += 2

                if origin_agent.has_effect("STEADY_AIM"):
                    accuracy += 4

                # get target_info
                facing = target_agent.get_stat("facing")
                location = target_agent.get_stat("position")

                flanked, covered, reduction = self.check_cover(origin, facing, location)

                if target_agent.agent_type == "INFANTRY":
                    base_target = target_agent.get_stat("number") + 1
                else:
                    base_target = target_agent.get_stat("size")

                if target_agent.check_immobile():
                    base_target += 1

                if target_agent.has_effect("PRONE"):
                    base_target -= 1

                if target_agent.has_effect("MOVED"):
                    base_target -= 1
                if target_agent.has_effect("FAST"):
                    base_target -= 1

                if target_agent.has_effect("MARKED"):
                    base_target += 2

                if covered:
                    base_target -= 2

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

                elif flanked:
                    damage = int(damage * 1.5)
                    shock = int(shock * 1.5)
                    armor_value = armor[1]

                if armor_value == 0:
                    armor_target = 7
                else:
                    penetration -= reduction
                    armor_target = max(0, penetration - armor_value)

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
        self.refresh_units()
        self.environment.cycle_effects(self.team)
        self.clear_movement_icons()


movement_color = [0.69, 0.92, 0.95, 1.0]


class PlayerTurn(TurnManager):

    def __init__(self, environment):
        super().__init__(environment)
        self.team = 1
        self.timer = 0

        self.path = None
        self.max_actions = 0
        self.moved = 0.0

    def process_path(self):

        selected = self.environment.agents[self.active_agent]
        new_path = self.environment.pathfinder.current_path

        self.clear_movement_icons()

        if self.active_agent:
            origin = selected.get_position()
            origin_position = mathutils.Vector(origin).to_3d()
            highlight = self.environment.add_object("highlight")
            highlight.worldPosition = origin_position
            highlight.color = movement_color
            self.movement_icons.append(highlight)
            if new_path:
                self.draw_path()

    def draw_path(self):
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

                    if i == length - 1:
                        marker_type = "movement_{}".format(int(movement_cost))
                    else:
                        marker_type = "movement_0"

                    last = mathutils.Vector(last_node).to_3d()
                    current = mathutils.Vector(current_node).to_3d()

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

                self.environment.pathfinder.generate_paths(origin, on_road_cost, off_road_cost)
                self.environment.update_map()

        self.environment.pathfinder.find_path(self.environment.tile_over)

    def process(self):

        if "space" in self.environment.input_manager.keys:
            self.finished = True

        # if self.active_agent != self.last_active_agent:
        #     self.last_active_agent = self.active_agent
        #
        #     self.environment.update_map()
        #     self.find_path()
        #     self.process_path()

        current_agent = None

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

    def check_input(self):

        if not self.environment.ui.focus and not self.busy:
            mouse_over_tile = self.environment.get_tile(self.environment.tile_over)

            if "left_button" in self.environment.input_manager.buttons and self.active_agent:
                active_agent = self.environment.agents[self.active_agent]
                action_trigger = active_agent.trigger_current_action()

                if action_trigger:
                    self.reset_ui()

            if "right_button" in self.environment.input_manager.buttons:
                target = mouse_over_tile["occupied"]
                if target:
                    target_agent = self.environment.agents[target]
                    team_mate = target_agent.get_stat("team") == self.team
                    active_target = not target_agent.has_effect("BAILED_OUT")
                    unloaded_target = not target_agent.has_effect("LOADED")

                    if active_target and unloaded_target and team_mate:
                        self.active_agent = target
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

    def process(self):

        if self.active_agent:

            active_agent = self.environment.agents[self.active_agent]

            if active_agent.get_stat("free_actions") == 0:
                self.active_agent = None
            elif not active_agent.busy:
                position = active_agent.get_stat("position")
                closest = 10000.0
                target_position = None

                for agent_key in self.environment.agents:
                    other_agent = self.environment.agents[agent_key]
                    if other_agent.get_stat("team") == 1:
                        other_position = other_agent.get_stat("position")
                        target_vector = mathutils.Vector(other_position) - mathutils.Vector(position)
                        distance = target_vector.length

                        if distance < closest:
                            closest = distance
                            target_position = other_position

                if target_position:
                    active_agent.active_action = active_agent.get_action_key("FACE_TARGET")
                    action_trigger = active_agent.trigger_current_action(target_position)
                    active_agent.set_stat("free_actions", 0)
                else:
                    active_agent.set_stat("free_actions", 0)

        # if self.timer > 12:
        #     self.finished = True
        # else:
        #     self.timer += 1
