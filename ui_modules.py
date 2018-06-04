import bge
import bgeutils
import static_dicts

ui_colors = {"GREEN": [0.1, 0.8, 0.0, 1.0],
             "OFF_GREEN": [0.02, 0.1, 0.0, 1.0],
             "RED": [1.0, 0.0, 0.0, 1.0],
             "BLUE": [0.1, 0.2, 0.7, 1.0],
             "OFF_BLUE": [0.0, 0.05, 0.1, 1.0],
             "OFF_RED": [0.1, 0.0, 0.0, 1.0],
             "YELLOW": [0.5, 0.4, 0.0, 1.0],
             "OFF_YELLOW": [0.05, 0.04, 0.0, 1.0],
             "HUD": [0.07, 0.6, 0.05, 1.0]}


class HealthBar(object):

    def __init__(self, manager, owner_id):
        self.manager = manager
        self.owner_id = owner_id
        self.owner = self.manager.environment.agents[self.owner_id]
        self.box = self.manager.environment.add_object("ui_health")
        self.cover_icon = None
        self.cover_string = None
        self.active_cover = None
        self.active_cover_status = None

        self.ended = False

        self.cover_adder = bgeutils.get_ob("cover_adder", self.box.children)
        self.action_adder = bgeutils.get_ob("action_adder", self.box.children)
        self.armor_adder = bgeutils.get_ob("armor_adder", self.box.children)
        self.shock_adder = bgeutils.get_ob("shock_adder", self.box.children)
        self.health_adder = bgeutils.get_ob("health_adder", self.box.children)
        self.damage_adder = bgeutils.get_ob("damage_adder", self.box.children)
        self.action_count = bgeutils.get_ob("action_count", self.box.children)

        self.action_count.resolution = 12

        self.categories = self.get_categories()

        self.pips = {}
        self.add_pips()

    def update(self):
        if not self.ended:
            self.update_info_string()
            self.update_screen_position()

    def update_info_string(self):
        if self.owner.get_stat("team") == 1:
            effects = self.owner.get_stat("effects")
            effect_list = ["{}:{}".format(".".join((ek[0] for ek in effect_key.split("_"))), effects[effect_key]) for effect_key in effects]

            effect_string = "/ ".join(effect_list)

            self.action_count["Text"] = effect_string
        else:
            base_target = None
            base_penetration = None
            flanked = False
            covered = False

            target_data = self.owner.target_data
            if target_data and not target_data["target_type"] == "INVALID":
                contents = target_data["contents"]
                if target_data["target_type"] == "EXPLOSION":
                    base_target = contents[2]
                elif target_data["target_type"] == "DIRECT_ATTACK":
                    base_target = contents[4]
                    base_penetration = contents[5]
                    flanked = contents[2]
                    covered = contents[3]

            if self.active_cover_status != covered:
                self.active_cover_status = covered
                if covered:
                    tail = "on"
                else:
                    tail = "off"

                self.active_cover.replaceMesh("active_cover_{}".format(tail))

            if not base_target:
                self.action_count["Text"] = ""
            else:
                if flanked:
                    flank_string = "(flanked)"
                else:
                    flank_string = ""

                hit_string = "{}%".format(int(bgeutils.dice_probability(2, base_target)))

                if base_penetration is not None:
                    armor_string = "{}%".format(int(bgeutils.dice_probability(1, base_penetration)))
                else:
                    armor_string = ""

                self.action_count["Text"] = "{} - {} {}".format(hit_string, armor_string, flank_string)

    def get_categories(self):
        categories = [
            ["action", self.action_adder, [self.owner.get_stat("base_actions"), self.owner.get_stat("free_actions")],
             "YELLOW"],
            ["armor", self.armor_adder, self.owner.get_stat("armor"), "BLUE"],
            ["shock", self.shock_adder, int(self.owner.get_stat("shock") * 0.1), "RED"],
            ["health", self.health_adder,
             [int(self.owner.get_stat("hps") * 0.1), int((self.owner.get_stat("hps") - self.owner.get_stat("hp_damage")) * 0.1)], "GREEN"]]

        return categories

    def update_cover(self):
        cover_string = self.owner.get_cover()
        if self.cover_string != cover_string:
            self.cover_string = cover_string
            self.cover_icon.replaceMesh("cover_icon.{}".format(str(cover_string).zfill(3)))

    def add_pips(self):

        for category in self.categories:
            name, adder, stat, color = category
            piplist = []
            new_color = "OFF_{}".format(color)

            for i in range(10):
                pip = adder.scene.addObject("ui_pip", adder, 0)
                piplist.append(pip)
                pip.setParent(adder)
                pip.localPosition.x += i * 0.004
                pip.color = ui_colors[new_color]

            self.pips[name] = piplist

        self.cover_icon = self.box.scene.addObject("cover_icon.000", self.cover_adder, 0)
        self.cover_icon.setParent(self.cover_adder)

        self.active_cover = self.box.scene.addObject("active_cover_off", self.cover_adder, 0)
        self.active_cover.setParent(self.cover_adder)

        if self.owner.get_stat("team") == 2:
            self.active_cover.color = [0.8, 0.2, 0.1, 1.0]
            self.cover_icon.color = [0.8, 0.2, 0.1, 1.0]
        else:
            self.active_cover.color = [0.69, 0.92, 0.95, 1.0]
            self.cover_icon.color = [0.69, 0.92, 0.95, 1.0]

    def update_pips(self):

        self.categories = self.get_categories()

        for category in self.categories:
            name, adder, stat, color = category

            for i in range(10):

                twin_sets = ["armor", "action", "health"]

                if name in twin_sets:
                    pip_stat = max(stat[0], stat[1])
                    if stat[1] > i:
                        pip_color = color
                    else:
                        pip_color = "OFF_{}".format(color)
                else:
                    pip_color = color
                    pip_stat = stat

                if pip_stat > i:
                    visibility = 1
                else:
                    visibility = 0

                pip = self.pips[name][i]
                pip.visible = visibility

                pip.color = ui_colors[pip_color]

    def update_screen_position(self):
        position = self.owner.box.worldPosition.copy()
        camera = self.box.scene.active_camera

        invalid = not self.owner.on_screen or not self.owner.visible or self.owner.has_effect("DYING")

        if not invalid:
            screen_position = camera.getScreenPosition(position)
            mouse_hit = self.manager.mouse_ray(screen_position, "cursor_plane")
            if mouse_hit[0]:
                self.box.localScale = [1.0, 1.0, 1.0]
                plane, screen_position, screen_normal = mouse_hit
                self.box.worldPosition = screen_position
                self.box.worldOrientation = screen_normal.to_track_quat("Z", "Y")
                self.update_pips()
                self.update_cover()
            else:
                invalid = True

        if invalid:
            self.ended = True
            self.box.localScale = [0.0, 0.0, 0.0]

    def terminate(self):
        self.box.endObject()


