import bge
import mathutils
import random


class CameraController(object):

    def __init__(self, level):
        self.level = level
        self.camera_hook = self.level.game_object
        self.track = None

    def update(self):

        if self.track:
            if not self.track_to():
                self.track = None
        else:
            self.process()

    def track_to(self):
        start = self.camera_hook.worldPosition.copy()
        end = mathutils.Vector(self.track).to_3d()
        length = (end - start).length

        self.camera_hook.worldPosition = start.lerp(end, 0.02)

        if length < 0.1:
            self.track = None
            return False

        return True

    def process(self):

        self.track = [random.randint(14, 16), random.randint(14, 16)]


