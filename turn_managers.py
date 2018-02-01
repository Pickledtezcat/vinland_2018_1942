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

        for i in range(length):
            if i < length - 1:
                next_node = path[i + 1]
                current_node = path[i]

                next_tile = self.pathfinder.graph[next_node]
                if next_tile.off_road:
                    self.moved += off_road_cost
                else:
                    self.moved += on_road_cost

                if self.moved >= 1.0:
                    self.moved -= 1.0
                    self.action_cost += 1
                    marker_type = "movement_end"
                else:
                    if self.action_cost >= max_actions:
                        action_exceeded = True
                    marker_type = "movement_middle"

                if i == length - 2:
                    marker_type = "movement_end"

                target = mathutils.Vector(next_node).to_3d()
                current = mathutils.Vector(current_node).to_3d()

                target_vector = target - current
                marker = self.environment.add_object(marker_type)
                if marker_type == "movement_middle":
                    marker.localScale.y = target_vector.length

                track = target_vector.to_track_quat("Y", "Z").to_matrix().to_3x3()
                marker.worldPosition = current
                marker.worldOrientation = track

                if action_exceeded:
                    marker.color = [1.0, 0.0, 0.0, 1.0]

                self.movement_icons.append(marker)

            if i == length - 1:
                current_node = path[i]
                current = mathutils.Vector(current_node).to_3d()
                end_marker = self.environment.add_object("target")
                end_marker.worldPosition = current
                if action_exceeded:
                    end_marker.color = [1.0, 0.0, 0.0, 1.0]

                self.movement_icons.append(end_marker)

            if i <= length - 1:
                current_node = path[i]
                if self.action_cost <= max_actions:
                    self.path.append(current_node)

    def process(self):

        if self.active_agent:
            current_agent = self.environment.agents[self.active_agent]

            if not current_agent.busy:
                if self.pulse():
                    self.find_path()
                    self.process_path()

                self.check_input()
            else:
                self.clear_movement_icons()

    def check_input(self):

        if not self.environment.ui.focus:
            if "left_button" in self.environment.input_manager.buttons:
                position = self.environment.tile_over

                for agent in self.valid_agents:
                    if self.environment.agents[agent].get_position() == position:
                        self.active_agent = agent
            if self.active_agent:
                if "right_button" in self.environment.input_manager.buttons:
                    if self.path:
                        message = {"agent_id": self.active_agent, "header": "FOLLOW_PATH",
                                   "contents": [self.path, self.action_cost]}

                        self.environment.message_list.append(message)

    def pulse(self):
        if self.timer >= 12:
            self.timer = 0
            return True
        else:
            self.timer += 1

        return False

    def find_path(self):
        selected = self.environment.agents[self.active_agent]
        origin = selected.get_position()
        target = self.environment.tile_over
        infantry = False

        movement_cost = selected.get_movement_cost()
        if movement_cost:
            on_road_cost, off_road_cost = movement_cost
            self.pathfinder.generate_path(origin, target, on_road_cost, off_road_cost, infantry)

        else:
            return []

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
