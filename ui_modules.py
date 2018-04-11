import bge
import bgeutils

ui_colors = {"GREEN": [0.1, 0.8, 0.0, 1.0],
             "OFF_GREEN": [0.05, 0.2, 0.0, 1.0],
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

        self.ended = False

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
            self.action_count["Text"] = self.owner.get_stat("free_actions")
            self.update_screen_position()

    def get_categories(self):
        categories = [["armor", self.armor_adder, self.owner.get_stat("armor"), "BLUE"],
                      ["shock", self.shock_adder, self.owner.get_stat("shock"), "RED"],
                      ["health", self.health_adder,
                       max(1, int((self.owner.get_stat("hps") - self.owner.get_stat("hp_damage")) * 0.1)), "GREEN"],
                      ["damage", self.damage_adder, self.owner.get_stat("drive_damage"), "YELLOW"]]

        return categories

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

    def update_pips(self):

        self.categories = self.get_categories()

        for category in self.categories:
            name, adder, stat, color = category

            for i in range(10):

                if name == "armor":
                    pip_stat = stat[0]
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

        screen_position = camera.getScreenPosition(position)
        mouse_hit = self.manager.mouse_ray(screen_position, "cursor_plane")
        if mouse_hit[0]:
            self.box.localScale = [1.0, 1.0, 1.0]
            plane, screen_position, screen_normal = mouse_hit
            self.box.worldPosition = screen_position
            self.box.worldOrientation = screen_normal.to_track_quat("Z", "Y")
            self.update_pips()
        else:
            self.ended = True
            self.box.localScale = [0.0, 0.0, 0.0]

    def terminate(self):
        self.box.endObject()


class Button(object):

    def __init__(self, manager, spawn, name, x, y, scale, message, mouse_over_text):
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
        self.debug_text = self.add_debug_text()
        self.health_bars = {}

        self.selected_unit = self.get_selected_unit()
        self.team = 1
        self.cool_off = 30

        self.add_buttons()
        self.add_editor_buttons()

    def get_selected_unit(self):
        return None

    def add_editor_buttons(self):
        pass

    def add_buttons(self):

        modes = ["GAMEPLAY", "EDITOR", "PLACER", "EXIT"]

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

    def add_debug_text(self):
        mouse_hit = self.mouse_ray([0.1, 0.9], "cursor_plane")

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
        self.process()

        mouse_hit = self.mouse_ray(self.environment.input_manager.virtual_mouse, "cursor_plane")

        if mouse_hit[0]:
            location = mouse_hit[1]
            normal = mouse_hit[2]
            self.cursor.worldPosition = location
            self.cursor.worldOrientation = normal.to_track_quat("Z", "Y")

        self.handle_elements()
        self.set_cursor()

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
        else:
            self.cursor.replaceMesh("standard_cursor")

    def process_messages(self):

        if self.messages:
            print(self.messages, "msg_list")

            message_content = self.messages[0]
            elements = message_content.split("_")

            if elements[0] == "button":
                if elements[1] == "terrain":
                    self.environment.paint = int(elements[2])
                if elements[1] == "mode":
                    self.environment.switch_modes(elements[2])
                if elements[1] == "add":
                    if elements[2] == "infantry":
                        self.environment.placing = elements[3]
                    else:
                        self.environment.placing = elements[2]
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


class GamePlayInterface(UiModule):

    def __init__(self, environment):
        super().__init__(environment)

    def handle_health_bars(self):

        for agent_key in self.environment.agents:
            agent = self.environment.agents[agent_key]
            # TODO add some stuff to validate healthbars

            if agent.on_screen:
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


class PlacerInterface(UiModule):

    def __init__(self, environment):
        super().__init__(environment)

    def add_editor_buttons(self):

        buttons = ["add_artillery", "add_anti tank gun", "add_scout car", "add_medium tank", "add_light tank",
                   "add_truck", "add_assault gun", "add_infantry_rm", "add_infantry_sm",
                   "add_infantry_mg", "add_infantry_at", "add_infantry_en", "add_infantry_cm"]

        for i in range(len(buttons)):
            button_name = buttons[i]
            spawn = self.cursor_plane
            ox = 0.9
            oy = 0.73
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.1), oy, 0.1, "", "")
            self.buttons.append(button)

        team_buttons = ["team_1", "team_2"]

        for i in range(len(team_buttons)):
            button_name = team_buttons[i]
            spawn = self.cursor_plane
            ox = 0.9
            oy = 0.56
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.1), oy, 0.1, "", "")
            self.buttons.append(button)


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
        target_type = None
        mouse_over_type = None
        x, y = self.environment.tile_over
        lit = self.environment.player_visibility.lit(x, y)
        max_actions = 0

        if self.selected_unit:
            agent = self.environment.agents[self.selected_unit]
            max_actions = agent.get_stat("free_actions")
            busy = self.environment.turn_manager.busy

            if not busy:
                current_action = agent.get_current_action()
                target_type = current_action["target"]
                mouse_over_tile = self.environment.get_tile(self.environment.tile_over)

                occupier = mouse_over_tile["occupied"]

                if occupier:
                    target = self.environment.agents[occupier]
                    if target.get_stat("agent_id") == self.selected_unit:
                        mouse_over_type = "SELF"

                    elif target.get_stat("team") == 1:
                        mouse_over_type = "FRIEND"

                    else:
                        mouse_over_type = "ENEMY"
                else:

                    mouse_over_type = "MAP"

            else:
                context = "WAITING"

        if max_actions < 1:
            if mouse_over_type == "FRIEND":
                context = "SELECT"
            elif mouse_over_type == "ENEMY" and lit > 0:
                context = "NO_TARGET"
            else:
                context = "CYCLE"

        elif target_type == "MOVE":
            if mouse_over_type == "FRIEND":
                context = "SELECT"
            elif mouse_over_type != "MAP":
                context = "NO_TARGET"

        elif target_type == "SELF":
            if mouse_over_type == "SELF":
                context = "SELECT"
            elif mouse_over_type == "FRIEND":
                context = "SELECT"
            elif mouse_over_type != "MAP":
                context = "NO_TARGET"

        elif target_type == "ENEMY":
            if mouse_over_type == "ENEMY":
                if lit == 2:
                    context = "TARGET"
                else:
                    context = "NO_TARGET"
            elif mouse_over_type == "FRIEND":
                context = "SELECT"
            elif mouse_over_type != "MAP":
                context = "NO_TARGET"

        elif target_type == "FRIEND":
            if mouse_over_type == "FRIEND":
                context = "TARGET"
            elif mouse_over_type == "SELF":
                context = "TARGET"
            elif target_type == "ENEMY":
                context = "NO_TARGET"

        elif target_type == "MAP":
            if mouse_over_type == "FRIEND":
                context = "SELECT"
            elif mouse_over_type != "SELF":
                if lit > 0:
                    context = "MAP_TARGET"

        # self.debug_text["Text"] = "context:{}\ntarget_type:{}\nmouse_over{}\nlit{}".format(context, target_type, mouse_over_type, lit)
        self.context = context

    def get_selected_unit(self):
        return self.environment.turn_manager.active_agent

    def add_buttons(self):

        modes = ["GAMEPLAY", "EDITOR", "PLACER", "EXIT"]

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

            ox = 0.9
            oy = 0.7

            action_keys = [key for key in action_dict]
            action_keys.sort()

            for i in range(len(action_keys)):
                spawn = self.cursor_plane

                action_key = action_keys[i]
                action = action_dict[action_key]
                icon = "order_{}".format(action["icon"])

                if i > 6:
                    x = 1
                    y = i - 7
                else:
                    x = 0
                    y = i

                message = "action_set${}".format(action_key)

                button = Button(self, spawn, icon, ox - (x * 0.1), oy - (y * 0.15), 0.1, message, "")
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
                agent.active_action = action_elements[1]

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
                weapon_stats_string = "\npwr:{} / acr:{} / pen:{} / dmg:{} / shk:{} / sht: {}".format(weapon_stats["power"], weapon_stats["accuracy"], weapon_stats["penetration"], weapon_stats["damage"], weapon_stats["shock"], weapon_stats["shots"])

            action_text = "{}{}{}".format(action["action_name"], weapon, weapon_stats_string)

            self.debug_text["Text"] = "{}\n{}".format(self.debug_text["Text"], action_text)


