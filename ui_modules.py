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
        self.ended = False
        self.box = self.manager.environment.add_object("ui_health")
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
        self.action_count["Text"] = self.owner.get_stat("free_actions")

        self.update_screen_position()

    def get_categories(self):
        categories = [["armor", self.armor_adder, self.owner.get_stat("armor"), "BLUE"],
                      ["shock", self.shock_adder, self.owner.get_stat("shock"), "RED"],
                      ["health", self.health_adder,
                       int((self.owner.get_stat("hps") - self.owner.get_stat("hp_damage")) * 0.1), "GREEN"],
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
            if self.owner.update_health_bar:
                self.update_pips()
                self.owner.update_health_bar = False
        else:
            self.box.localScale = [0.0, 0.0, 0.0]

    def terminate(self):
        self.box.endObject()


class Button(object):

    def __init__(self, manager, spawn, name, x, y, scale):
        self.manager = manager
        self.spawn = spawn
        self.name = name

        x, y = self.get_screen_placement(x, y)

        self.box = self.add_box(x, y, spawn, scale)
        self.pressed = False
        self.triggered = False
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
                self.manager.messages.append(self.name)
                self.pressed = False
                self.reset()
            else:
                self.timer -= 1

        else:
            self.reset()

    def reset(self):
        self.timer = 5
        self.pressed = False
        self.triggered = False
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

        self.add_buttons()
        self.add_editor_buttons()

    def add_editor_buttons(self):
        pass

    def add_action_buttons(self):
        pass

    def add_buttons(self):

        modes = ["GAMEPLAY", "EDITOR", "PLACER", "EXIT"]

        for i in range(len(modes)):
            mode = modes[i]
            spawn = self.cursor_plane
            ox = 0.9
            oy = 0.9
            button = Button(self, spawn, "button_mode_{}".format(mode), ox - (i * 0.1), oy, 0.1)
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

        self.process()
        mouse_hit = self.mouse_ray(self.environment.input_manager.virtual_mouse, "cursor_plane")

        if mouse_hit[0]:
            location = mouse_hit[1]
            normal = mouse_hit[2]
            self.cursor.worldPosition = location
            self.cursor.worldOrientation = normal.to_track_quat("Z", "Y")

        self.debug_text["Text"] = self.environment.debug_text
        self.set_cursor()
        self.handle_elements()

    def handle_elements(self):
        self.add_action_buttons()
        self.handle_health_bars()

        ui_hit = self.mouse_ray(self.environment.input_manager.virtual_mouse, "ui_element")

        if ui_hit[0]:
            self.focus = True
            self.handle_buttons(ui_hit[0])
            self.context = "SELECT"
        else:
            self.focus = False
            self.context = "NONE"

        for button in self.buttons:
            button.update()

        for action_button in self.action_buttons:
            action_button.update()

        self.process_messages()

    def handle_health_bars(self):
        pass

    def handle_buttons(self, hit_button):
        if hit_button["owner"]:
            if "left_button" in self.environment.input_manager.buttons:
                hit_button["owner"].pressed = True

    def set_cursor(self):

        if self.context == "SELECT":
            self.cursor.replaceMesh("select_cursor")
        else:
            self.cursor.replaceMesh("standard_cursor")

    def process_messages(self):

        if self.messages:
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
            button = Button(self, spawn, "button_terrain_{}".format(i), ox - (i * 0.1), oy, 0.1)
            self.buttons.append(button)

    def process(self):
        pass


class GamePlayInterface(UiModule):

    def __init__(self, environment):
        super().__init__(environment)

        self.selected_agent = None

    def add_action_buttons(self):

        turn_manager = self.environment.turn_manager

        if turn_manager and turn_manager.team == 1:
            active_agent = turn_manager.active_agent

            if active_agent != self.selected_agent:
                self.selected_agent = active_agent

                for button in self.action_buttons:
                    button.terminate()
                self.action_buttons = []

                agent = self.environment.agents[active_agent]
                action_dict = agent.get_stat("action_dict")

                ox = 0.9
                oy = 0.7

                action_keys = [key for key in action_dict]
                action_keys.sort()

                for i in range(len(action_keys)):
                    spawn = self.cursor_plane

                    action = action_dict[action_keys[i]]
                    icon = "order_{}".format(action["icon"])

                    if i > 6:
                        x = 1
                        y = i - 7
                    else:
                        x = 0
                        y = i

                    button = Button(self, spawn, icon, ox - (x * 0.1), oy - (y * 0.15), 0.1)
                    self.action_buttons.append(button)

        else:
            for button in self.action_buttons:
                button.terminate()
            self.action_buttons = []

    def handle_health_bars(self):

        for agent_key in self.environment.agents:
            agent = self.environment.agents[agent_key]

            # TODO add some stuff to validate healthbars
            if agent_key not in self.health_bars:
                self.health_bars[agent_key] = HealthBar(self, agent_key)

        for health_bar_key in self.health_bars:
            health_bar = self.health_bars[health_bar_key]
            if not health_bar.ended:
                health_bar.update()
            else:
                health_bar.terminate()
                del self.health_bars[health_bar_key]


class PlacerInterface(UiModule):

    def __init__(self, environment):
        super().__init__(environment)

    def add_editor_buttons(self):

        buttons = ["add_artillery", "add_anti tank gun", "add_scout car", "add_medium tank", "add_light tank",
                   "add_truck", "add_assault gun", "add_infantry_rm", "add_infantry_st",
                   "add_infantry_mg", "add_infantry_at", "add_infantry_en", "add_infantry_cm"]

        for i in range(len(buttons)):
            button_name = buttons[i]
            spawn = self.cursor_plane
            ox = 0.9
            oy = 0.73
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.1), oy, 0.1)
            self.buttons.append(button)

        team_buttons = ["team_1", "team_2"]

        for i in range(len(team_buttons)):
            button_name = team_buttons[i]
            spawn = self.cursor_plane
            ox = 0.9
            oy = 0.56
            button = Button(self, spawn, "button_{}".format(button_name), ox - (i * 0.1), oy, 0.1)
            self.buttons.append(button)
