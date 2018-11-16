import bge
import bgeutils
import static_dicts
import math
import ui_canvas

ui_colors = {"GREEN": [0.1, 0.8, 0.0, 1.0],
             "OFF_GREEN": [0.02, 0.1, 0.0, 1.0],
             "RED": [1.0, 0.0, 0.0, 1.0],
             "BLUE": [0.1, 0.1, 1.0, 1.0],
             "OFF_BLUE": [0.0, 0.05, 0.1, 1.0],
             "OFF_RED": [0.1, 0.0, 0.0, 1.0],
             "YELLOW": [0.5, 0.5, 0.0, 1.0],
             "OFF_YELLOW": [0.05, 0.04, 0.0, 1.0],
             "ORANGE": [0.7, 0.2, 0.0, 1.0],
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
        self.status_adder = bgeutils.get_ob("status_adder", self.box.children)
        self.status_icons = []

        self.action_count.resolution = 20
        self.timer = 0
        self.categories = self.get_categories()

        self.pips = {}
        self.add_pips()

    def update(self):
        self.update_screen_position()
        self.update_info_string()

    def update_info_string(self):
        self.action_count["Text"] = ""

        if self.owner.get_stat("team") != 1:
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
             [int(self.owner.get_stat("hps") * 0.1),
              int((self.owner.get_stat("hps") - self.owner.get_stat("hp_damage")) * 0.1)], "GREEN"]]

        return categories

    def clear_status_icons(self):
        for icon in self.status_icons:
            icon.endObject()
        self.status_icons = []

    def update_status(self):

        self.clear_status_icons()

        status_dict = static_dicts.status_icons
        status = {}

        for effect in self.owner.get_stat("effects"):
            if effect in status_dict:
                icon, value = status_dict[effect]
                if value > 0:
                    if status.get(icon, - 2) < value:
                        status[icon] = value

        status_keys = sorted([key for key in status])
        adder = self.status_adder

        value_dict = {4: "BLUE",
                      1: "GREEN",
                      2: "YELLOW",
                      3: "ORANGE",
                      5: "RED"}

        for i in range(len(status_keys)):
            status_key = status_keys[i]
            value = status[status_key]
            icon = adder.scene.addObject("effect_icons_{}".format(status_key), adder, 0)
            self.status_icons.append(icon)
            icon.setParent(adder)
            icon.localPosition.x += i * 0.011
            icon.color = ui_colors[value_dict[value]]

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
                pip.visible = False

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

    def update_visual_feedback(self):
        if self.timer > 12:
            self.update_pips()
            self.update_cover()
            self.update_status()
            self.timer = 0
        else:
            self.timer += 1

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
                self.update_visual_feedback()
            else:
                invalid = True

        if invalid:
            self.ended = True
            self.box.localScale = [0.0, 0.0, 0.0]

    def terminate(self):
        self.box.endObject()


class Button(object):

    def __init__(self, manager, spawn, name, x, y, scale, message, mouse_over_text, null=False, extra_cost=False):
        self.manager = manager
        self.spawn = spawn
        self.name = name
        self.message = message
        if not mouse_over_text:
            self.mouse_over_text = name
        else:
            self.mouse_over_text = mouse_over_text

        self.on_color = [1.0, 1.0, 1.0, 1.0]
        self.off_color = [0.05, 0.05, 0.05, 1.0]

        x, y = self.get_screen_placement(x, y)

        self.box = self.add_box(x, y, spawn, scale)
        self.extra_cost_box = None
        if extra_cost:
            self.extra_cost_box = self.add_extra_cost(x, y, spawn, scale)

        self.pressed = False
        self.timer = 20

        self.null = null
        if self.null:
            self.box.color = self.off_color

    def add_extra_cost(self, x, y, spawn, scale):
        box = spawn.scene.addObject("extra_order_cost", spawn, 0)
        box["owner"] = self
        box.setParent(spawn)
        box.localPosition = [x, y, 0.02]
        box.localScale = [scale, scale, scale]
        return box

    def add_box(self, x, y, spawn, scale):
        box = spawn.scene.addObject(self.name, spawn, 0)
        box["owner"] = self
        box.setParent(spawn)
        box.localPosition = [x, y, 0.02]
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
        if self.extra_cost_box:
            self.extra_cost_box.endObject()


