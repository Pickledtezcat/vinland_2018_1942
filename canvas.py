import bge
import bgeutils
#from struct import *
import influence_maps


class TerrainCanvas(object):

    def __init__(self, environment):
        self.environment = environment
        self.textures = []
        self.vision_object = self.environment.add_object("vision_object")
        self.vision_object.worldPosition.z = 300.0

        self.terrain_object = self.environment.add_object("terrain_object")
        self.terrain_object.worldPosition.z = 300.0

        self.canvas_size = [self.environment.max_x, self.environment.max_y]

        self.white_pixel = self.create_pixel((255, 255, 255, 255))
        self.grey_pixel = self.create_pixel((128, 128, 128, 255))
        self.black_pixel = self.create_pixel((0, 0, 0, 255))

        self.red_pixel = self.create_pixel((255, 0, 0, 255))
        self.half_red_pixel = self.create_pixel((127, 0, 0, 255))
        self.blue_pixel = self.create_pixel((0, 0, 255, 255))
        self.green_pixel = self.create_pixel((0, 255, 0, 255))
        self.non_green_pixel = self.create_pixel((0, 64, 0, 255))

        self.terrain_pixels = {0: self.create_pixel((0, 0, 0, 255)),
                               1: self.create_pixel((64, 0, 0, 255)),
                               2: self.create_pixel((128, 0, 0, 255)),
                               3: self.create_pixel((191, 0, 0, 255)),
                               4: self.create_pixel((255, 0, 0, 255)),
                               5: self.create_pixel((0, 128, 0, 255)),
                               6: self.create_pixel((0, 255, 0, 255)),
                               7: self.create_pixel((0, 0, 220, 255)),
                               8: self.create_pixel((0, 0, 255, 255))}

        self.paint_type = "BLANK"
        self.canvas = self.create_canvas(self.vision_object)
        self.terrain_canvas = self.create_canvas(self.terrain_object)
        self.timer = 0

        self.get_textures("map_texture", self.canvas)
        self.get_textures("terrain_texture", self.terrain_canvas)

        self.update_terrain()
        self.influence_map = None

    def update_terrain(self):

        self.reload_terrain()

        x_max, y_max = self.canvas_size

        for x in range(x_max):
            for y in range(y_max):

                map_tile = self.environment.get_tile((x, y))
                if map_tile:
                    if map_tile["water"]:
                        if map_tile["rocks"]:
                            water_value = 5
                        else:
                            water_value = 6

                        water_pixel = self.terrain_pixels[water_value]
                        self.terrain_canvas.source.plot(water_pixel, 1, 1, x, y, bge.texture.IMB_BLEND_LIGHTEN)

                    soft_value = map_tile["softness"]
                    soft_pixel = self.terrain_pixels[soft_value]
                    self.terrain_canvas.source.plot(soft_pixel, 1, 1, x, y, bge.texture.IMB_BLEND_LIGHTEN)

                    if map_tile["road"]:
                        if map_tile["visual"] < 4:
                            road_pixel = self.terrain_pixels[7]
                        else:
                            road_pixel = self.terrain_pixels[8]
                        self.terrain_canvas.source.plot(road_pixel, 1, 1, x, y, bge.texture.IMB_BLEND_LIGHTEN)

        self.terrain_canvas.refresh(True)

    def fill_all(self):
        self.reload_canvas()

        pixel = self.white_pixel
        x_max, y_max = self.canvas_size

        for x in range(x_max):
            for y in range(y_max):
                self.canvas.source.plot(pixel, 1, 1, x, y,
                                        bge.texture.IMB_BLEND_MIX)

        self.canvas.refresh(True)

    def set_update(self, update_type):

        self.paint_type = update_type
        self.update_canvas()

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

    def update_canvas(self):

        if self.paint_type == "BLANK":
            self.fill_all()

        elif self.paint_type == "INACTIVE":
            self.fill_view(False, False, False)

        elif self.paint_type == "MOVE":
            self.fill_view(False, True, False)

        elif self.paint_type == "SHOOTING":
            self.fill_view(True, False, False)

        elif self.paint_type == "FRIEND":
            self.fill_view(False, False, True)
        else:
            self.debug_canvas()

        # self.terrain_canvas.refresh(True)

    def fill_view(self, restricted, movement, friend):

        turn_manager = self.environment.turn_manager
        selected_agent = turn_manager.active_agent
        adjacent_tiles = self.environment.pathfinder.adjacent_tiles

        if selected_agent:
            active_agent = self.environment.agents[selected_agent]
            max_movement = self.environment.turn_manager.max_actions

        else:
            active_agent = None
            max_movement = 0

        self.reload_canvas()
        x_max, y_max = self.canvas_size

        off_board = []
        for x in range(x_max):
            for y in range(y_max):
                if x == 0 or y == 0 or x >= x_max - 1 or y >= y_max - 1:
                    off_board.append((x, y))

        for x in range(x_max):
            for y in range(y_max):

                # TODO remove debugging view
                if "control" in self.environment.input_manager.keys:
                    lit = self.environment.enemy_visibility.lit(x, y)
                else:
                    lit = self.environment.player_visibility.lit(x, y)

                vision_pixel = None

                if (x, y) not in off_board:
                    if not restricted:
                        if lit > 0:
                            vision_pixel = self.red_pixel
                    elif lit == 2:
                        vision_pixel = self.red_pixel
                    elif lit == 1:
                        vision_pixel = self.half_red_pixel

                if vision_pixel:
                    self.canvas.source.plot(vision_pixel, 1, 1, x, y,
                                            bge.texture.IMB_BLEND_LIGHTEN)
                if active_agent and lit > 0:
                    home = (x, y) == active_agent.get_stat("position") and active_agent.get_stat("free_actions") > 0

                    if friend:
                        if home or (x, y) in adjacent_tiles:
                            self.canvas.source.plot(self.blue_pixel, 1, 1, x, y,
                                                    bge.texture.IMB_BLEND_LIGHTEN)

                    elif movement:
                        tile = self.environment.pathfinder.graph[(x, y)]
                        movable = tile.parent and tile.get_movement_cost() <= max_movement

                        if movable or home:
                            self.canvas.source.plot(self.blue_pixel, 1, 1, x, y,
                                                    bge.texture.IMB_BLEND_LIGHTEN)

        self.canvas.refresh(True)

    def influence_map_visualize(self):
        self.reload_canvas()

        if not self.influence_map:
            influence_map_object = influence_maps.RetreatMap(self.environment)
            self.influence_map = influence_map_object.generate_influence_map()

        influence_map = self.influence_map

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

            color_pixel = self.create_pixel([255, color_value, 255, 255])
            x, y = map_key

            self.canvas.source.plot(color_pixel, 1, 1, x, y,
                                    bge.texture.IMB_BLEND_MIX)

        self.canvas.refresh(True)

    def debug_canvas(self):

        turn_manager = self.environment.turn_manager
        selected_agent = turn_manager.active_agent

        # TODO set canvas updates for enemy turn, busy movement and shooting actions

        if selected_agent:
            active_agent = self.environment.agents[selected_agent]

            self.reload_canvas()
            self.influence_map_visualize()

            x_max, y_max = self.canvas_size

            # for x in range(x_max):
            #     for y in range(y_max):
            #         self.canvas.source.plot(self.black_pixel, 1, 1, x, y,
            #                                 bge.texture.IMB_BLEND_LIGHTEN)

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
                    lit = self.environment.player_visibility.lit(x, y)

                    vision_pixel = None

                    if not active_agent.busy:

                        if lit == 2:
                            vision_pixel = self.red_pixel
                        elif lit == 1:
                            vision_pixel = self.half_red_pixel

                        if vision_pixel:
                            self.canvas.source.plot(vision_pixel, 1, 1, x, y,
                                                    bge.texture.IMB_BLEND_LIGHTEN)

                        tile = self.environment.pathfinder.graph[(x, y)]
                        movable = tile.parent and tile.get_movement_cost() <= max_movement

                        home = (x, y) == active_agent.get_stat("position") and active_agent.get_stat("free_actions") > 0

                        if movable or home:
                            self.canvas.source.plot(self.blue_pixel, 1, 1, x, y,
                                                    bge.texture.IMB_BLEND_LIGHTEN)

                    else:
                        if lit > 0:
                            self.canvas.source.plot(self.red_pixel, 1, 1, x, y,
                                                    bge.texture.IMB_BLEND_LIGHTEN)

                    # if (x, y) in friendly:
                    #    self.canvas.source.plot(self.green_pixel, 1, 1, x, y,
                    #                            bge.texture.IMB_BLEND_LIGHTEN)

                    # elif (x, y) not in enemies:
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

    def get_textures(self, texture, canvas_object):

        owner = self.environment.add_object(texture)
        owner.worldPosition.z = 300

        material_id = bge.texture.materialID(owner, "MA{}_mat".format(texture))
        object_texture = bge.texture.Texture(owner, material_id, textureObj=canvas_object)
        object_texture.refresh(False)
        texture_set = {"name": texture, "saved": object_texture, "owner": owner}

        self.textures.append(texture_set)

    def create_canvas(self, canvas_object):
        canvas_x, canvas_y = self.canvas_size

        tex = bge.texture.Texture(canvas_object, 0, 0)
        tex.source = bge.texture.ImageBuff(color=0)
        tex.source.load(b'\x00\x00\x00' * (canvas_x * canvas_y), canvas_x, canvas_y)

        return tex

    def reload_canvas(self):
        canvas_x, canvas_y = self.canvas_size

        self.canvas.source.load(b'\x00\x00\x00' * (canvas_x * canvas_y), canvas_x, canvas_y)

    def reload_terrain(self):
        canvas_x, canvas_y = self.canvas_size

        self.terrain_canvas.source.load(b'\x00\x00\x00' * (canvas_x * canvas_y), canvas_x, canvas_y)

    def terminate(self):

        del self.canvas
        del self.terrain_canvas

        self.vision_object.endObject()
        self.terrain_object.endObject()

        for texture_set in self.textures:
            texture_set["owner"].endObject()
            del texture_set["saved"]