class Button(object):

    def __init__(self, manager, spawn, name, x, y, scale, message, mouse_over_text, null=False):
        self.manager = manager
        self.spawn = spawn
        self.name = name
        self.message = message
        self.mouse_over_text = mouse_over_text

        x, y = self.get_screen_placement(x, y)

        self.box = self.add_box(x, y, spawn, scale)
        self.pressed = False
        self.timer = 20

        self.on_color = [1.0, 1.0, 1.0, 1.0]
        self.off_color = [0.2, 0.2, 0.2, 1.0]
        self.null = null
        if self.null:
            self.box.color = self.off_color

    def add_box(self, x, y, spawn, scale):
        box = spawn.scene.addObject(self.name, spawn, 0)
        box["owner"] = self
        box.setParent(spawn)
        box.localPosition = [x, y, -0.05]
        box.localScale = [scale, scale, scale]
        return box

    def get_screen_placement(self, x, y):
        x *= 0.52
        y *= 0.285

        return [x, y]

    def update(self):

        if not self.null:
            if self.pressed:
                self.box.color = self.off_color
                if self.timer <= 0:
                    if not self.message:
                        message = self.name
                    else:
                        message = self.message

                    self.manager.messages.append(message)
                    self.pressed = False
                    self.reset()
                else:
                    self.timer -= 1

            else:
                self.reset()

    def reset(self):
        self.timer = 20
        self.pressed = False
        self.box.color = self.on_color

    def terminate(self):
        self.box.endObject()