class BasicInterface(object):

    def __init__(self, environment):
        self.environment = environment
        self.cursor_plane = bgeutils.get_ob("cursor_plane", self.environment.scene.objects)
        self.camera = self.environment.scene.active_camera
        self.background = ui_canvas.UserInterfaceCanvas(self, self.environment)

    def mouse_ray(self, position, hit_string):
        x, y = position

        camera = self.camera
        screen_vect = camera.getScreenVect(x, y)
        target_position = camera.worldPosition.copy() - screen_vect
        mouse_hit = camera.rayCast(target_position, camera, 50.0, hit_string, 0, 1, 0)

        return mouse_hit

    def update(self):
        self.background.update()
        self.process()

    def process(self):
        pass

    def end(self):
        self.background.terminate()


class LoadingInterface(BasicInterface):

    def __init__(self, environment):
        super().__init__(environment)
        self.loading_text = self.add_loading_text()
        self.loading_object = self.add_loading_object()
        self.timer = 0.0

    def add_loading_object(self):
        mouse_hit = self.mouse_ray((0.25, 0.5), "cursor_plane")

        if mouse_hit[0]:
            location = mouse_hit[1]
            normal = mouse_hit[2]
            loader = self.environment.add_object("loading_progress")
            loader.worldPosition = location
            loader.worldOrientation = normal.to_track_quat("Z", "Y")
            loader.setParent(self.cursor_plane)

            normal.length = 0.3
            loader.worldPosition += normal

            return loader

        return None

    def add_loading_text(self):
        mouse_hit = self.mouse_ray((0.3, 0.5), "cursor_plane")

        if mouse_hit[0]:
            location = mouse_hit[1]
            normal = mouse_hit[2]
            loading_text = self.environment.add_object("main_debug_text")
            loading_text.worldPosition = location
            loading_text.worldOrientation = normal.to_track_quat("Z", "Y")
            loading_text.setParent(self.cursor_plane)
            loading_text.localScale *= 0.6
            loading_text.resolution = 8
            loading_text["Text"] = "LOADING!"

            normal.length = 0.3
            loading_text.worldPosition += normal

            return loading_text

        return None

    def process(self):

        if not self.loading_text:
            self.loading_text = self.add_loading_text()
        elif not self.loading_object:
            self.loading_object = self.add_loading_object()
        else:
            assets = self.environment.assets
            total = len(assets)

            self.loading_text["Text"] = "LOADING..."

            if total > 0 and assets[0]:
                self.loading_text["Text"] = "LOADING ... {}".format(assets[0].libraryName[12:])
            else:
                self.loading_text["Text"] = "LOADED!"

            self.loading_object.applyRotation([0.0, 0.0, 0.2], True)

            time = math.sin(self.timer)
            self.timer += 6.0
            self.loading_object.color = [time + 1.0, time + 3.0, time - 1.0, 1.0]

    def end(self):
        self.background.terminate()
        self.loading_text.endObject()
        self.loading_object.endObject()


class UiModule(BasicInterface):

    def __init__(self, environment):

        super().__init__(environment)

        self.cursor = self.add_cursor()
        self.messages = []
        self.buttons = []
        self.action_buttons = []
        self.focus = False
        self.context = "NONE"
        self.debug_text = self.add_debug_text([0.1, 0.88])
        self.printer = self.add_debug_text([0.1, 0.1])
        self.mouse_over_text = self.add_debug_text([0.1, 0.5])
        self.mouse_over_text.localScale *= 0.5
        self.tool_tip = self.add_tool_tip()

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

    def add_tool_tip(self):
        tool_tip = self.environment.add_object("main_debug_text")
        tool_tip.setParent(self.cursor)
        tool_tip.worldPosition = self.cursor.worldPosition.copy()
        tool_tip.localScale = [0.02, 0.02, 0.02]
        tool_tip.color = ui_colors["RED"]
        tool_tip.localPosition.y -= 0.04
        tool_tip.localPosition.x -= 0.03
        tool_tip.resolution = 12
        tool_tip["Text"] = ""

        return tool_tip

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

    def process(self):
        self.debug_text["Text"] = self.environment.debug_text
        self.printer["Text"] = self.environment.printing_text
        self.sub_process()

        mouse_hit = self.mouse_ray(self.environment.input_manager.virtual_mouse, "cursor_plane")

        if mouse_hit[0]:
            location = mouse_hit[1]
            normal = mouse_hit[2]
            self.cursor.worldPosition = location
            self.cursor.worldOrientation = normal.to_track_quat("Z", "Y")

            normal.length = 0.05
            self.cursor.worldPosition += normal.copy()

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
                self.handle_tool_tips(ui_hit[0])
                self.context = "SELECT"
            else:
                self.focus = False
                self.handle_tool_tips(ui_hit[0])
                self.in_game_context()

        for button in self.buttons:
            button.update()

        for action_button in self.action_buttons:
            action_button.update()

        self.process_messages()

    def in_game_context(self):
        self.context = "NONE"

    def handle_tool_tips(self, hit_button):
        text = ""
        if hit_button:
            if hit_button["owner"]:
                text = hit_button["owner"].mouse_over_text
                text = text.split("_")
                text = "\n".join(text).title()

        self.tool_tip["Text"] = text

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
                if elements[1] == "rotation":
                    self.environment.set_rotation(int(elements[2]))
                if elements[1] == "filter":
                    self.environment.set_filter(elements[2])

                if elements[1] == "add":
                    if elements[2] == "infantry":
                        self.environment.placing_type = "infantry"
                        self.environment.placing = elements[3]
                    elif elements[2] == "building":
                        self.environment.placing_type = "building"
                        self.environment.placing = "_".join(elements[3:])
                    else:
                        self.environment.placing_type = "vehicle"
                        placing = "_".join(elements[2:])
                        self.environment.placing = placing

                if elements[1] == "effect":
                    self.environment.placing = "{}_{}".format(elements[1], elements[2])

                if elements[1] == "team":
                    self.environment.set_team(int(elements[2]))

            self.messages = []

    def sub_process(self):
        pass

    def end(self):
        self.background.terminate()
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

    def sub_process(self):
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

    def sub_process(self):
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

    def sub_process(self):
        pass


