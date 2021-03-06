import bge
import game_input
import ui_modules
import camera_controller
import random
import bgeutils
import mathutils
import agents
import turn_managers
import shadow_casting
import canvas
import pathfinding
import static_dicts
import buildings
import effects
import particles
import game_audio
import time


debug_clear_game_map = False


class Environment(object):

    def __init__(self, main_loop):

        self.environment_type = "DEFAULT"
        self.ready = False
        self.main_loop = main_loop
        self.game_object = self.main_loop.cont.owner
        self.listener = self.game_object
        self.scene = self.game_object.scene
        self.input_manager = game_input.GameInput()
        self.camera_control = camera_controller.CameraController(self)
        self.debug_text = ""
        self.printing_text = ""
        self.loading_bar = None

        self.assets = []
        self.mesh_normals = []
        self.decals = []
        self.level_map = {}
        self.tiles = {}
        self.id_index = 0
        self.agents = {}
        self.buildings = {}
        self.effects = {}
        self.ui = None
        self.tile_over = None
        self.turn_manager = None

        self.max_x = 32
        self.max_y = 32
        self.dirt_color = [0.42, 0.37, 0.28, 1.0]
        self.water_color = [0.231, 0.243, 0.243, 1.0]

        self.terrain_canvas = None
        self.player_visibility = None
        self.enemy_visibility = None
        self.pathfinder = None
        self.influence_map = None
        self.debug_time = time.clock()

        self.game_audio = game_audio.Audio(self)

        self.weapons_dict = static_dicts.get_weapon_stats()
        self.vehicle_dict = static_dicts.get_vehicle_stats()
        self.action_dict = static_dicts.get_action_stats()
        self.infantry_dict = static_dicts.get_infantry_stats()
        self.building_dict = static_dicts.get_building_stats()

        self.particles = []

    def get_new_id(self):
        self.id_index += 1
        got_id = self.id_index
        return got_id

    def particle_tester(self):
        """use this function to test particle effects"""

        array = None

        if "shift" in self.input_manager.keys:
            final = True
        else:
            final = False

        if "1" in self.input_manager.keys:
            array = (1, 1)
        if "2" in self.input_manager.keys:
            array = (2, 2)
        if "3" in self.input_manager.keys:
            array = (3, 3)

        if array:
            tile_over = self.tile_over
            particles.BuildingDestruction(self, tile_over, array, final)

    def debug_timer(self, process_string):

        if "0" in self.input_manager.keys:
            current_time = self.debug_time
            new_time = time.clock()

            elapsed = round(new_time - current_time, 4)
            print("{} time: {}".format(process_string, elapsed))
            self.debug_time = new_time

        else:
            self.debug_time = time.clock()

    def update(self):
        if not self.main_loop.shutting_down:
            if self.ready:

                self.debug_timer("___ main entry")
                self.particle_tester()
                self.debug_timer("particles tester")

                self.mouse_over_map()
                self.debug_timer("mouse_over")

                self.input_manager.update()
                self.debug_timer("particles")

                self.camera_control.update()
                self.debug_timer("camera")

                self.agent_update()
                self.debug_timer("agents")
                self.effects_update()
                self.debug_timer("effects")
                self.particle_update()
                self.debug_timer("particles")
                self.audio_update()
                self.debug_timer("audio")

                self.process()
                self.debug_timer("____ process exit")
                self.manage_ui()
                self.debug_timer("manage ui")

            else:
                self.prep()

    def audio_update(self):
        self.game_audio.update()

    def sound_effect(self, sound_details):

        sound = sound_details.get("sound", "ERROR")
        game_object = sound_details.get("owner", self.game_object)
        pitch = sound_details.get("pitch", 1.0)
        attenuation = sound_details.get("attenuation", 1.0)
        loop = sound_details.get("loop", 0)
        volume = sound_details.get("volume", 1.0)

        self.game_audio.sound_effect(sound, game_object, volume, attenuation, loop, pitch)

    def particle_update(self):
        next_generation = []
        for particle in self.particles:
            if not particle.ended:
                particle.update()
                next_generation.append(particle)
            else:
                particle.terminate()

        self.particles = next_generation

    def agent_update(self):
        for agent_key in self.agents:
            agent = self.agents[agent_key]
            agent.update()

        for building_key in self.buildings:
            building = self.buildings[building_key]
            building.update()

    def process(self):
        pass

    def manage_ui(self):
        if self.ui:
            self.ui.update()

    def get_messages(self, agent_id):
        return []

    def add_object(self, object_name):
        new_object = self.scene.addObject(object_name, self.game_object, 0)
        return new_object

    def save_level(self):

        preserved_agents_list = []

        for agent_key in self.agents:
            saving_agent = self.agents[agent_key]
            agent_stats = saving_agent.save_to_dict()
            preserved_agents_list.append(agent_stats)

        preserved_buildings_list = []

        for building_key in self.buildings:
            saving_building = self.buildings[building_key]
            building_stats = saving_building.save_to_dict()
            preserved_buildings_list.append(building_stats)

        preserved_effects = []

        for effect_key in self.effects:
            saving_effect = self.effects[effect_key]
            effect_save = saving_effect.save_to_dict()
            preserved_effects.append(effect_save)

        preserved_decals = []

        for decal in self.decals:
            decal_details = decal.save_decal()
            preserved_decals.append(decal_details)

        level = {"level_map": self.level_map, 'id_index': self.id_index, "effects": preserved_effects,
                 "agents": preserved_agents_list, "buildings": preserved_buildings_list, "decals": preserved_decals}

        bgeutils.save_level(level)

    def load_level(self):

        if debug_clear_game_map:
            return False

        loaded_level = bgeutils.load_level()
        if loaded_level:
            self.level_map = loaded_level["level_map"]
            self.id_index = loaded_level["id_index"]

            for loading_agent in loaded_level["agents"]:
                self.load_agent(loading_agent)

            for loading_building in loaded_level["buildings"]:
                self.load_building(loading_building)

            for loading_effect in loaded_level["effects"]:
                self.load_effect(loading_effect)

            for loading_decal in loaded_level["decals"]:
                self.load_decal(loading_decal)

            return True
        else:
            return False

    def load_decal(self, loading_decal):
        name, position, scale, colored = loading_decal
        particles.Decal(self, name, position, scale, colored)

    def load_effect(self, loading_effect):

        effect_type, team, effect_id, position, turn_timer, stats, flag = loading_effect

        if effect_type == "OBJECTIVE":
            effects.Objective(self, team, effect_id, position, turn_timer, stats, flag)

        if effect_type == "MAP_POINT":
            effects.MapPoint(self, team, effect_id, position, turn_timer, stats, flag)

        if effect_type == "SMOKE":
            effects.Smoke(self, team, effect_id, position, turn_timer)

        if effect_type == "MINES":
            effects.Mines(self, team, effect_id, position, turn_timer)

        if effect_type == "SPOTTER_PLANE":
            effects.SpotterPlane(self, team, effect_id, position, turn_timer)

        if effect_type == "AIR_STRIKE":
            effects.AirStrike(self, team, effect_id, position, turn_timer)

        if effect_type == "REVEAL":
            effects.Reveal(self, team, effect_id, position, turn_timer)

        if effect_type == "PARADROP":
            effects.Paradrop(self, team, effect_id, position, turn_timer)

    def set_tile(self, position, key_type, setting):

        error = None

        x, y = position
        x_ok = 0 <= x < self.max_x
        y_ok = 0 <= y < self.max_y

        if x_ok and y_ok:
            tile_key = bgeutils.get_key(position)
            try:
                self.level_map[tile_key][key_type] = setting
            except:
                error = "SETTING_ERROR"
        else:
            error = "TILE_ERROR"

        if error:
            print("{}/ unable to set map/ {} tile/ {} key/ {} setting".format(error, position, key_type, setting))

    def get_tile(self, position):

        x, y = position
        x_ok = 0 <= x < self.max_x
        y_ok = 0 <= y < self.max_y

        if x_ok and y_ok:
            tile_key = bgeutils.get_key(position)
            return self.level_map[tile_key]

        else:
            return None

    def mouse_over_map(self):
        mouse_hit = self.mouse_ray(self.input_manager.virtual_mouse)

        if mouse_hit[0]:
            self.tile_over = bgeutils.position_to_location(mouse_hit[1])
        else:
            self.tile_over = (0, 0)

    def switch_modes(self, mode):

        valid_modes = ["GAMEPLAY", "EDITOR", "PLACER", "MISSION", "FLAGS"]

        if mode in valid_modes:
            self.save_level()
            self.main_loop.switching_mode = mode

        else:
            if mode == "EXIT":
                self.save_level()
                self.main_loop.shutting_down = True

    def prep(self):
        if not self.assets:
            asset_path = bge.logic.expandPath("//resources/models/test_content.blend")
            test_assets = bge.logic.LibLoad(asset_path, "Scene", async=True)
            self.assets.append(test_assets)

        else:
            self.display_loading()

    def display_loading(self):

        if not self.ui:
            self.ui = ui_modules.LoadingInterface(self)
        else:
            self.ui.update()

        finished = True
        for asset in self.assets:
            if not asset.finished:
                finished = False

        if finished:
            self.ui.end()
            self.ui = None
            self.loaded()

    def generate_map(self):
        for x in range(0, self.max_x):
            for y in range(0, self.max_y):
                tile_type = 2
                tile_key = bgeutils.get_key([x, y])

                tile_dict = {"softness": tile_type,
                             "wall": False,
                             "trees": False,
                             "bushes": False,
                             "bridge": False,
                             "rocks": False,
                             "water": False,
                             "road": False,
                             "heights": False,
                             "occupied": None,
                             "visual": random.randint(0, 8),
                             "smoke": False,
                             "building": False,
                             "mines": False,
                             "objective": None,
                             "map_point": None}

                self.level_map[tile_key] = tile_dict

    def draw_map(self):

        self.create_blank_tiles()

        for tile_key in self.level_map:
            location = bgeutils.get_loc(tile_key)
            self.draw_tile(location)

    def clear_undead(self):
        living_agents = {}

        for agent_key in self.agents:
            agent = self.agents[agent_key]
            if agent.has_effect("DYING"):
                agent.end()
            else:
                living_agents[agent_key] = agent

        self.agents = living_agents

    def load_agent(self, load_dict, position=None, team=1, load_key=None):
        infantry = ["rm", "sm", "mg", "hg", "at", "en", "gr", "gc", "mk", "ht", "pt", "cm"]

        if not load_key:
            load_key = load_dict["agent_name"]

        if load_key in infantry:
            agent = agents.Infantry(self, position, team, load_key, load_dict)
        else:
            vehicle_details = self.vehicle_dict[load_key]
            if vehicle_details["drive_type"] == "GUN_CARRIAGE":
                agent = agents.Artillery(self, position, team, load_key, load_dict)
            else:
                agent = agents.Vehicle(self, position, team, load_key, load_dict)

        return agent

    def load_building(self, load_dict, position=None, rotations=None, load_key=None):

        if not load_key:
            load_key = load_dict["building_name"]

        buildings.Building(self, position, rotations, load_key, load_dict)

    def create_blank_tiles(self):
        for x in range(0, self.max_x):
            for y in range(0, self.max_y):
                tile_key = bgeutils.get_key([x, y])
                self.tiles[tile_key] = []

    def load_ui(self):
        self.ui = ui_modules.EditorInterface(self)

    def initiate_visibility(self):
        self.terrain_canvas = canvas.TerrainCanvas(self)
        self.terrain_canvas.fill_all()

    def loaded(self):

        if not self.load_level():
            self.generate_map()

        self.draw_map()
        self.initiate_visibility()

        self.load_ui()
        self.ready = True

    def draw_tile(self, location):
        x, y = location

        if x < 0 or x > self.max_x - 2:
            return False

        if y < 0 or y > self.max_y - 2:
            return False

        tile_key = bgeutils.get_key(location)
        map_tile = self.get_tile(location)

        if map_tile:
            existing_tiles = self.tiles[tile_key]
            for tile in existing_tiles:
                tile.endObject()
            self.tiles[tile_key] = []

            if map_tile["wall"]:
                self.draw_wall(location, tile_key)
            if map_tile["bridge"]:
                self.draw_bridge(location, tile_key)

            search_array = [(1, 0, 1), (1, 1, 2), (0, 1, 4), (0, 0, 8)]
            hills = 0
            water = 0
            rocks = 0

            for i in range(len(search_array)):
                n = search_array[i]
                nx = x + n[0]
                ny = y + n[1]
                n_key = (nx, ny)

                n_tile = self.get_tile(n_key)

                if n_tile:
                    has_water = n_tile["water"]
                    has_rocks = n_tile["rocks"]
                    has_hills = n_tile["heights"]

                    if has_rocks:
                        rocks += n[2]

                    if has_hills:
                        hills += n[2]

                    if has_water:
                        water += n[2]

            if rocks:
                rock_mesh = "rocks.{}".format(str(rocks).zfill(3))

                rock = self.add_object(rock_mesh)
                rock.worldPosition = mathutils.Vector(location).to_3d()
                if water == 15:
                    rock.worldPosition.z = -0.4
                elif water:
                    rock.worldPosition.z = -0.2
                elif hills == 15:
                    rock.worldPosition.z = 0.5
                elif hills:
                    rock.worldPosition.z = 0.3

                self.tiles[tile_key].append(rock)

            if water:
                tile_mesh = "water.{}".format(str(water).zfill(3))
            elif hills:
                tile_mesh = "hills.{}".format(str(hills).zfill(3))
            else:
                tile_mesh = "hills.000"

            tile = self.add_object(tile_mesh)
            tile.worldPosition = mathutils.Vector(location).to_3d()
            self.tiles[tile_key].append(tile)

            if map_tile["bushes"]:
                visual = map_tile["visual"]
                if map_tile["water"] or map_tile["softness"] == 4:
                    bush_mesh = "bushes_wet.{}".format(str(visual).zfill(3))
                else:
                    bush_mesh = "bushes_dry.{}".format(str(visual).zfill(3))

                bush_tile = self.add_object(bush_mesh)
                bush_tile.worldPosition = mathutils.Vector(location).to_3d()

                if water == 15:
                    bush_tile.worldPosition.z = -0.3
                elif water:
                    bush_tile.worldPosition.z = -0.2
                elif hills == 15:
                    bush_tile.worldPosition.z = 0.5
                elif hills:
                    bush_tile.worldPosition.z = 0.3
                elif rocks == 15:
                    bush_tile.worldPosition.z = 0.2

                self.tiles[tile_key].append(bush_tile)

            if map_tile["trees"]:
                visual = map_tile["visual"]
                tree_mesh = "tree_mesh.{}".format(str(visual).zfill(3))

                tree_tile = self.add_object(tree_mesh)
                tree_tile.worldPosition = mathutils.Vector(location).to_3d()

                if water == 15:
                    tree_tile.worldPosition.z = -0.3
                elif water:
                    tree_tile.worldPosition.z = -0.2
                elif hills == 15:
                    tree_tile.worldPosition.z = 0.5
                elif rocks == 15:
                    tree_tile.worldPosition.z = 0.2

                self.tiles[tile_key].append(tree_tile)

            if tile_mesh not in self.mesh_normals:
                self.mesh_normals.append(tile_mesh)
                self.set_normals(tile)

        # TODO draw bridges

    def draw_wall(self, location, tile_key):

        x, y = location

        search_array = [(-1, 0, 1), (0, -1, 2), (1, 0, 4), (0, 1, 8)]
        wall = 0

        for i in range(len(search_array)):
            n = search_array[i]
            n_key = bgeutils.get_key([x + n[0], y + n[1]])
            n_tile = self.level_map.get(n_key)

            if n_tile:
                if n_tile["wall"]:
                    wall += n[2]

        wall_mesh = "wall_{}".format(wall)
        wall_tile = self.add_object(wall_mesh)
        wall_tile.worldPosition = mathutils.Vector(location).to_3d()
        self.tiles[tile_key].append(wall_tile)

    def draw_bridge(self, location, tile_key):

        x, y = location

        search_array = [(-1, 0, 1), (0, -1, 2), (1, 0, 4), (0, 1, 8)]
        bridge = 0

        for i in range(len(search_array)):
            n = search_array[i]
            n_key = bgeutils.get_key([x + n[0], y + n[1]])
            n_tile = self.level_map.get(n_key)

            if n_tile:
                if n_tile["bridge"]:
                    bridge += n[2]

        bridge_mesh = "bridge_{}".format(bridge)
        bridge_tile = self.add_object(bridge_mesh)
        bridge_tile.worldPosition = mathutils.Vector(location).to_3d()
        self.tiles[tile_key].append(bridge_tile)

    def set_normals(self, mesh_object):

        mesh_list = mesh_object.meshes
        mesh = mesh_list[0]
        mat_list = mesh.materials

        mat_id = 0

        for m in range(len(mat_list)):
            mat_name = mesh.getMaterialName(m)
            if mat_name == "MAbase_terrain_material":
                mat_id = m

        length = mesh.getVertexArrayLength(mat_id)

        for v in range(length):
            vertex = mesh.getVertex(mat_id, v)
            vertex.normal = [0.0, 0.0, 1.0]

    def mouse_ray(self, position):
        x, y = position

        camera = self.scene.active_camera
        screen_vect = camera.getScreenVect(x, y)
        target_position = camera.worldPosition.copy() - screen_vect
        mouse_hit = camera.rayCast(target_position, camera, 500.0, "ground", 0, 1, 0)

        return mouse_hit

    def remove_effect(self, target_tile, effect_string):
        effect_string = target_tile[effect_string]

        if effect_string in self.effects:
            removing_effect = self.effects[effect_string]
            if removing_effect:

                del self.effects[effect_string]
                removing_effect.terminate()
                target_tile[effect_string] = None
        else:
            print(effect_string)

    def effects_update(self):

        next_generation = {}
        checked = []
        current_effects = {effect_key: self.effects[effect_key] for effect_key in self.effects}

        for effect_key in current_effects:
            checked.append(effect_key)
            effect = self.effects[effect_key]

            effect.update()
            if not effect.ended:
                next_generation[effect_key] = effect
            else:
                effect.terminate()

        for old_key in self.effects:
            if old_key not in checked:
                next_generation[old_key] = self.effects[old_key]

        self.effects = next_generation

    def cycle_effects(self, team):
        for effect_key in self.effects:
            effect = self.effects[effect_key]
            if effect.team != team:
                effect.cycle()

    def end(self):
        # add code to remove textures, shut down units and free lib loaded stuff

        if self.terrain_canvas:
            self.terrain_canvas.terminate()

        if self.ui:
            self.ui.end()
            self.ui = None

        for tile_key in self.tiles:
            existing_tiles = self.tiles[tile_key]
            if existing_tiles:
                for tile in existing_tiles:
                    tile.endObject()
                self.tiles[tile_key] = []

        if self.turn_manager:
            self.turn_manager.end()

        for particle in self.particles:
            particle.terminate()

        # TODO free assets

        self.assets = None

        for library in bge.logic.LibList():
            bge.logic.LibFree(library)


