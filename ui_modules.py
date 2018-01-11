import bge
import bgeutils


class UiModule(object):

    def __init__(self, level):

        self.level = level
        self.cursor_plane = bgeutils.get_ob("cursor_plane", self.level.scene.objects)
        self.camera = self.level.scene.active_camera
        self.cursor = self.level.scene.addObject("standard_cursor", self.level.game_object, 0)
        self.cursor.setParent(self.cursor_plane)

    def update(self):
        mouse_hit = self.mouse_ray(self.level.input_manager.virtual_mouse)
        if mouse_hit[0]:

            location = mouse_hit[1]
            normal = mouse_hit[2]

            self.cursor.worldPosition = location
            self.cursor.worldOrientation = normal.to_track_quat("Z", "Y")

        self.process()

    def process(self):
        pass

    def mouse_ray(self, position):
        x, y = position

        camera = self.camera
        screen_vect = camera.getScreenVect(x, y)
        target_position = camera.worldPosition.copy() - screen_vect
        mouse_hit = camera.rayCast(target_position, camera, 7.0, "cursor_plane", 0, 1, 0)

        return mouse_hit


class EditorInterface(UiModule):

    def __init__(self, level):
        super().__init__(level)

    def process(self):
        pass



