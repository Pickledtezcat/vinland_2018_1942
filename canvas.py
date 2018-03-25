import bge
import bgeutils


class TerrainCanvas(object):

    def __init__(self, environment):
        self.environment = environment
        self.textures = []
        self.ground = self.environment.add_object("vision_object")
        self.ground.worldPosition.z = 300.0
        self.canvas_size = [self.environment.max_x, self.environment.max_y]

        self.white_pixel = self.create_pixel((255, 255, 255, 255))
        self.grey_pixel = self.create_pixel((128, 128, 128, 255))
        self.black_pixel = self.create_pixel((0, 0, 0, 255))

        self.red_pixel = self.create_pixel((255, 0, 0, 255))
        self.blue_pixel = self.create_pixel((0, 0, 255, 255))
        self.green_pixel = self.create_pixel((0, 255, 0, 255))
        self.non_green_pixel = self.create_pixel((0, 64, 0, 255))

        self.canvas = self.create_canvas()
        self.timer = 0
        self.get_textures()

    def fill_all(self):
        pixel = self.white_pixel

        x_max, y_max = self.canvas_size

        for x in range(x_max):
            for y in range(y_max):
                self.canvas.source.plot(pixel, 1, 1, x, y,
                                        bge.texture.IMB_BLEND_MIX)

        self.canvas.refresh(True)

    def update(self):
        if self.timer > 4:
            self.update_canvas()
            self.timer = 0
        else:
            self.timer += 1

    def influence_map_visualize(self):
        self.reload_canvas()

        influence_map = self.environment.influence_map
        highest = -12
        lowest = 1000

        for map_key in influence_map:
            tile_value = influence_map[map_key]
            if tile_value < 100:
                if tile_value > highest:
                    highest = tile_value

                if tile_value < lowest:
                    lowest = tile_value

        for map_key in influence_map:
            tile_value = influence_map[map_key]

            grey = bgeutils.grayscale(lowest, highest, tile_value)
            color_value = max(0, min(255, int(grey * 255)))

            color_pixel = self.create_pixel([0, color_value, 0, 255])
            x, y = map_key

            self.canvas.source.plot(color_pixel, 1, 1, x, y,
                                    bge.texture.IMB_BLEND_MIX)

        #self.canvas.refresh(True)

    def update_canvas(self):
        self.reload_canvas()

        self.influence_map_visualize()

        x_max, y_max = self.canvas_size

        for x in range(x_max):
            for y in range(y_max):
                self.canvas.source.plot(self.black_pixel, 1, 1, x, y,
                                        bge.texture.IMB_BLEND_LIGHTEN)

        friendly = []
        enemies = []

        for agent_key in self.environment.agents:
            agent = self.environment.agents[agent_key]
            team = agent.get_stat("team")
            position = agent.get_stat("position")

            if team == 1:
                friendly.append(position)
            else:
                enemies.append(position)

        for x in range(x_max):
            for y in range(y_max):

                max_movement = self.environment.turn_manager.max_actions

                if self.environment.player_visibility.lit(x, y):
                    self.canvas.source.plot(self.red_pixel, 1, 1, x, y,
                                            bge.texture.IMB_BLEND_LIGHTEN)

                tile = self.environment.pathfinder.graph[(x, y)]
                movable = tile.parent and tile.get_movement_cost() <= max_movement
                active_agent = self.environment.agents[self.environment.turn_manager.active_agent]

                home = (x, y) == active_agent.get_stat("position") and active_agent.get_stat("free_actions") > 0

                if movable or home:
                    self.canvas.source.plot(self.blue_pixel, 1, 1, x, y,
                                            bge.texture.IMB_BLEND_LIGHTEN)

                #if (x, y) in friendly:
                #    self.canvas.source.plot(self.green_pixel, 1, 1, x, y,
                #                            bge.texture.IMB_BLEND_LIGHTEN)

                #elif (x, y) not in enemies:
                #    self.canvas.source.plot(self.non_green_pixel, 1, 1, x, y,
                #                            bge.texture.IMB_BLEND_LIGHTEN)

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

    def reload_canvas(self):
        canvas_x, canvas_y = self.canvas_size

        self.canvas.source.load(b'\x00\x00\x00' * (canvas_x * canvas_y), canvas_x, canvas_y)

    def terminate(self):

        del self.canvas
        self.ground.endObject()

        for texture_set in self.textures:
            texture_set["owner"].endObject()
            del texture_set["saved"]
