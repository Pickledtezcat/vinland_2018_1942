import bge


class LineOfSight(object):

    def __init__(self, environment):
        self.environment = environment
        self.textures = []
        self.ground = self.environment.add_object("vision_object")
        self.ground.worldPosition.z = 300.0
        self.canvas_size = [self.environment.max_x, self.environment.max_y]

        self.white_pixel = self.create_pixel((255, 255, 255, 255))

        self.canvas = self.create_canvas()
        self.get_textures()

        self.test_draw()

    def test_draw(self):

        for x in range(1, 31):
            for y in range(1, 31):
                self.canvas.source.plot(self.white_pixel, 1, 1, x, y,
                                        bge.texture.IMB_BLEND_LIGHTEN)

        self.canvas.refresh(True)

    def create_pixel(self, rbga):
        r, g, b, a = rbga
        pixel = bytearray(1 * 1 * 4)
        pixel[0] = r
        pixel[1] = g
        pixel[2] = b
        pixel[3] = a

        return pixel

    def get_textures(self):

        texture_list = ["map_texture"]

        for texture in texture_list:
            owner = self.environment.add_object("map_texture")
            owner.worldPosition.z = 300
            texture_set = {"name": texture, "saved": None, "owner": owner}
            self.textures.append(texture_set)

        for texture_set in self.textures:

            texture_object = texture_set["owner"]
            texture_name = texture_set["name"]

            material_id = bge.texture.materialID(texture_object, "MA{}_mat".format(texture_name))
            object_texture = bge.texture.Texture(texture_object, material_id, textureObj=self.canvas)
            texture_set["saved"] = object_texture
            texture_set["saved"].refresh(False)

    def create_canvas(self):
        canvas_x, canvas_y = self.canvas_size

        tex = bge.texture.Texture(self.ground, 0, 0)
        tex.source = bge.texture.ImageBuff(color=0)
        tex.source.load(b'\x00\x00\x00' * (canvas_x * canvas_y), canvas_x, canvas_y)

        return tex

    def terminate(self):

        del self.canvas
        self.ground.endObject()

        for texture_set in self.textures:
            texture_set["owner"].endObject()
            del texture_set["saved"]

    def update(self):
        pass

