import bge
import game_input
import ui_modules
import camera_controller
import random
import bgeutils
import mathutils
import agents
import turn_managers
import shadow_casting
import canvas
import pathfinding
import static_dicts


class Environment(object):

    def __init__(self, main_loop):
        self.environment_type = "DEFAULT"
        self.ready = False
        self.main_loop = main_loop
        self.game_object = self.main_loop.cont.owner
        self.listener = self.game_object
        self.scene = self.game_object.scene
        self.input_manager = game_input.GameInput()
        self.camera_control = camera_controller.CameraController(self)
        self.debug_text = ""

        self.assets = []
        self.level_map = {}
        self.tiles = {}
        self.id_index = 0
        self.agents = {}
        self.ui = None
        self.tile_over = None
        self.turn_manager = None

        self.max_x = 32
        self.max_y = 32

        self.terrain_canvas = None
        self.visibility = None
        self.pathfinder = None

        self.audio = None

        self.weapons_dict = static_dicts.get_weapon_stats()
        self.vehicle_dict = static_dicts.get_vehicle_stats()
        self.action_dict = static_dicts.get_action_stats()

    def get_new_id(self):
        self.id_index += 1
        got_id = self.id_index
        return got_id

    def update(self):
        if not self.main_loop.shutting_down:
            if self.ready:
                self.mouse_over_map()
                self.process()
            else:
                self.prep()

    def process(self):
        pass

    def add_object(self, object_name):
        new_object = self.scene.addObject(object_name, self.game_object, 0)
        return new_object

    def save_level(self):

        preserved_list = []

        for agent_key in self.agents:
            saving_agent = self.agents[agent_key]
            agent_stats = saving_agent.save_to_dict()
            preserved_list.append(agent_stats)

        level = {"level_map": self.level_map, 'id_index': self.id_index,
                 "agents": preserved_list}

        bgeutils.save_level(level)

    def load_level(self):

        # to clear map
        # return False

        loaded_level = bgeutils.load_level()
        if loaded_level:
            self.level_map = loaded_level["level_map"]
            self.id_index = loaded_level["id_index"]

            for loading_agent in loaded_level["agents"]:
                self.load_agent(loading_agent)

            return True

        else:
            return False

    def set_tile(self, position, key_type, setting):

        error = None

        under = position[0] < self.max_x and position[1] < self.max_y
        over = position[0] >= 0 and position[1] >= 0

        if under and over:
            tile_key = bgeutils.get_key(position)
            try:
                self.level_map[tile_key][key_type] = setting
            except:
                error = "SETTING_ERROR"

        else:
            error = "TILE_ERROR"

        if error:
            print("{}/ unable to set map/ {} tile/ {} key/ {} setting".format(error, position, key_type, setting))

    def get_tile(self, position):

        under = position[0] < self.max_x and position[1] < self.max_y
        over = position[0] >= 0 and position[1] >= 0

        if under and over:
            tile_key = bgeutils.get_key(position)
            return self.level_map[tile_key]

        else:
            error = "TILE_ERROR"

        if error:
            print("{}/ unable to get map/ {} tile".format(error, position))

    def mouse_over_map(self):
        mouse_hit = self.mouse_ray(self.input_manager.virtual_mouse)

        if mouse_hit[0]:
            self.tile_over = bgeutils.position_to_location(mouse_hit[1])
        else:
            self.tile_over = [0, 0]

    def switch_modes(self, mode):

        valid_modes = ["GAMEPLAY", "EDITOR", "PLACER"]

        if mode in valid_modes:
            self.save_level()
            self.main_loop.switching_mode = mode

        else:
            if mode == "EXIT":
                self.save_level()
                self.main_loop.shutting_down = True

    def prep(self):
        if not self.assets:
            asset_path = bge.logic.expandPath("//resources/models/test_content.blend")
            test_assets = bge.logic.LibLoad(asset_path, "Scene", async=True)
            self.assets.append(test_assets)

        else:
            finished = True
            for asset in self.assets:
                if not asset.finished:
                    finished = False
            if finished:
                self.loaded()

    def generate_map(self):
        for x in range(0, 32):
            for y in range(0, 32):
                tile_type = 2
                tile_key = bgeutils.get_key([x, y])

                tile_dict = {"softness": tile_type,
                             "wall": False,
                             "trees": False,
                             "bushes": False,
                             "bridge": False,
                             "rocks": False,
                             "water": False,
                             "road": False,
                             "heights": False,
                             "occupied": None,
                             "visual": random.randint(0, 8)}

                self.level_map[tile_key] = tile_dict

    def draw_map(self):

        self.create_blank_tiles()
        for tile_key in self.level_map:
            location = bgeutils.get_loc(tile_key)
            self.draw_tile(location)

    def load_agent(self, load_dict, position=None, team=1, load_key=None):
        infantry = ["rm", "st",
                    "mg", "at", "en", "cm"]

        vehicles = ["scout car", "medium tank", "light tank",
                    "truck", "assault gun"]

        artillery = ["artillery", "anti tank gun"]

        agents.Agent(self, position, team, load_key, load_dict)

    def create_blank_tiles(self):
        for x in range(0, 32):
            for y in range(0, 32):
                tile_key = bgeutils.get_key([x, y])
                self.tiles[tile_key] = []

    def load_ui(self):
        self.ui = ui_modules.EditorInterface(self)

    def initiate_visibility(self):
        self.terrain_canvas = canvas.TerrainCanvas(self)
        self.terrain_canvas.fill_all()

    def loaded(self):

        if not self.load_level():
            self.generate_map()

        self.draw_map()

        self.initiate_visibility()

        self.load_ui()
        self.ready = True

    def draw_tile(self, location):
        location = [max(0, min(31, location[0])), max(0, min(31, location[1]))]

        tile_key = bgeutils.get_key(location)

        existing_tiles = self.tiles[tile_key]
        if existing_tiles:
            for tile in existing_tiles:
                tile.endObject()
            self.tiles[tile_key] = []

        if self.level_map[tile_key]["water"]:
            tile_string = "water"
            z_pos = -0.5
        else:
            ground_type = self.level_map[tile_key]["softness"]
            tile_string = "ground_{}".format(ground_type)
            if self.level_map[tile_key]["heights"]:
                z_pos = 0.5
            else:
                z_pos = 0.0

        tile = self.add_object(tile_string)
        tile.worldPosition = mathutils.Vector(location).to_3d()
        tile.worldPosition.z = z_pos
        self.tiles[tile_key].append(tile)

        features = ["trees", "bushes", "bridge", "rocks", "road"]

        if self.level_map[tile_key]["wall"]:
            self.draw_wall(location, tile_key)

        for feature in features:
            if self.level_map[tile_key][feature]:
                feature_tile = self.add_object(feature)
                feature_tile.worldPosition = mathutils.Vector(location).to_3d()
                feature_tile.worldPosition.z = z_pos
                self.tiles[tile_key].append(feature_tile)

    def draw_wall(self, location, tile_key):

        x, y = location

        search_array = [(-1, 0, 1), (0, -1, 2), (1, 0, 4), (0, 1, 8)]
        wall = 0

        for i in range(len(search_array)):
            n = search_array[i]
            n_key = bgeutils.get_key([x + n[0], y + n[1]])
            n_tile = self.level_map.get(n_key)

            if n_tile:
                if n_tile["wall"]:
                    wall += n[2]

        wall_mesh = "wall_{}".format(wall)
        wall_tile = self.add_object(wall_mesh)
        wall_tile.worldPosition = mathutils.Vector(location).to_3d()
        self.tiles[tile_key].append(wall_tile)

    def mouse_ray(self, position):
        x, y = position

        camera = self.scene.active_camera
        screen_vect = camera.getScreenVect(x, y)
        target_position = camera.worldPosition.copy() - screen_vect
        mouse_hit = camera.rayCast(target_position, camera, 500.0, "ground", 0, 1, 0)

        return mouse_hit

    def end(self):
        # add code to remove textures, shut down units and free lib loaded stuff

        if self.terrain_canvas:
            self.terrain_canvas.terminate()

        if self.ui:
            self.ui.end()
            self.ui = None

        for tile_key in self.tiles:
            existing_tiles = self.tiles[tile_key]
            if existing_tiles:
                for tile in existing_tiles:
                    tile.endObject()
                self.tiles[tile_key] = []

        if self.turn_manager:
            self.turn_manager.end()

        # TODO free assets

        self.assets = None

        for library in bge.logic.LibList():
            bge.logic.LibFree(library)