class UiModule(object):

    def __init__(self, environment):

        self.environment = environment
        self.cursor_plane = bgeutils.get_ob("cursor_plane", self.environment.scene.objects)
        self.camera = self.environment.scene.active_camera
        self.cursor = self.add_cursor()
        self.messages = []
        self.buttons = []
        self.action_buttons = []
        self.focus = False
        self.context = "NONE"
        self.debug_text = self.add_debug_text([0.1, 0.8])
        self.printer = self.add_debug_text([0.1, 0.2])
        self.mouse_over_text = self.add_debug_text([0.1, 0.5])
        self.mouse_over_text.localScale *= 0.5

        self.health_bars = {}

        self.selected_unit = self.get_selected_unit()
        # self.team = 1
        self.cool_off = 30

        self.add_buttons()
        self.add_editor_buttons()

    def get_selected_unit(self):
        return None

    def add_editor_buttons(self):
        pass

    def add_buttons(self):

        modes = ["GAMEPLAY", "EDITOR", "PLACER", "MISSION", "FLAGS", "EXIT"]

        for i in range(len(modes)):
            mode = modes[i]
            spawn = self.cursor_plane
            ox = 0.9
            oy = 0.9
            button_name = "button_mode_{}".format(mode)
            button = Button(self, spawn, button_name, ox - (i * 0.1), oy, 0.1, "", "")
            self.buttons.append(button)

    def add_cursor(self):
        cursor = self.environment.add_object("standard_cursor")
        cursor.setParent(self.cursor_plane)
        return cursor

    def add_debug_text(self, screen_position):
        mouse_hit = self.mouse_ray(screen_position, "cursor_plane")

        if mouse_hit[0]:
            location = mouse_hit[1]
            normal = mouse_hit[2]
            debug_text = self.environment.add_object("main_debug_text")
            debug_text.worldPosition = location
            debug_text.worldOrientation = normal.to_track_quat("Z", "Y")
            debug_text.resolution = 12
            debug_text.setParent(self.cursor_plane)
            debug_text["Text"] = "debugging"

            return debug_text

        return None

    def update(self):

        self.debug_text["Text"] = self.environment.debug_text
        self.printer["Text"] = self.environment.printing_text
        self.process()

        mouse_hit = self.mouse_ray(self.environment.input_manager.virtual_mouse, "cursor_plane")

        if mouse_hit[0]:
            location = mouse_hit[1]
            normal = mouse_hit[2]
            self.cursor.worldPosition = location
            self.cursor.worldOrientation = normal.to_track_quat("Z", "Y")

        self.handle_elements()
        self.set_cursor()
        self.set_mouse_over_text()

    def set_mouse_over_text(self):
        location = self.environment.tile_over
        tile = self.environment.get_tile(location)

        occupier = None
        building = None
        objective = None
        occupier_string = ""
        building_string = ""
        objective_string = ""

        occupier_key = tile["occupied"]
        building_key = tile["building"]
        objective_key = tile["objective"]

        if building_key:
            building = self.environment.buildings[building_key]
            building_string = building.get_mouse_over()

        if occupier_key:
            occupier = self.environment.agents[occupier_key]
            occupier_string = occupier.get_mouse_over()

        if objective_key and self.environment.environment_type != "GAMEPLAY":
            objective = self.environment.effects[objective_key]
            objective_string = objective.get_mouse_over()

        self.mouse_over_text["Text"] = "{}\n\n\n\n{}\n{}".format(building_string, occupier_string, objective_string)

    def handle_elements(self):
        self.handle_health_bars()

        ui_hit = self.mouse_ray(self.environment.input_manager.virtual_mouse, "ui_element")

        if self.cool_off > 0:
            self.context = "WAITING"
            self.cool_off -= 1
        else:
            if ui_hit[0]:
                self.focus = True
                self.handle_buttons(ui_hit[0])
                self.context = "SELECT"
            else:
                self.focus = False
                self.in_game_context()

        for button in self.buttons:
            button.update()

        for action_button in self.action_buttons:
            action_button.update()

        self.process_messages()

    def in_game_context(self):
        self.context = "NONE"

    def handle_health_bars(self):
        pass

    def handle_buttons(self, hit_button):
        if hit_button["owner"]:
            if "left_button" in self.environment.input_manager.buttons:
                if not hit_button["owner"].pressed:
                    hit_button["owner"].pressed = True

    def set_cursor(self):

        if self.context == "SELECT":
            self.cursor.replaceMesh("select_cursor")
        elif self.context == "WAITING":
            self.cursor.replaceMesh("waiting_cursor")
        elif self.context == "TARGET":
            self.cursor.replaceMesh("target_cursor")
        elif self.context == "NO_TARGET":
            self.cursor.replaceMesh("no_target_cursor")
        elif self.context == "MAP_TARGET":
            self.cursor.replaceMesh("map_target_cursor")
        elif self.context == "CYCLE":
            self.cursor.replaceMesh("cycle_cursor")
        elif self.context == "BAD_TARGET":
            self.cursor.replaceMesh("bad_target_cursor")
        elif self.context == "UNKNOWN":
            self.cursor.replaceMesh("unknown_cursor")
        else:
            self.cursor.replaceMesh("standard_cursor")

    def process_messages(self):

        if self.messages:
            message_content = self.messages[0]
            elements = message_content.split("_")

            ai_flags = ["MAP", "OBJECTIVE", "MODIFIER", "AGENT", "COLOR", "BEHAVIOR"]

            if elements[0] == "button":
                if elements[1] in ai_flags:
                    self.environment.paint = "_".join(elements[1:])

                if elements[1] == "terrain":
                    self.environment.paint = int(elements[2])
                if elements[1] == "mode":
                    self.environment.switch_modes(elements[2])
                if elements[1] == "add":
                    if elements[2] == "infantry":
                        self.environment.placing = elements[3]
                    elif elements[2] == "building":
                        self.environment.placing = "{}_{}".format(elements[2], elements[3])
                    else:
                        self.environment.placing = elements[2]

                if elements[1] == "effect":
                    self.environment.placing = "{}_{}".format(elements[1], elements[2])

                if elements[1] == "team":
                    self.environment.team = int(elements[2])

            self.messages = []

    def mouse_ray(self, position, hit_string):
        x, y = position

        camera = self.camera
        screen_vect = camera.getScreenVect(x, y)
        target_position = camera.worldPosition.copy() - screen_vect
        mouse_hit = camera.rayCast(target_position, camera, 50.0, hit_string, 0, 1, 0)

        return mouse_hit

    def process(self):
        pass

    def end(self):
        self.cursor.endObject()
        self.debug_text.endObject()
        self.printer.endObject()
        self.mouse_over_text.endObject()

        for health_bar_key in self.health_bars:
            health_bar = self.health_bars[health_bar_key]
            health_bar.terminate()

        for button in self.buttons:
            button.terminate()

        for action_button in self.action_buttons:
            action_button.terminate()


