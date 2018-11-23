import bge
import mathutils
import random


# removed from project for now

class UserInterfaceCanvas(object):

    def __init__(self, owner, environment):
        self.environment = environment
        self.owner = owner
        self.canvas_object = self.environment.add_object("ui_object")
        self.canvas_object.worldPosition.z = 300.0

        self.canvas_size = [64, 32]

        self.canvas = self.create_canvas(self.canvas_object)
        self.red_pixel = self.create_pixel((255, 0, 0, 255))
        self.timer = 0

        self.test_pixels = {i: self.create_pixel([i * 25, 0, 0, 255]) for i in range(11)}

        self.update_canvas()

    def create_pixel(self, rbga):
        r, g, b, a = rbga
        pixel = bytearray(1 * 1 * 4)
        pixel[0] = r
        pixel[1] = g
        pixel[2] = b
        pixel[3] = a

        return pixel

    def update(self):

        if self.trigger():
            self.update_canvas()

    def randomize_uvs(self):

        color = [random.uniform(0.0, 1.0) for _ in range(4)]
        color[3] = 1.0

        self.owner.cursor_plane.color = color

    def trigger(self):
        if self.timer > 12:
            self.timer = 0
            return True
        else:
            self.timer += 1

        return False

    def create_canvas(self, canvas_object):
        canvas_x, canvas_y = self.canvas_size

        tex = bge.texture.Texture(canvas_object, 0, 0)
        tex.source = bge.texture.ImageBuff(color=0)
        tex.source.load(b'\x00\x00\x00' * (canvas_x * canvas_y), canvas_x, canvas_y)

        return tex

    def reload_canvas(self):
        canvas_x, canvas_y = self.canvas_size

        self.canvas.source.load(b'\x00\x00\x00' * (canvas_x * canvas_y), canvas_x, canvas_y)

    def terminate(self):

        del self.canvas

        self.canvas_object.endObject()

    def update_canvas_x(self):
        self.reload_canvas()

        for tile_key in self.test_content:
            tile_value = self.test_content[tile_key][0]

            x, y = tile_key

            pixel_key = max(0, int(tile_value))
            pixel = self.test_pixels[pixel_key]
            self.canvas.source.plot(pixel, 1, 1, x, y, bge.texture.IMB_BLEND_MIX)

        self.canvas.refresh(True)

    def update_canvas(self):
        return
        self.reload_canvas()
        x_max, y_max = self.canvas_size

        ui_tiles = []

        # for x in range(0, 8):
        #     for y in range(13, 16):
        #         ui_tiles.append([x, y])
        #
        # for x in range(12, 18):
        #     for y in range(8, 12):
        #         ui_tiles.append([x, y])
        #
        # for x in range(28, 64):
        #     for y in range(22, 32):
        #         ui_tiles.append([x, y])

        for x in range(x_max):
            for y in range(y_max):

                if [x, y] in ui_tiles:
                    self.canvas.source.plot(self.red_pixel, 1, 1, x, y, bge.texture.IMB_BLEND_MIX)

                elif y < 2:
                    self.canvas.source.plot(self.red_pixel, 1, 1, x, y, bge.texture.IMB_BLEND_MIX)

        self.canvas.refresh(True)