terrain_types = {0: "hard",
                 1: "firm",
                 2: "normal",
                 3: "soft",
                 4: "wet",
                 5: "water",
                 6: "heights",
                 7: "wall",
                 8: "trees",
                 9: "bushes",
                 10: "bridge",
                 11: "rocks",
                 12: "road"}


class Editor(Environment):

    def __init__(self, main_loop):
        super().__init__(main_loop)

        self.environment_type = "EDITOR"
        self.paint = 4

    def process(self):

        if "save" in self.input_manager.keys:
            bgeutils.load_settings(True)
            self.main_loop.switching_mode = "EDITOR"
        else:
            self.input_manager.update()
            self.camera_control.update()
            self.ui.update()

            if not self.ui.focus:
                self.paint_tile()

            self.debug_text = "{} / {}".format(self.tile_over, terrain_types[self.paint])

    def load_ui(self):
        self.ui = ui_modules.EditorInterface(self)

    def paint_tile(self):

        location = self.tile_over

        if "left_drag" in self.input_manager.buttons:
            map_key = bgeutils.get_key(location)

            if "control" in self.input_manager.keys:
                features = ["water", "heights", "wall", "trees", "bushes", "bridge", "rocks", "road"]
                for erase in features:
                    self.level_map[map_key][erase] = False
                self.level_map[map_key]["softness"] = 3

            elif self.paint < 5:
                self.level_map[map_key]["softness"] = self.paint
            else:
                feature = terrain_types[self.paint]

                if "shift" in self.input_manager.keys:
                    self.level_map[map_key][feature] = False
                else:
                    if feature == "heights":
                        self.level_map[map_key]["water"] = False
                    if feature == "water":
                        self.level_map[map_key]["heights"] = False

                    self.level_map[map_key][feature] = True

            for x in range(-1, 2):
                for y in range(-1, 2):
                    self.draw_tile([x + location[0], y + location[1]])


