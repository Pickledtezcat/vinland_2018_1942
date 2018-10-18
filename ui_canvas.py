import bge
import mathutils


class UserInterfaceCanvas(object):

    def __init__(self, environment):
        self.environment = environment
        self.canvas_object = self.environment.add_object("ui_object")
        self.canvas_object.worldPosition.z = 300.0

        self.canvas_size = [32, 16]

        self.canvas = self.create_canvas(self.canvas_object)
        self.red_pixel = self.create_pixel((255, 0, 0, 255))
        self.timer = 0

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

    def update_canvas(self):
        self.reload_canvas()
        x_max, y_max = self.canvas_size

        ui_tiles = [[22, 1], [23, 1], [24, 1], [24, 2], [7, 14], [8, 14]]

        for x in range(8, 12):
            for y in range(4, 8):
                ui_tiles.append([x, y])

        for x in range(x_max):
            for y in range(y_max):

                if x == 0 or y == 0 or x == x_max - 1 or y == y_max - 1:
                    self.canvas.source.plot(self.red_pixel, 1, 1, x, y, bge.texture.IMB_BLEND_MIX)

                if [x, y] in ui_tiles:
                    self.canvas.source.plot(self.red_pixel, 1, 1, x, y, bge.texture.IMB_BLEND_MIX)

        self.canvas.refresh(True)
