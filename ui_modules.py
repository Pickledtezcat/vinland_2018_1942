import bge
import bgeutils


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

    def end(self):
        self.box.endObject()


class UiModule(object):

    def __init__(self, environment):

        self.environment = environment
        self.cursor_plane = bgeutils.get_ob("cursor_plane", self.environment.scene.objects)
        self.camera = self.environment.scene.active_camera
        self.cursor = self.add_cursor()
        self.messages = []
        self.buttons = []
        self.focus = False
        self.context = "NONE"
        self.debug_text = self.add_debug_text()

        self.add_buttons()
        self.add_editor_buttons()

    def add_editor_buttons(self):
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

        self.process_messages()

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

        for button in self.buttons:
            button.end()


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

