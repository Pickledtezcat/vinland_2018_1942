import bge
import game_input
import ui_modules
import camera_controller
import random
import bgeutils
import mathutils
import agents


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
        self.ui = None

        self.map_texture = None
        self.audio = None

    def update(self):
        if not self.main_loop.shutting_down:
            if self.ready:
                self.process()
            else:
                self.prep()

    def process(self):
        pass

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

    def draw_map(self):

        level_map = bgeutils.load_level()
        if not level_map:
            for x in range(0, 32):
                for y in range(0, 32):
                    tile_type = 3
                    tile_key = bgeutils.get_key([x, y])

                    tile_dict = {"firmness": tile_type,
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
        else:
            self.level_map = level_map

        self.create_blank_tiles()
        for tile_key in self.level_map:
            location = bgeutils.get_loc(tile_key)
            self.draw_tile(location)

    def create_blank_tiles(self):
        for x in range(0, 32):
            for y in range(0, 32):
                tile_key = bgeutils.get_key([x, y])
                self.tiles[tile_key] = []

    def loaded(self):
        self.draw_map()

        self.ui = ui_modules.EditorInterface(self)
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
            ground_type = self.level_map[tile_key]["firmness"]
            tile_string = "ground_{}".format(ground_type)
            if self.level_map[tile_key]["heights"]:
                z_pos = 0.5
            else:
                z_pos = 0.0

        tile = self.scene.addObject(tile_string, self.game_object, 0)
        tile.worldPosition = mathutils.Vector(location).to_3d()
        tile.worldPosition.z = z_pos
        self.tiles[tile_key].append(tile)

        features = ["trees", "bushes", "bridge", "rocks", "road"]

        if self.level_map[tile_key]["wall"]:
            self.draw_wall(location, tile_key)

        for feature in features:
            if self.level_map[tile_key][feature]:
                feature_tile = self.scene.addObject(feature, self.game_object, 0)
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
        wall_tile = self.scene.addObject(wall_mesh, self.game_object, 0)
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

        if self.ui:
            self.ui.end()
            self.ui = None

        for tile_key in self.tiles:
            existing_tiles = self.tiles[tile_key]
            if existing_tiles:
                for tile in existing_tiles:
                    tile.endObject()
                self.tiles[tile_key] = []

        self.assets = None

        for library in bge.logic.LibList():
            bge.logic.LibFree(library)


class Editor(Environment):

    def __init__(self, main_loop):
        super().__init__(main_loop)

        self.environment_type = "EDITOR"
        self.paint = 4

    def process(self):
        self.input_manager.update()
        self.camera_control.update()
        self.ui.update()

        if not self.ui.focus:
            self.paint_tile()

            if "escape" in self.input_manager.keys:
                bgeutils.save_level(self.level_map)
                self.main_loop.shutting_down = True

            if "switch_mode" in self.input_manager.keys:
                bgeutils.save_level(self.level_map)
                self.main_loop.switching_mode = "GAMEPLAY"

    def paint_tile(self):

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

        mouse_hit = self.mouse_ray(self.input_manager.virtual_mouse)
        first_line = mouse_hit[1]

        if mouse_hit[0]:
            location = bgeutils.position_to_location(mouse_hit[1])

            if "left_drag" in self.input_manager.buttons:
                map_key = bgeutils.get_key(location)

                if "control" in self.input_manager.keys:
                    features = ["water", "heights", "wall", "trees", "bushes", "bridge", "rocks", "road"]
                    for erase in features:
                        self.level_map[map_key][erase] = False
                    self.level_map[map_key]["firmness"] = 3

                elif self.paint < 5:
                    self.level_map[map_key]["firmness"] = self.paint
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

            first_line = [int(round(a)) for a in mouse_hit[1]][:2]

        self.debug_text = "{} / {}".format(first_line, terrain_types[self.paint])

    def loaded(self):
        self.draw_map()

        self.ui = ui_modules.EditorInterface(self)
        self.ready = True


class GamePlay(Environment):
    def __init__(self, main_loop):
        super().__init__(main_loop)

        self.environment_type = "GAMEPLAY"
        self.debug_text = "GAMEPLAY_MODE"
        self.agent = None

    def process(self):
        self.input_manager.update()
        self.camera_control.update()
        self.ui.update()

        if "escape" in self.input_manager.keys:
            bgeutils.save_level(self.level_map)
            self.main_loop.shutting_down = True

        if "switch_mode" in self.input_manager.keys:
            bgeutils.save_level(self.level_map)
            self.main_loop.switching_mode = "EDITOR"

    def loaded(self):
        self.draw_map()

        self.ui = ui_modules.GamePlayInterface(self)

        self.agent = agents.Agent(self, (15, 16), "assault_gun")
        self.ready = True





















