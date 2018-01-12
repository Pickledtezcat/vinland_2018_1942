import bge
import game_input
import ui_modules
import camera_controller
import random
import bgeutils
import mathutils


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

        self.assets = None
        self.map_texture = None
        self.audio = None

    def update(self):
        if self.ready:
            self.process()
        else:
            self.prep()

    def process(self):
        pass

    def shut_down(self):
        pass

    def prep(self):
        self.ready = True


class Editor(Environment):

    def __init__(self, main_loop):
        super().__init__(main_loop)

        self.environment_type = "EDITOR"
        self.ui = None
        self.assets = []
        self.map = {}
        self.tiles = {}
        self.paint = 3

        self.terrain_types = {0: "water_rocks",
                              1: "water",
                              2: "road",
                              3: "ground",
                              4: "field",
                              5: "bushes",
                              6: "trees",
                              7: "rocks",
                              8: "heights"}

    def process(self):
        self.input_manager.update()
        self.camera_control.update()
        self.ui.update()

        self.paint_tile()

    def paint_tile(self):

        if "wheel_up" in self.input_manager.buttons:
            self.paint = min(8, self.paint + 1)

        if "wheel_down" in self.input_manager.buttons:
            self.paint = max(0, self.paint - 1)

        mouse_hit = self.mouse_ray(self.input_manager.virtual_mouse)

        if mouse_hit[0]:
            location = bgeutils.position_to_location(mouse_hit[1])

            if "left_drag" in self.input_manager.buttons:
                self.map[bgeutils.get_key(location)]["tile_type"] = self.paint
                self.draw_tile(location)

        self.debug_text = self.terrain_types[self.paint]

    def mouse_ray(self, position):
        x, y = position

        camera = self.scene.active_camera
        screen_vect = camera.getScreenVect(x, y)
        target_position = camera.worldPosition.copy() - screen_vect
        mouse_hit = camera.rayCast(target_position, camera, 500.0, "ground", 0, 1, 0)

        return mouse_hit

    def loaded(self):
        self.draw_map()

        self.ui = ui_modules.EditorInterface(self)
        self.ready = True

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
        for x in range(0, 32):
            for y in range(0, 32):
                tile_type = 3
                tile_key = bgeutils.get_key([x, y])

                tile_dict = {"tile_type": tile_type,
                             "bridge": False,
                             "wall": False}

                self.map[tile_key] = tile_dict
                self.tiles[tile_key] = []

        for tile_key in self.map:
            location = bgeutils.get_loc(tile_key)
            self.draw_tile(location)

    def draw_tile(self, location):
        tile_key = bgeutils.get_key(location)

        existing_tiles = self.tiles[tile_key]
        if existing_tiles:
            for tile in existing_tiles:
                tile.endObject()
            self.tiles[tile_key] = []

        map_tile = self.map[tile_key]["tile_type"]
        tile_string = self.terrain_types[map_tile]
        tile = self.scene.addObject(tile_string, self.game_object, 0)
        tile.worldPosition = mathutils.Vector(location).to_3d()
        self.tiles[tile_key].append(tile)





















