import bge


class Environment(object):

    environment_type = "DEFAULT"
    ready = False

    def __init__(self, main_loop):
        self.main_loop = main_loop
        self.game_object = self.main_loop.cont.owner
        self.listener = self.game_object
        self.scene = self.game_object.scene

        self.assets = None
        self.map_texture = None
        self.camera_control = None
        self.audio = None

    def update(self):
        pass

    def shut_down(self):
        pass

    def prep(self):
        self.ready = True


class Editor(Environment):

    def __init__(self, main_loop):
        super().__init__(main_loop)

        self.environment_type = "EDITOR"