terrain_types = {0: "hard",
                 1: "firm",
                 2: "normal",
                 3: "soft",
                 4: "wet",
                 5: "water",
                 6: "heights",
                 7: "wall",
                 8: "trees",
                 9: "bushes",
                 10: "bridge",
                 11: "rocks",
                 12: "road"}


class Editor(Environment):

    def __init__(self, main_loop):
        super().__init__(main_loop)

        self.environment_type = "EDITOR"
        self.paint = 4

    def process(self):

        if "f1" in self.input_manager.keys:
            bgeutils.load_settings(True)
            self.main_loop.switching_mode = "EDITOR"
        else:
            if not self.ui.focus:
                self.paint_tile()

            self.debug_text = "{} / {}".format(self.tile_over, terrain_types[self.paint])

    def load_ui(self):
        self.ui = ui_modules.EditorInterface(self)

    def paint_tile(self):

        location = self.tile_over

        if "left_drag" in self.input_manager.buttons:
            map_key = bgeutils.get_key(location)

            if "control" in self.input_manager.keys:
                features = ["water", "heights", "wall", "trees", "bushes", "bridge", "rocks", "road"]
                for erase in features:
                    self.level_map[map_key][erase] = False

            elif self.paint < 5:
                self.level_map[map_key]["softness"] = self.paint
            else:
                feature = terrain_types[self.paint]

                if feature == "heights":
                    self.level_map[map_key]["water"] = False
                if feature == "water":
                    self.level_map[map_key]["heights"] = False

                self.level_map[map_key][feature] = True

            for x in range(-1, 2):
                for y in range(-1, 2):
                    self.draw_tile([x + location[0], y + location[1]])

            self.terrain_canvas.update_terrain()