class PlacerInterface(UiModule):

    def __init__(self, environment):
        super().__init__(environment)

    def get_vehicle_buttons(self):

        team = int(self.environment.team)
        vehicles = self.environment.vehicle_dict

        if team == 1:
            search_term = "VIN"
        else:
            search_term = "HRR"

        vehicle_list = [key for key in vehicles if search_term in key]

        guns = []
        tanks = []

        for vehicle in vehicle_list:
            vehicle_details = vehicles[vehicle]
            if vehicle_details["drive_type"] == "GUN_CARRIAGE":
                guns.append("add_{}".format(vehicle))
            else:
                tanks.append("add_{}".format(vehicle))

        return guns, tanks

    def get_building_buttons(self):

        buildings = self.environment.building_dict
        search_term = self.environment.filter

        building_list = ["add_building_{}".format(key) for key in buildings if buildings[key]["building_type"] == search_term]
        building_list = sorted(building_list)

        return building_list

    def add_editor_buttons(self):

        guns, tanks = self.get_vehicle_buttons()

        vehicle_buttons = guns

        vehicle_buttons_2 = tanks

        infantry_buttons_1 = ["add_infantry_rm", "add_infantry_sm", "add_infantry_hg",
                              "add_infantry_ht", "add_infantry_pt", "add_infantry_mk"]

        infantry_buttons_2 = ["add_infantry_gr", "add_infantry_mg", "add_infantry_at", "add_infantry_en",
                              "add_infantry_cm"]

        buildings = self.get_building_buttons()
        split_point = int(len(buildings) * 0.5)

        building_buttons_1 = buildings[split_point:]
        building_buttons_2 = buildings[:split_point]

        team_buttons = ["team_1", "team_2", "filter_village", "filter_military", "filter_misc", "filter_town"]

        effect_buttons = ["effect_smoke", "effect_mines"]

        rotation_buttons = ["rotation_{}".format(n) for n in range(8)]

        ox = 0.9
        oy = 0.73

        for i in range(len(vehicle_buttons)):
            button_name = vehicle_buttons[i]
            spawn = self.cursor_plane
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.1), oy, 0.1, "", "")
            self.buttons.append(button)

        oy -= 0.2

        for i in range(len(vehicle_buttons_2)):
            button_name = vehicle_buttons_2[i]
            spawn = self.cursor_plane
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.1), oy, 0.1, "", "")
            self.buttons.append(button)

        oy -= 0.2

        for i in range(len(infantry_buttons_1)):
            button_name = infantry_buttons_1[i]
            spawn = self.cursor_plane
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.2), oy, 0.1, "", "")
            self.buttons.append(button)

        oy -= 0.2

        for i in range(len(infantry_buttons_2)):
            button_name = infantry_buttons_2[i]
            spawn = self.cursor_plane
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.2), oy, 0.1, "", "")
            self.buttons.append(button)

        oy -= 0.2

        for i in range(len(building_buttons_1)):
            button_name = building_buttons_1[i]
            spawn = self.cursor_plane
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.1), oy, 0.1, "", "")
            self.buttons.append(button)

        oy -= 0.2

        for i in range(len(building_buttons_2)):
            button_name = building_buttons_2[i]
            spawn = self.cursor_plane
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.1), oy, 0.1, "", "")
            self.buttons.append(button)

        oy -= 0.2

        for i in range(len(team_buttons)):
            button_name = team_buttons[i]
            spawn = self.cursor_plane
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.2), oy, 0.1, "", "")
            self.buttons.append(button)

        oy -= 0.2

        for i in range(len(effect_buttons)):
            button_name = effect_buttons[i]
            spawn = self.cursor_plane
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.2), oy, 0.1, "", "")
            self.buttons.append(button)

        oy -= 0.2

        for i in range(len(rotation_buttons)):
            button_name = rotation_buttons[i]
            spawn = self.cursor_plane
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.1), oy, 0.1, "", "")
            self.buttons.append(button)


