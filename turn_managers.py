import bge
import bgeutils
import mathutils


class TurnManager(object):
    turn_type = "PROTOTYPE"

    def __init__(self, environment):

        self.team = 1
        self.environment = environment
        self.finished = False
        self.active_agent = None
        self.valid_agents = []
        self.movement_icons = []
        self.turn_id = 0

    def check_valid_units(self):
        team_units = []
        for agent_key in self.environment.agents:
            if self.environment.agents[agent_key].get_stat("team") == self.team:
                # TODO add more checks for validity of agents, actions remaining etc...
                team_units.append(agent_key)

        if not team_units:
            self.active_agent = None
        else:
            if self.active_agent:
                pass
            else:
                self.active_agent = team_units[0]

        self.valid_agents = team_units

    def update(self):
        self.process()

        if self.end_check():
            self.finished = True

    def process(self):
        pass

    def end_check(self):
        self.check_valid_units()
        if not self.valid_agents:
            return True

        return False

    def clear_movement_icons(self):
        for icon in self.movement_icons:
            icon.endObject()
        self.movement_icons = []

    def end(self):
        self.clear_movement_icons()


movement_color = [0.69, 0.92, 0.95, 1.0]


class PlayerTurn(TurnManager):

    def __init__(self, environment):
        self.turn_type = "PLAYER"
        super().__init__(environment)
        self.team = 1
        self.timer = 0

        self.path = None
        self.max_actions = 0
        self.moved = 0.0

    def process_path(self):
        self.clear_movement_icons()

        selected = self.environment.agents[self.active_agent]

        if self.active_agent:
            origin = selected.get_position()
            origin_position = mathutils.Vector(origin).to_3d()
            highlight = self.environment.add_object("highlight")
            highlight.worldPosition = origin_position
            highlight.color = movement_color
            self.movement_icons.append(highlight)

            if self.environment.pathfinder.current_path:
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

        self.environment.debug_text = "{} / {} / {}".format(self.environment.tile_over, movement_cost, length - 1)

    def process(self):

        if "save" in self.environment.input_manager.keys:
            for agent_key in self.environment.agents:
                agent = self.environment.agents[agent_key]
                agent.set_stat("free_actions", 3)

            self.environment.pathfinder.update_graph()
            self.environment.update_map()

        if self.active_agent:
            current_agent = self.environment.agents[self.active_agent]
            self.max_actions = current_agent.get_stat("free_actions")

            if not current_agent.busy:
                if self.pulse():
                    self.find_path()
                    self.process_path()

                self.check_input()
            else:
                self.clear_movement_icons()

    def check_input(self):

        if not self.environment.ui.focus:
            mouse_over_tile = self.environment.get_tile(self.environment.tile_over)
            occupier = mouse_over_tile["occupied"]
            message = None

            if "left_button" in self.environment.input_manager.buttons and self.active_agent:
                if "control" in self.environment.input_manager.keys:
                    message = {"agent_id": self.active_agent, "header": "TARGET_LOCATION",
                               "contents": [self.environment.tile_over]}

                elif occupier:
                    if self.environment.agents[occupier].get_stat("team") == self.team:
                        self.active_agent = occupier
                        self.environment.pathfinder.update_graph()

                else:
                    if self.path:
                        action_cost = self.environment.pathfinder.movement_cost

                        message = {"agent_id": self.active_agent, "header": "FOLLOW_PATH",
                                   "contents": [self.path, action_cost]}

            if message:
                self.environment.message_list.append(message)

    def debug_movement(self):

        for tile_key in self.environment.pathfinder.graph:
            tile = self.environment.pathfinder.graph[tile_key]
            if tile.parent and int(tile.g * 10) <= self.max_actions * 10:
                position = mathutils.Vector(tile_key).to_3d()
                tag = self.environment.add_object("tile_tag")
                tag.worldPosition = position
                tag.children[0]["Text"] = int(tile.g * 10)
                self.movement_icons.append(tag)

    def pulse(self):
        if self.timer >= 4:
            self.timer = 0
            return True
        else:
            self.timer += 1

        return False

    def find_path(self):

        if not self.environment.pathfinder.flooded:

            selected = self.environment.agents[self.active_agent]
            origin = selected.get_position()
            infantry = False

            movement_cost = selected.get_movement_cost()
            if movement_cost:
                on_road_cost, off_road_cost = movement_cost

                self.environment.pathfinder.generate_paths(origin, on_road_cost, off_road_cost, infantry)
                self.environment.update_map()

        self.environment.pathfinder.find_path(self.environment.tile_over)


class EnemyTurn(TurnManager):

    def __init__(self, environment):
        self.turn_type = "ENEMY"
        super().__init__(environment)
        self.team = 2

    def process(self):
        pass
