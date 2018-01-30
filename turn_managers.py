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

    def set_movement_icons(self):
        self.clear_movement_icons()

        selected = self.environment.agents[self.active_agent]

        if self.active_agent:
            origin = selected.get_position()
            origin_position = mathutils.Vector(origin).to_3d()
            hightlight = self.environment.add_object("highlight")
            hightlight.worldPosition = origin_position
            self.movement_icons.append(hightlight)

            path = self.pathfinder.current_path

            for tile in path:
                marker = self.environment.add_object("highlight")
                marker.worldPosition = mathutils.Vector(tile).to_3d()
                self.movement_icons.append(marker)

    def process(self):

        self.check_select()

        if self.pulse():
            self.find_path()
            self.set_movement_icons()

    def check_select(self):

        if not self.environment.ui.focus:
            if "left_button" in self.environment.input_manager.buttons:
                position = self.environment.tile_over
                for agent in self.valid_agents:
                    if self.environment.agents[agent].get_position() == position:
                        self.active_agent = agent

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
            self.pathfinder.generate_path(origin, target, infantry, on_road_cost, off_road_cost)

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
