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

                if agent.get_stat("free_actions") > 0 and not agent.has_effect("LOADED"):

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
            if not self.busy:
                return True

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

    def end(self):
        self.refresh_units()
        self.environment.cycle_effects()
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
                    if immobile:
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
                elif current_action["target"] == "FRIEND":
                    self.max_actions = 0
                    self.set_canvas("FRIEND")
                    self.find_path()
                    self.process_path()
                elif current_action["target"] == "MAP":
                    self.set_canvas("INACTIVE")
                    self.max_actions = 0
                    self.find_path()
                    self.process_path()
                else:
                    self.set_canvas("SHOOTING")
                    self.max_actions = 0
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
                occupier = mouse_over_tile["occupied"]
                if occupier:
                    if self.environment.agents[occupier].get_stat("team") == self.team:
                        self.active_agent = occupier
                        self.update_pathfinder()


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
            print(self.active_agent)

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
                    print(active_agent.active_action, "ACTIVE_ACTION")
                    action_trigger = active_agent.trigger_current_action(target_position)
                    print(action_trigger, "TRIGGERED")
                    active_agent.set_stat("free_actions", 0)
                else:
                    active_agent.set_stat("free_actions", 0)


        # if self.timer > 12:
        #     self.finished = True
        # else:
        #     self.timer += 1
