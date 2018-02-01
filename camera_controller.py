import bge
import mathutils
import random


class CameraTrack(object):
    def __init__(self, camera, target):
        self.camera = camera
        self.start = self.camera.worldPosition.copy()
        self.end = mathutils.Vector(target).to_3d()
        self.target = target
        self.timer = 0.0

        if (self.start - self.end).length < 0.1:
            self.timer = 1.1

    def moving(self):

        self.camera.worldPosition = self.start.lerp(self.end, min(self.timer, 1.0))
        self.timer += 0.02

        if self.timer < 1.0:
            return True

        return False


class CameraController(object):

    def __init__(self, level):
        self.level = level
        self.camera_hook = self.level.game_object
        self.actions = []
        self.offset = mathutils.Euler((0.0, 0.0, -0.785398), 'XYZ')

    def update(self):

        if self.actions:
            next_actions = []
            for action in self.actions:
                if action.moving():
                    next_actions.append(action)
            self.actions = next_actions

        else:
            self.process()

    def process(self):
        self.camera_scroll()

    def camera_action(self, target):
        self.actions.append(CameraTrack(self.camera_hook, target))

    def camera_scroll(self):

        mouse_position = self.level.input_manager.virtual_mouse
        x, y = mouse_position
        speed = 0.1
        cam_scroll = x < 0.01 or x > 0.99 or y < 0.01 or y > 0.99

        if cam_scroll:
            mouse_vector = (mathutils.Vector((x, 1.0 - y)) - mathutils.Vector((0.5, 0.5))).to_3d()
            mouse_vector.length = speed

            mouse_vector.rotate(self.offset)

            self.camera_hook.worldPosition += mouse_vector