class GamePlayInterface(UiModule):

    def __init__(self, environment):
        super().__init__(environment)
        self.environment.turn_manager.update_targeting_data()

    def handle_health_bars(self):

        next_generation = {}

        for health_bar_key in self.health_bars:
            health_bar = self.health_bars[health_bar_key]

            if health_bar.owner.on_screen and not health_bar.ended:
                health_bar.update()
                next_generation[health_bar_key] = health_bar
            else:
                health_bar.terminate()

        self.health_bars = next_generation

        for agent_key in self.environment.agents:
            agent = self.environment.agents[agent_key]

            if agent.on_screen and agent.visible and not agent.has_effect("DYING"):
                if agent_key not in self.health_bars:
                    self.health_bars[agent_key] = HealthBar(self, agent_key)


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

    def check_valid_action(self, agent, action_key):
        action_dict = agent.get_stat("action_dict")
        free_actions = agent.get_stat("free_actions")

        action = action_dict[action_key]

        if action["triggered"]:
            return False

        if free_actions < action["action_cost"]:
            return False

        if action["radio_points"] > 0:
            if not agent.has_effect("HAS_RADIO"):
                return False

            elif agent.has_effect("RADIO_JAMMING"):
                return False

        if agent.check_jammed(action_key):
            return False

        if agent.out_of_ammo(action_key):
            return False

        invalid_combinations = [["REMOVE_JAMMING", "RADIO_JAMMED"], ["CLEAR_JAM", "JAMMED"]]
        for action_effect, effect_check in invalid_combinations:
            if action["effect"] == action_effect:
                if not agent.has_effect(effect_check):
                    return False

        if action["effect"] == "REINFORCEMENT":
            if agent.get_stat("hp_damage") == 0:
                return False

        if action["requires_supply"]:
            if not agent.check_has_supply():
                return False

        return True

    def add_buttons(self):

        modes = ["GAMEPLAY", "EDITOR", "PLACER", "MISSION", "FLAGS", "EXIT"]

        for i in range(len(modes)):
            mode = modes[i]
            spawn = self.cursor_plane
            ox = 0.1
            oy = 0.9
            button = Button(self, spawn, "button_mode_{}".format(mode), ox - (i * 0.1), oy, 0.1, "", "")
            self.buttons.append(button)

        if self.selected_unit:
            agent = self.environment.agents[self.selected_unit]
            action_dict = agent.get_stat("action_dict")

            all_action_keys = [key for key in action_dict]
            all_action_keys.sort()

            action_keys = [[], [], [], [], [], []]

            for action_key in all_action_keys:
                valid_action = self.check_valid_action(agent, action_key)

                action = action_dict[action_key]

                if valid_action:
                    if action["target"] == "MOVE":
                        action_keys[5].append(action_key)
                    elif action["radio_points"] > 0 and action["target"] == "SELF":
                        action_keys[0].append(action_key)
                    elif action["target"] == "SELF":
                        action_keys[1].append(action_key)
                    elif action["action_type"] == "ORDERS":
                        action_keys[2].append(action_key)
                    else:
                        if "turret" in action["weapon_location"]:
                            action_keys[4].append(action_key)
                        else:
                            action_keys[3].append(action_key)

            ox = 0.86
            oy = 0.76

            for x in range(len(action_keys)):
                for y in range(len(action_keys[x])):
                    spawn = self.cursor_plane

                    current_action_key = action_keys[x][y]

                    extra_cost = False
                    action = action_dict[current_action_key]
                    if action["action_cost"] > 1:
                        extra_cost = True
                    icon = "order_{}".format(action["icon"])
                    tool_tip = action["action_name"]

                    message = "action_set${}".format(current_action_key)

                    button = Button(self, spawn, icon, ox - (x * 0.06), oy - (y * 0.11), 0.065, message, tool_tip,
                                    extra_cost=extra_cost)
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
                action_dict = agent.get_stat("action_dict")
                target_action = action_dict[action_elements[1]]
                if target_action["target"] == "SELF":
                    agent.quick_trigger(action_elements[1])
                else:
                    agent.set_active_action(action_elements[1])

            self.messages = []

    def sub_process(self):

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
