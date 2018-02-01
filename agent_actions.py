import bge
import mathutils
import bgeutils



class VehicleMovement(object):
    def __init__(self, agent):
        self.agent = agent
        self.path = []
        self.target_tile = self.agent.stats["position"]
        self.target_facing = self.agent.stats["facing"]
        self.current_tile = self.agent.stats["position"]
        self.current_facing = self.agent.stats["facing"]

        self.start_orientation = None
        self.end_orientation = None

        self.start_position = None
        self.end_position = None

        self.timer = 0
        self.speed = 0.02
        self.done = False

    def set_path(self, path):
        self.path = path
        self.done = False

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

        self.target_facing = [x, y]

    def update(self):

            if not self.target_facing == self.current_facing:
                if not self.start_orientation:
                    self.set_rotation_vectors()

                if self.timer >= 1.0:
                    self.current_facing = self.target_facing
                    self.reset_rotation_vectors()
                    self.timer = 0.0
                else:
                    self.timer += self.speed
                    self.agent.agent_hook.worldOrientation = self.start_orientation.lerp(self.end_orientation, bgeutils.smoothstep(self.timer))

            else:
                if not self.current_tile == self.target_tile:
                    if not self.start_position:
                        self.set_movement_vectors()

                    if self.timer >= 1.0:
                        self.current_tile = self.target_tile
                        self.reset_movement_vectors()
                        self.timer = 0.0
                    else:
                        self.timer += self.speed
                        self.agent.box.worldPosition = self.start_position.lerp(self.end_position, self.timer)
                else:
                    if len(self.path) > 0:
                        self.target_tile = self.path.pop(0)
                        self.get_new_facing()
                    else:
                        self.agent.stats["facing"] = self.current_facing
                        self.agent.stats["position"] = self.current_tile
                        self.agent.set_occupied()
                        self.done = True