class Mission(Environment):
    def __init__(self, main_loop):
        self.ai_painter_dict = static_dicts.get_ai_painter()

        super().__init__(main_loop)

        self.environment_type = "MISSION"
        self.debug_text = "mission mode"
        self.paint = None

    def process(self):

        if "f1" in self.input_manager.keys:
            self.reset_objectives()
        else:
            if not self.ui.focus:
                self.mission_painter()

        self.debug_text = "Mission mode\n{} / {}".format(self.tile_over, self.paint)

    def reset_objectives(self):
        # TODO reset objectives
        pass

    def mission_painter(self):
        position = self.tile_over
        world_position = mathutils.Vector(position).to_3d()
        paint = self.paint
        update_objectives = False

        info_text = ""
        remove = "control" in self.input_manager.keys

        if paint:
            target_tile = self.get_tile(position)
            occupier_id = target_tile["occupied"]
            building_id = target_tile["building"]
            objective_id = target_tile["objective"]
            map_point_id = target_tile["map_point"]

            if "left_button" in self.input_manager.buttons:
                painter_list = self.paint.split("_")
                painter_tag = painter_list.pop(0)
                painter_string = "_".join(painter_list)

                if remove:
                    if objective_id:
                        self.remove_effect(target_tile, "objective")
                        info_text = "REMOVED!: \n{}".format(objective_id)
                    elif map_point_id:
                        self.remove_effect(target_tile, "map_point")
                        info_text = "REMOVED!: \n{}".format(map_point_id)

                elif painter_tag == "OBJECTIVE" and not objective_id:
                    effects.Objective(self, 1, None, position, 0, None, painter_string)
                    info_text = "ADDED OBJECTIVE: \n{}".format(painter_string)
                    update_objectives = True

                elif painter_tag == "COLOR":
                    flag = self.ai_painter_dict[self.paint]["flag"]

                    if painter_list[0] == "INDEX":
                        info_text = "TRIGGER INDEX SET: \n{}".format(flag)

                        if objective_id:
                            objective_object = self.effects[objective_id]
                            objective_object.set_stat("index", flag)

                            if flag == 9:
                                objective_object.set_stat("trigger_index", flag)

                        elif occupier_id:
                            selected_agent = self.agents[occupier_id]
                            selected_agent.set_stat("objective_index", flag)

                        elif map_point_id:
                            selected_point = self.effects[map_point_id]
                            selected_point.set_stat("index", flag)
                        else:
                            info_text = ""

                        update_objectives = True

                    else:
                        if objective_id:
                            objective_object = self.effects[objective_id]
                            objective_object.set_stat("trigger_index", flag)

                            info_text = "TRIGGER INDEX SET: \n{}".format(flag)
                            update_objectives = True

                elif painter_tag == "MAP" and not map_point_id:
                    map_type = "_".join(painter_list[1:])
                    effects.MapPoint(self, 1, None, position, 0, None, map_type)
                    info_text = "ADDED MAP POINT: \n{}".format(map_type)
                    update_objectives = True

                elif painter_tag == "MODIFIER":
                    flag = self.ai_painter_dict[self.paint]["flag"]

                    modifier_type = painter_list[0]
                    modifier_stat = painter_string

                    if objective_id:
                        modifying_objective = self.effects[objective_id]
                        if modifier_type == "HIDDEN":
                            current_stat = modifying_objective.get_stat(modifier_stat)
                            modifying_objective.set_stat(modifier_stat, not current_stat)
                            info_text = "TIMER SET: \n{}: {}".format(modifier_stat, not current_stat)
                        elif modifier_type == "TIMER":
                            modifying_objective.set_stat("max_turns", flag)
                            info_text = "TIMER SET: \n{}".format(flag)

        if update_objectives:
            for effect_key in self.effects:
                effect = self.effects[effect_key]
                if effect.effect_type == "MAP_POINT":
                    effect.update_stats()

            for effect_key in self.effects:
                effect = self.effects[effect_key]
                if effect.effect_type == "OBJECTIVE":
                    effect.update_stats()

        if info_text:
            particles.DebugText(self, info_text, world_position)

    def load_ui(self):
        self.ui = ui_modules.MissionInterface(self)