class EditorInterface(UiModule):

    def __init__(self, environment):
        super().__init__(environment)

    def add_editor_buttons(self):
        for i in range(13):
            spawn = self.cursor_plane
            ox = 0.9
            oy = 0.73
            button = Button(self, spawn, "button_terrain_{}".format(i), ox - (i * 0.1), oy, 0.1, "", "")
            self.buttons.append(button)

    def process(self):
        pass


class MissionInterface(UiModule):

    def __init__(self, environment):
        super().__init__(environment)
        self.painter_dict = self.environment.ai_painter_dict

    def add_editor_buttons(self):

        painter_dict = self.environment.ai_painter_dict
        painter_keys = sorted(p_key for p_key in painter_dict)

        objective_buttons = []
        modifier_buttons = []
        color_buttons = []
        map_buttons = []

        for paint_key in painter_keys:
            elements = paint_key.split("_")
            if elements[0] == "OBJECTIVE":
                objective_buttons.append(paint_key)
            if elements[0] == "MODIFIER":
                modifier_buttons.append(paint_key)
            if elements[0] == "COLOR":
                color_buttons.append(paint_key)
            if elements[0] == "MAP":
                map_buttons.append(paint_key)

        x = 0
        y = 0

        x, y = self.add_list(color_buttons, x, y)
        y = 0
        x += 1
        x, y = self.add_list(objective_buttons, x, y)
        y = 0
        x += 1
        x, y = self.add_list(modifier_buttons, x, y)
        self.add_list(map_buttons, x, y)

    def add_list(self, key_list, x, y):

        x_base = 0.9
        y_base = 0.73

        x_amount = 0.2
        y_amount = 0.18

        for i in range(len(key_list)):
            spawn = self.cursor_plane

            ox = x_base - (x * x_amount)
            oy = y_base - (y * y_amount)
            button = Button(self, spawn, "button_{}".format(key_list[i]), ox, oy, 0.10, "", "")
            self.buttons.append(button)

            if y > 8:
                x += 1
                y = 0
            else:
                y += 1

        return x, y

    def process(self):
        pass