class Placer(Environment):
    def __init__(self, main_loop):
        super().__init__(main_loop)

        self.environment_type = "PLACER"
        self.debug_text = "PLACER_MODE"
        self.placing = None
        self.team = 1

    def process(self):
        self.input_manager.update()
        self.camera_control.update()
        self.ui.update()

        if not self.ui.focus:
            self.paint_agents()

        self.debug_text = "{} / {} / {} \n{}".format(self.tile_over, self.team, self.placing, len(self.agents))

    def paint_agents(self):
        position = self.tile_over
        team = self.team
        placing = self.placing

        if "left_button" in self.input_manager.buttons:
            target_tile = self.get_tile(position)
            occupier_id = target_tile["occupied"]

            if occupier_id:
                if "control" in self.input_manager.keys:
                    target_agent = self.agents[occupier_id]
                    target_agent.end()
                    del self.agents[occupier_id]
            elif self.placing:
                self.load_agent(None, position, team, placing)

    def load_ui(self):
        self.ui = ui_modules.PlacerInterface(self)


class GamePlay(Environment):
    def __init__(self, main_loop):
        super().__init__(main_loop)

        self.environment_type = "GAMEPLAY"
        self.debug_text = "GAMEPLAY_MODE"
        self.message_list = []

    def initiate_visibility(self):

        self.terrain_canvas = canvas.TerrainCanvas(self)
        self.pathfinder = pathfinding.Pathfinder(self)
        self.visibility = shadow_casting.ShadowCasting(self)

    def process(self):
        self.input_manager.update()
        self.camera_control.update()
        self.ui.update()
        self.agent_update()

        if not self.turn_manager:
            self.turn_manager = turn_managers.PlayerTurn(self)

        self.turn_manager.update()
        if self.turn_manager.finished:
            if self.turn_manager.team == 1:
                self.turn_manager.end()
                self.turn_manager = turn_managers.EnemyTurn(self)
            else:
                self.turn_manager.end()
                self.turn_manager = turn_managers.PlayerTurn(self)

    def update_map(self):
        self.visibility.update()
        self.terrain_canvas.update()

    def load_ui(self):
        self.ui = ui_modules.GamePlayInterface(self)

    def get_messages(self, agent_id):
        agent_messages = []
        remaining_messages = []

        for message in self.message_list:
            if message["agent_id"] == agent_id:
                agent_messages.append(message)
            else:
                remaining_messages.append(message)

        self.message_list = remaining_messages

        return agent_messages

    def agent_update(self):
        for agent_key in self.agents:
            agent = self.agents[agent_key]
            agent.update()