class AiPainter(Environment):
    def __init__(self, main_loop):
        self.ai_painter_dict = static_dicts.get_ai_painter()

        super().__init__(main_loop)

        self.environment_type = "FLAGS"
        self.debug_text = "Ai painter mode"
        self.paint = None

    def process(self):

        if not self.ui.focus:
            self.flag_painter()

        self.debug_text = "AI painter mode\n{} / {}".format(self.tile_over, self.paint)

    def flag_painter(self):
        position = self.tile_over
        world_position = mathutils.Vector(position).to_3d()
        paint = self.paint
        update_objectives = False
        info_text = ""

        remove = "shift" in self.input_manager.keys

        if paint:
            target_tile = self.get_tile(position)
            occupier_id = target_tile["occupied"]
            building_id = target_tile["building"]

            # TODO allow objectives to set default behavior
            objective_id = target_tile["objective"]

            if "left_button" in self.input_manager.buttons:
                painter_list = paint.split("_")
                painter_tag = painter_list.pop(0)
                painter_details = "_".join(painter_list)

                if occupier_id:
                    modifying_agent = self.agents[occupier_id]
                    if painter_tag == "BEHAVIOR":
                        if remove:
                            modifying_agent.set_stat("default_behavior", self.paint)
                            modifying_agent.set_behavior(self.paint)
                            info_text = "SET DEFAULT BEHAVIOR: \n{}".format(self.paint)
                        else:
                            modifying_agent.set_behavior(self.paint)
                            info_text = "SET BEHAVIOR: \n{}".format(self.paint)
                    else:
                        self.add_effect(occupier_id, self.paint, remove)

                elif building_id:
                    if painter_tag == "AGENT":
                        modifying_building = self.buildings[building_id]
                        if painter_details == "EFFECT_DAMAGED":
                            info_text = modifying_building.set_damage(remove, False)
                        elif painter_details == "EFFECT_BAILED_OUT":
                            info_text = modifying_building.set_damage(remove, True)

        if info_text:
            particles.DebugText(self, info_text, world_position)

    def load_ui(self):
        self.ui = ui_modules.AiPainterInterface(self)

    def add_effect(self, agent_key, effect, remove):
        modifying_agent = self.agents[agent_key]

        agent_effects = ["AGENT_EFFECT_BAILED_OUT",
                         "AGENT_EFFECT_DAMAGED",
                         "AGENT_EFFECT_OUT_OF_AMMO",
                         "AGENT_EFFECT_RAW_RECRUITS",
                         "AGENT_EFFECT_VETERANS",
                         "AGENT_EFFECT_BUTTONED_UP",
                         "AGENT_EFFECT_STAY_PRONE"]

        if effect not in agent_effects:
            return "ERROR, EFFECT NOT VALID"
        else:
            if effect == "AGENT_EFFECT_BAILED_OUT":
                if remove:
                    modifying_agent.set_stat("number", modifying_agent.get_stat("base_number"))
                    modifying_agent.clear_effect("BAILED_OUT")
                    return "NOT BAILED OUT"
                else:
                    modifying_agent.set_stat("number", 0)
                    modifying_agent.add_effect("BAILED_OUT", -1)
                    return "BAILED OUT"

            elif effect == "AGENT_EFFECT_DAMAGED":
                return modifying_agent.set_damaged(remove)

            elif effect == "AGENT_EFFECT_OUT_OF_AMMO":
                if remove:
                    ammo_store = modifying_agent.get_stat("starting_ammo")
                    modifying_agent.set_stat("ammo", ammo_store)
                    return "AMMO RESTORED"

                else:
                    modifying_agent.set_stat("ammo", 0)
                    return "OUT OF AMMO"

            elif effect == "AGENT_EFFECT_RAW_RECRUITS":
                if remove:
                    modifying_agent.clear_effect("RAW_RECRUITS")
                    return "STANDARD EXPERIENCE"
                else:
                    modifying_agent.add_effect("RAW_RECRUITS", -1)
                    modifying_agent.clear_effect("VETERANS")

                    return "RAW RECRUITS"

            elif effect == "AGENT_EFFECT_VETERANS":
                if remove:
                    modifying_agent.clear_effect("VETERANS")
                    return "STANDARD EXPERIENCE"
                else:
                    modifying_agent.add_effect("VETERANS", -1)
                    modifying_agent.clear_effect("RAW_RECRUITS")

                    return "VETERANS"

            elif effect == "AGENT_EFFECT_BUTTONED_UP":
                if remove:
                    modifying_agent.clear_effect("STAY_BUTTONED_UP")
                    return "REMOVED STAY BUTTONED UP"
                else:
                    modifying_agent.add_effect("STAY_BUTTONED_UP", -1)
                    return "STAY BUTTONED UP"

            elif effect == "AGENT_EFFECT_STAY_PRONE":
                if remove:
                    modifying_agent.clear_effect("STAY_PRONE")
                    return "REMOVED STAY PRONE"
                else:
                    modifying_agent.add_effect("STAY_PRONE", -1)
                    return "STAY PRONE"


