import bge
import mathutils
import random


class UserInterfaceCanvas(object):

    def __init__(self, environment):
        self.environment = environment
        self.canvas_object = self.environment.add_object("ui_object")
        self.canvas_object.worldPosition.z = 300.0

        self.canvas_size = [32, 16]

        self.canvas = self.create_canvas(self.canvas_object)
        self.red_pixel = self.create_pixel((255, 0, 0, 255))
        self.timer = 0
        self.test_content = self.create_test_content()

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

    def create_test_content(self):
        test_content = {}
        for x in range(32):
            for y in range(16):
                test_content[(x, y)] = [10, random.uniform(0.05, 0.15)]

        return test_content

    def update_test_content(self):

        for tile_key in self.test_content:
            if self.test_content[tile_key][0] > 0.0:
                self.test_content[tile_key][0] -= self.test_content[tile_key][1]

    def update(self):

        #if self.trigger():
        self.update_test_content()
        self.update_canvas()

    def trigger(self):
        if self.timer > 6:
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
        self.reload_canvas()
        x_max, y_max = self.canvas_size

        ui_tiles = []

        for x in range(0, 8):
            for y in range(13, 16):
                ui_tiles.append([x, y])

        for x in range(22, 30):
            for y in range(0, 3):
                ui_tiles.append([x, y])

        for x in range(x_max):
            for y in range(y_max):

                if [x, y] in ui_tiles:
                    self.canvas.source.plot(self.red_pixel, 1, 1, x, y, bge.texture.IMB_BLEND_MIX)

                elif y == 0:
                    self.canvas.source.plot(self.red_pixel, 1, 1, x, y, bge.texture.IMB_BLEND_MIX)

        self.canvas.refresh(True)