class AiPainterInterface(UiModule):

    def __init__(self, environment):
        super().__init__(environment)
        self.painter_dict = self.environment.ai_painter_dict

    def add_editor_buttons(self):

        painter_dict = self.environment.ai_painter_dict
        painter_keys = sorted(p_key for p_key in painter_dict)

        agent_buttons = []
        behavior_buttons = []

        for paint_key in painter_keys:
            elements = paint_key.split("_")
            if elements[0] == "AGENT":
                agent_buttons.append(paint_key)
            elif elements[0] == "BEHAVIOR":
                behavior_buttons.append(paint_key)

        x = 0
        y = 0

        x, y = self.add_list(agent_buttons, x, y)
        x, y = self.add_list(behavior_buttons, x, y)

    def add_list(self, key_list, x, y):

        x_base = 0.9
        y_base = 0.73

        x_amount = 0.2
        y_amount = 0.18

        for i in range(len(key_list)):
            spawn = self.cursor_plane

            ox = x_base - (x * x_amount)
            oy = y_base - (y * y_amount)
            button = Button(self, spawn, "button_{}".format(key_list[i]), ox, oy, 0.10, "", "")
            self.buttons.append(button)

            if y > 5:
                x += 1
                y = 0
            else:
                y += 1

        return x, y

    def process(self):
        pass


class PlacerInterface(UiModule):

    def __init__(self, environment):
        super().__init__(environment)

    def add_editor_buttons(self):

        vehicle_buttons = ["add_artillery", "add_anti tank gun", "add_scout car", "add_medium tank", "add_light tank",
                   "add_truck", "add_assault gun"]

        infantry_buttons = ["add_infantry_rm", "add_infantry_sm", "add_infantry_hg",
                   "add_infantry_ht", "add_infantry_pt", "add_infantry_hg", "add_infantry_mk",
                   "add_infantry_gr", "add_infantry_mg", "add_infantry_at", "add_infantry_en", "add_infantry_cm"]

        building_buttons = ["add_building_1", "add_building_2", "add_building_3"]

        team_buttons = ["team_1", "team_2"]

        effect_buttons = ["effect_smoke", "effect_mines"]

        ox = 0.9
        oy = 0.73

        for i in range(len(vehicle_buttons)):
            button_name = vehicle_buttons[i]
            spawn = self.cursor_plane
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.1), oy, 0.1, "", "")
            self.buttons.append(button)

        oy -= 0.2

        for i in range(len(infantry_buttons)):
            button_name = infantry_buttons[i]
            spawn = self.cursor_plane
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.1), oy, 0.1, "", "")
            self.buttons.append(button)

        oy -= 0.2

        for i in range(len(building_buttons)):
            button_name = building_buttons[i]
            spawn = self.cursor_plane
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.1), oy, 0.1, "", "")
            self.buttons.append(button)

        oy -= 0.2

        for i in range(len(team_buttons)):
            button_name = team_buttons[i]
            spawn = self.cursor_plane
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.1), oy, 0.1, "", "")
            self.buttons.append(button)

        oy -= 0.2

        for i in range(len(effect_buttons)):
            button_name = effect_buttons[i]
            spawn = self.cursor_plane
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.1), oy, 0.1, "", "")
            self.buttons.append(button)


class GamePlayInterface(UiModule):

    def __init__(self, environment):
        super().__init__(environment)

        self.environment.turn_manager.update_targeting_data()

    def handle_health_bars(self):

        for agent_key in self.environment.agents:
            agent = self.environment.agents[agent_key]

            if agent.on_screen and agent.visible and not agent.has_effect("DYING"):
                if agent_key not in self.health_bars:
                    self.health_bars[agent_key] = HealthBar(self, agent_key)

        next_generation = {}

        for health_bar_key in self.health_bars:
            health_bar = self.health_bars[health_bar_key]

            if health_bar.owner.on_screen and not health_bar.ended:
                health_bar.update()
                next_generation[health_bar_key] = health_bar
            else:
                health_bar.terminate()

        self.health_bars = next_generation


class EnemyInterface(GamePlayInterface):

    def __init__(self, environment):
        super().__init__(environment)
        self.team = 2

    def handle_elements(self):
        self.context = "WAITING"