class Placer(Environment):
    def __init__(self, main_loop):
        super().__init__(main_loop)

        self.environment_type = "PLACER"
        self.debug_text = "PLACER_MODE"
        self.placing = None
        self.team = 1
        self.filter = "misc"
        self.rotation = 0
        self.placing_type = "vehicle"

    def process(self):

        if "f1" in self.input_manager.keys:
            self.clear_undead()
        else:
            if not self.ui.focus:
                self.paint_agents()

        self.debug_text = "{} / {} / {} \n{}".format(self.tile_over, self.team, self.placing, len(self.agents))

    def paint_agents(self):
        position = self.tile_over
        team = self.team
        placing = self.placing

        if "left_button" in self.input_manager.buttons:
            target_tile = self.get_tile(position)
            occupier_id = target_tile["occupied"]
            building_id = target_tile["building"]
            smoke = target_tile["smoke"]
            mines = target_tile["mines"]

            remove = "control" in self.input_manager.keys

            if self.placing:
                if "effect" in self.placing:
                    if "smoke" in self.placing:
                        if smoke:
                            if remove:
                                self.remove_effect(target_tile, "smoke")
                        else:
                            effects.Smoke(self, team, None, position, 0)

                    elif "mines" in self.placing:
                        if mines:
                            if remove:
                                self.remove_effect(target_tile, "mines")
                        else:
                            effects.Mines(self, team, None, position, 0)

                elif self.placing_type == "building":
                    if building_id and remove:
                        target_building = self.buildings[building_id]
                        target_building.end()
                        del self.buildings[building_id]

                    elif not building_id:
                        rotation = int(self.rotation * -0.5)

                        if "shift" in self.input_manager.keys:
                            rotation = random.randint(0, 7)

                        self.load_building(None, position, rotation, placing)

                elif self.placing_type != "building":
                    if occupier_id and remove:
                        target_agent = self.agents[occupier_id]
                        target_agent.end()
                        del self.agents[occupier_id]
                    elif not occupier_id:
                        agent = self.load_agent(None, position, team, placing)
                        facing = tuple(static_dicts.agent_rotations[int(self.rotation)])
                        agent.set_stat("facing", facing)
                        agent.movement.set_starting_position()

    def load_ui(self):
        self.ui = ui_modules.PlacerInterface(self)

    def set_team(self, team):
        self.team = team
        self.ui.end()
        self.ui = ui_modules.PlacerInterface(self)

    def set_rotation(self, rotation):
        self.rotation = rotation
        self.ui.end()
        self.ui = ui_modules.PlacerInterface(self)

    def set_filter(self, new_filter):
        self.filter = new_filter
        self.ui.end()
        self.ui = ui_modules.PlacerInterface(self)


