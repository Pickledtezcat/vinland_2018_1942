import bge
import bgeutils
import environments
import bgeutils


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
        self.shutting_down = False
        self.switching_mode = None

        self.start_up()

        bge.render.setMipmapping(0)
        print("game_started")

    def debug_test(self):
        pass

    def update(self):

        if self.shutting_down:
            self.shut_down()
        elif self.switching_mode:
            self.switch_mode()
            self.switching_mode = None
        else:
            if not self.environment:
                self.start_up()

            self.process()

    def start_up(self):
        bgeutils.load_settings()
        self.end_environment()
        self.environment = environments.GamePlay(self)

    def end_environment(self):
        if self.environment:
            self.environment.end()
            self.environment = None

    def shut_down(self):
        self.end_environment()
        bge.logic.endGame()

    def process(self):
        self.environment.update()

    def switch_mode(self):
        self.end_environment()
        print(self.switching_mode)

        if self.switching_mode == "EDITOR":
            self.environment = environments.Editor(self)
        if self.switching_mode == "GAMEPLAY":
            self.environment = environments.GamePlay(self)
        if self.switching_mode == "MISSION":
            self.environment = environments.Mission(self)
        if self.switching_mode == "FLAGS":
            self.environment = environments.AiPainter(self)
        if self.switching_mode == "PLACER":
            self.environment = environments.Placer(self)


