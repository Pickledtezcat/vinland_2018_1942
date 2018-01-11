import bge
import bgeutils
import environments


class GameLoop(object):
    def __init__(self, cont):
        self.debug = False
        self.started = False
        self.cont = cont

        self.debug_message = ""
        self.debug_timer = {}

        if self.debug:
            self.debug_test()

        self.state = "editor"
        self.environment = None

        self.start_up()

        bge.render.setMipmapping(0)
        print("game_started")

    def debug_test(self):
        pass

    def update(self):
        if not self.environment:
            self.start_up()

        self.process()

    def start_up(self):
        if self.environment:
            self.environment.shut_down()

        self.environment = environments.Editor(self)

    def process(self):

        if self.environment.ready:
            self.environment.update()
        else:
            self.environment.prep()


