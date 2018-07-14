import bge
import mathutils
import bgeutils


class VehicleMovement(object):
    def __init__(self, agent):
        self.agent = agent
        self.path = []
        self.target_tile = self.agent.get_stat("position")
        self.target_facing = self.agent.get_stat("facing")
        self.current_tile = self.agent.get_stat("position")
        self.current_facing = self.agent.get_stat("facing")

        self.start_orientation = None
        self.end_orientation = None

        self.start_position = None
        self.end_position = None

        self.timer = 0
        self.speed = 0.02
        self.left_over = 0.0
        self.done = True

    def set_path(self, path):
        self.path = path
        self.done = False

    def set_target_facing(self, target_facing):
        self.target_facing = target_facing
        self.done = False

    def set_starting_position(self):
        self.target_tile = self.agent.get_stat("position")
        self.target_facing = self.agent.get_stat("facing")
        self.current_tile = self.agent.get_stat("position")
        self.current_facing = self.agent.get_stat("facing")

        self.start_position = None
        self.end_position = None
        self.start_orientation = None
        self.end_orientation = None

        self.agent.box.worldPosition = mathutils.Vector(self.current_tile).to_3d()
        facing = bgeutils.track_vector(self.current_facing)
        self.agent.agent_hook.worldOrientation = facing

    def set_rotation_vectors(self):
        self.start_orientation = bgeutils.track_vector(self.current_facing)
        self.end_orientation = bgeutils.track_vector(self.target_facing)

    def reset_rotation_vectors(self):
        self.start_orientation = None
        self.end_orientation = None

    def set_movement_vectors(self):
        self.start_position = mathutils.Vector(self.current_tile).to_3d()
        self.end_position = mathutils.Vector(self.target_tile).to_3d()

    def reset_movement_vectors(self):
        self.start_position = None
        self.end_position = None

    def get_new_facing(self):
        target = self.target_tile
        current = self.current_tile

        x = target[0] - current[0]
        y = target[1] - current[1]

        self.target_facing = (x, y)

    def update(self):

            if self.target_facing != self.current_facing:
                if not self.start_orientation:
                    self.set_rotation_vectors()

                self.timer += (self.speed + self.left_over)
                self.left_over = 0.0
                self.agent.agent_hook.worldOrientation = self.start_orientation.lerp(self.end_orientation,
                                                                                     bgeutils.smoothstep(self.timer))

                if self.timer >= 1.00:
                    self.left_over = self.timer - 1.0
                    self.current_facing = self.target_facing
                    self.reset_rotation_vectors()
                    self.timer = 0.0

            if self.target_facing == self.current_facing:
                if self.current_tile != self.target_tile:
                    if not self.start_position:
                        self.set_movement_vectors()

                    self.timer += (self.speed + self.left_over)
                    self.left_over = 0.0
                    self.timer += self.speed
                    self.agent.box.worldPosition = self.start_position.lerp(self.end_position, self.timer)

                    if self.timer >= 1.0:
                        self.left_over = self.timer - 1.0
                        self.current_tile = self.target_tile
                        self.reset_movement_vectors()
                        self.timer = 0.0

                if self.current_tile == self.target_tile:
                    if len(self.path) > 0:
                        self.target_tile = self.path.pop(0)
                        self.get_new_facing()
                    else:
                        self.agent.set_stat("facing", self.current_facing)
                        self.agent.set_stat("position", tuple(self.current_tile))
                        self.agent.set_occupied(self.current_tile)
                        self.done = True