class PlayerInterface(GamePlayInterface):

    def __init__(self, environment):
        super().__init__(environment)

    def in_game_context(self):

        context = "NONE"
        tile_over = self.environment.tile_over

        if self.selected_unit:
            agent = self.environment.agents[self.selected_unit]
            current_action = agent.active_action

            action_check = agent.check_action_valid(current_action, tile_over)
            if action_check:
                status = action_check[0]
                target_status = static_dicts.ui_results[status]
                context = target_status[0]
                self.environment.printing_text = target_status[1]

        self.context = context

    def get_selected_unit(self):
        return self.environment.turn_manager.active_agent

    def add_buttons(self):

        modes = ["GAMEPLAY", "EDITOR", "PLACER", "MISSION", "FLAGS", "EXIT"]

        for i in range(len(modes)):
            mode = modes[i]
            spawn = self.cursor_plane
            ox = 0.9
            oy = 0.9
            button = Button(self, spawn, "button_mode_{}".format(mode), ox - (i * 0.1), oy, 0.1, "", "")
            self.buttons.append(button)

        if self.selected_unit:
            agent = self.environment.agents[self.selected_unit]
            action_dict = agent.get_stat("action_dict")
            free_actions = agent.get_stat("free_actions")

            # radio_points, orders, hull, turret

            all_action_keys = [key for key in action_dict]
            all_action_keys.sort()

            action_keys = [[], [], [], [], []]

            for action_key in all_action_keys:
                action = action_dict[action_key]
                null = False

                if action["triggered"]:
                    null = True

                if free_actions < action["action_cost"]:
                    null = True

                if not agent.has_effect("HAS_RADIO") and action["radio_points"] > 0:
                    null = True

                if agent.check_jammed(action_key):
                    null = True

                if agent.out_of_ammo(action_key):
                    null = True

                if action["target"] == "MOVE":
                    action_keys[4].append([action_key, null])
                elif action["radio_points"] > 0 and action["action_type"] == "ORDERS":
                    action_keys[0].append([action_key, null])
                elif action["action_type"] == "ORDERS":
                    action_keys[1].append([action_key, null])
                else:
                    if "turret" in action["weapon_location"]:
                        action_keys[3].append([action_key, null])
                    else:
                        action_keys[2].append([action_key, null])

            ox = 0.9
            oy = 0.7

            for x in range(len(action_keys)):
                for y in range(len(action_keys[x])):
                    spawn = self.cursor_plane

                    current_action_key, button_null = action_keys[x][y]

                    action = action_dict[current_action_key]
                    icon = "order_{}".format(action["icon"])

                    message = "action_set${}".format(current_action_key)

                    button = Button(self, spawn, icon, ox - (x * 0.1), oy - (y * 0.15), 0.1, message, "", button_null)
                    self.action_buttons.append(button)

    def process_messages(self):

        if self.messages:
            message_content = self.messages[0]
            elements = message_content.split("_")

            if elements[0] == "button":
                if elements[1] == "mode":
                    self.environment.switch_modes(elements[2])

            if elements[0] == "action":
                action_elements = message_content.split("$")
                agent = self.environment.agents[self.selected_unit]
                agent.set_active_action(action_elements[1])

            self.messages = []

    def process(self):

        if self.selected_unit:
            agent = self.environment.agents[self.selected_unit]
            action = agent.get_stat("action_dict")[agent.active_action]
            weapon = ""
            weapon_stats_string = ""

            if action["action_type"] == "WEAPON":
                weapon = "/ {} {}".format(action["weapon_name"], action["weapon_location"])
                weapon_stats = action["weapon_stats"]
                weapon_stats_string = "\npwr:{} / acr:{} / pen:{} / dmg:{} / shk:{} / sht: {}".format(
                    weapon_stats["power"], weapon_stats["accuracy"], weapon_stats["penetration"],
                    weapon_stats["damage"], weapon_stats["shock"], weapon_stats["shots"])

            action_string = "\ncst:{} / cyc:{} / mxc:{} / tgr:{}".format(action["action_cost"], action["recharged"],
                                                                         action["recharge_time"], action["triggered"])

            tile = self.environment.tile_over

            action_text = "{}  {}{}{}{}".format(tile, action["action_name"], weapon, weapon_stats_string, action_string)
            self.debug_text["Text"] = "{}\n{}".format(self.debug_text["Text"], action_text)
