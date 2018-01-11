import bge
import game_input
import ui_modules
import camera_controller


class Environment(object):

    environment_type = "DEFAULT"
    ready = False

    def __init__(self, main_loop):
        self.main_loop = main_loop
        self.game_object = self.main_loop.cont.owner
        self.listener = self.game_object
        self.scene = self.game_object.scene
        self.input_manager = game_input.GameInput()
        self.camera_control = camera_controller.CameraController(self)

        self.assets = None
        self.map_texture = None
        self.audio = None

    def update(self):
        self.process()

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
        self.ui = ui_modules.EditorInterface(self)

    def process(self):
        self.input_manager.update()
        self.camera_control.update()
        self.ui.update()