class GamePlay(Environment):
    def __init__(self, main_loop):
        super().__init__(main_loop)

        self.environment_type = "GAMEPLAY"
        self.debug_text = "GAMEPLAY_MODE"
        self.message_list = []
        self.enemy_air_strike_origin = (16, 32)
        self.player_air_strike_origin = (0, 16)

    def zoom_to(self, agent_key, select):
        agent = self.agents[agent_key]
        position = agent.get_stat("position")
        team = agent.get_stat("team")

        if select == "YES" and team == 1:
            self.turn_manager.active_agent = agent_key
            self.turn_manager.reset_ui()
            self.turn_manager.update_pathfinder()

        self.camera_control.camera_action(position)

    def initiate_visibility(self):
        self.pathfinder = pathfinding.Pathfinder(self)
        self.turn_manager = turn_managers.PlayerTurn(self)
        self.player_visibility = shadow_casting.ShadowCasting(self, 1)
        self.enemy_visibility = shadow_casting.ShadowCasting(self, 2)
        self.terrain_canvas = canvas.TerrainCanvas(self)

    def off_board(self, location):
        x_max = self.max_x
        y_max = self.max_y

        x, y = location
        off_board = x <= 0 or y <= 0 or x >= x_max - 1 or y >= y_max - 1
        if off_board:
            return True

        return False

    def process(self):
        self.debug_timer("___ enter process")

        self.ui.update()
        self.debug_timer("ui update")
        self.process_messages()

        # if not self.turn_manager:
        #     self.turn_manager = turn_managers.PlayerTurn(self)

        self.turn_manager.update()
        self.debug_timer("turn manager")

        if self.turn_manager.team == 1:
            if self.turn_manager.finished:
                self.turn_manager.end()
                self.turn_manager = turn_managers.EnemyTurn(self)
                self.switch_ui("ENEMY")

            elif self.turn_manager.active_agent != self.ui.selected_unit:
                self.switch_ui("PLAYER")

        else:
            if self.turn_manager.finished:
                self.turn_manager.end()
                self.turn_manager = turn_managers.PlayerTurn(self)
                self.switch_ui("PLAYER")

        self.debug_timer("ui switch")

        self.terrain_canvas.update()
        self.debug_timer("canvas")

    def switch_ui(self, new_ui):
        self.ui.end()
        if new_ui == "PLAYER":
            self.ui = ui_modules.PlayerInterface(self)
        elif new_ui == "ENEMY":
            self.ui = ui_modules.EnemyInterface(self)

    def update_map(self):
        if self.turn_manager:
            self.player_visibility.update()
            self.enemy_visibility.update()

        # TODO update influence maps in enemy turn only
        # self.influence_map = self.pathfinder.generate_influence_map()

    def load_ui(self):
        self.ui = ui_modules.EnemyInterface(self)

    def process_messages(self):
        # TODO look at the possibility that some actions should be processed outside of agent code

        next_generation = []

    def get_messages(self, agent_id):
        agent_messages = []
        remaining_messages = []

        for message in self.message_list:
            if message["agent_id"] == agent_id:
                agent_messages.append(message)
            else:
                remaining_messages.append(message)

        self.message_list = remaining_messages

        return agent_messages
