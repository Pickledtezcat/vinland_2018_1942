import bge
import bgeutils
import mathutils
import pathfinding


class TurnManager(object):

    turn_type = "PROTOTYPE"

    def __init__(self, environment):

        self.team = 1
        self.environment = environment
        self.finished = False
        self.active_agent = None
        self.valid_agents = []

    def check_valid_units(self):
        team_units = []
        for agent_key in self.environment.agents:
            if self.environment.agents[agent_key].stats["team"] == self.team:
                # TODO add more checks for validity of agents, actions remaining etc...
                team_units.append(agent_key)
            else:
                print(self.environment.agents[agent_key].stats["team"], self.team)

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


class PlayerTurn(TurnManager):

    def __init__(self, environment):
        self.turn_type = "PLAYER"
        super().__init__(environment)
        self.team = 1
        self.timer = 0

        self.movement_icons = []
        self.pathfinder = pathfinding.Pathfinder(environment)
        self.path = None
        self.action_cost = 0
        self.moved = 0.0

    def process_path(self):
        self.clear_movement_icons()

        selected = self.environment.agents[self.active_agent]

        if self.active_agent:
            origin = selected.get_position()
            origin_position = mathutils.Vector(origin).to_3d()
            highlight = self.environment.add_object("highlight")
            highlight.worldPosition = origin_position
            self.movement_icons.append(highlight)

            self.draw_path()

    def draw_path(self):
        path = self.pathfinder.current_path
        length = len(path)

        selected = self.environment.agents[self.active_agent]
        movement_cost = selected.get_movement_cost()
        on_road_cost, off_road_cost = movement_cost

        max_actions = 3
        self.moved = 0.0
        self.action_cost = 0
        action_exceeded = False

        self.path = []

        for i in range(1, length):

            if i <= length:
                current_node = path[i]
                last_node = path[i - 1]

                if self.action_cost < max_actions:
                    self.path.append(current_node)
                else:
                    action_exceeded = True

                current_tile = self.pathfinder.graph[current_node]
                if current_tile.off_road:
                    cost = off_road_cost
                else:
                    cost = on_road_cost

                self.moved += cost

                if self.moved >= 1.0:
                    self.moved -= 1.0
                    self.action_cost += 1

                    marker_type = "movement_end"
                else:
                    marker_type = "movement_middle"

                if i == length - 1:
                    marker_type = "movement_end"

                last = mathutils.Vector(last_node).to_3d()
                current = mathutils.Vector(current_node).to_3d()

                target_vector = current - last
                marker = self.environment.add_object(marker_type)
                if marker_type == "movement_middle":
                    marker.localScale.y = target_vector.length

                track = target_vector.to_track_quat("Y", "Z").to_matrix().to_3x3()
                marker.worldPosition = last
                marker.worldOrientation = track

                if action_exceeded:
                    marker.color = [1.0, 0.0, 0.0, 1.0]

                self.movement_icons.append(marker)

                if i == length - 1:
                    end_marker = self.environment.add_object("target")
                    end_marker.worldPosition = current
                    if action_exceeded:
                        end_marker.color = [1.0, 0.0, 0.0, 1.0]
                    self.movement_icons.append(end_marker)

        self.environment.debug_text = "{} / {}".format(self.environment.tile_over, self.pathfinder.current_path[:1])

    def process(self):

        if self.active_agent:
            current_agent = self.environment.agents[self.active_agent]

            if not current_agent.busy:
                if self.pulse():
                    self.find_path()
                    self.process_path()
                    self.debug_movement()

                self.check_input()
            else:
                self.clear_movement_icons()

    def check_input(self):

        if not self.environment.ui.focus:
            if "left_button" in self.environment.input_manager.buttons:
                mouse_over_tile = self.environment.get_tile(self.environment.tile_over)
                occupier = mouse_over_tile["occupied"]
                if occupier:
                    if self.environment.agents[occupier].stats["team"] == self.team:
                        self.active_agent = occupier
                        self.pathfinder.update_map()

            if self.active_agent:
                if "right_button" in self.environment.input_manager.buttons:
                    if self.path:
                        message = {"agent_id": self.active_agent, "header": "FOLLOW_PATH",
                                   "contents": [self.path, self.action_cost]}

                        self.environment.message_list.append(message)

    def debug_movement(self):

        for tile_key in self.pathfinder.graph:
            tile = self.pathfinder.graph[tile_key]
            if tile.parent and tile.g < 4:
                position = mathutils.Vector(tile_key).to_3d()
                tag = self.environment.add_object("tile_tag")
                tag.worldPosition = position
                tag.children[0]["Text"] = max(1, int(tile.g))
                self.movement_icons.append(tag)

    def pulse(self):
        if self.timer >= 4:
            self.timer = 0
            return True
        else:
            self.timer += 1

        return False

    def find_path(self):
        if not self.pathfinder.flooded:

            selected = self.environment.agents[self.active_agent]
            origin = selected.get_position()
            infantry = False

            movement_cost = selected.get_movement_cost()
            if movement_cost:
                on_road_cost, off_road_cost = movement_cost

                self.pathfinder.generate_paths(origin, on_road_cost, off_road_cost, infantry)

        self.pathfinder.find_path(self.environment.tile_over)

    def clear_movement_icons(self):
        for icon in self.movement_icons:
            icon.endObject()
        self.movement_icons = []


class EnemyTurn(TurnManager):

    def __init__(self, environment):
        self.turn_type = "ENEMY"
        super().__init__(environment)
        self.team = 2

    def process(self):
        pass
