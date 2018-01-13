import bge
import bgeutils


class UiModule(object):

    def __init__(self, level):

        self.level = level
        self.cursor_plane = bgeutils.get_ob("cursor_plane", self.level.scene.objects)
        self.camera = self.level.scene.active_camera
        self.cursor = self.add_cursor()
        self.debug_text = self.add_debug_text()

    def add_cursor(self):
        cursor = self.level.scene.addObject("standard_cursor", self.level.game_object, 0)
        cursor.setParent(self.cursor_plane)
        return cursor

    def add_debug_text(self):
        mouse_hit = self.mouse_ray([0.1, 0.9])

        if mouse_hit[0]:
            location = mouse_hit[1]
            normal = mouse_hit[2]
            debug_text = self.level.scene.addObject("main_debug_text", self.level.game_object, 0)
            debug_text.worldPosition = location
            debug_text.worldOrientation = normal.to_track_quat("Z", "Y")
            debug_text.resolution = 12
            debug_text.setParent(self.cursor_plane)
            debug_text["Text"] = "debugging"

            return debug_text

        return None

    def update(self):
        mouse_hit = self.mouse_ray(self.level.input_manager.virtual_mouse)

        if mouse_hit[0]:
            location = mouse_hit[1]
            normal = mouse_hit[2]
            self.cursor.worldPosition = location
            self.cursor.worldOrientation = normal.to_track_quat("Z", "Y")

        self.process()
        self.debug_text["Text"] = self.level.debug_text

    def process(self):
        pass

    def mouse_ray(self, position):
        x, y = position

        camera = self.camera
        screen_vect = camera.getScreenVect(x, y)
        target_position = camera.worldPosition.copy() - screen_vect
        mouse_hit = camera.rayCast(target_position, camera, 50.0, "cursor_plane", 0, 1, 0)

        return mouse_hit

    def end(self):
        self.cursor.endObject()
        self.debug_text.endObject()


class EditorInterface(UiModule):

    def __init__(self, level):
        super().__init__(level)

    def process(self):
        pass



