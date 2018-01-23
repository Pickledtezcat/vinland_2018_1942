import bge
import bgeutils


class Button(object):

    def __init__(self, manager, spawn, name, x, y, scale):
        self.manager = manager
        self.spawn = spawn
        self.name = name
        self.box = self.add_box(x, y, spawn, scale)
        self.pressed = False
        self.triggered = False
        self.timer = 20
        self.selected = False

        self.on_color = [1.0, 1.0, 1.0, 1.0]
        self.off_color = [0.2, 0.2, 0.2, 1.0]
        self.selected_color = [1.0, 0.0, 0.0, 1.0]

    def add_box(self, x, y, spawn, scale):
        box = spawn.scene.addObject(self.name, spawn, 0)
        box["owner"] = self
        box.setParent(spawn)
        box.localPosition = [x, y, -0.05]
        box.localScale = [scale, scale, scale]
        return box

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

        if self.selected:
            self.box.color = self.selected_color
        else:
            self.box.color = self.on_color

    def end(self):
        self.box.endObject()


class UiModule(object):

    def __init__(self, level):

        self.level = level
        self.cursor_plane = bgeutils.get_ob("cursor_plane", self.level.scene.objects)
        self.camera = self.level.scene.active_camera
        self.cursor = self.add_cursor()
        self.messages = []
        self.buttons = []
        self.focus = False
        self.context = "NONE"
        self.debug_text = self.add_debug_text()

    def add_cursor(self):
        cursor = self.level.scene.addObject("standard_cursor", self.level.game_object, 0)
        cursor.setParent(self.cursor_plane)
        return cursor

    def add_debug_text(self):
        mouse_hit = self.mouse_ray([0.1, 0.9], "cursor_plane")

        if mouse_hit[0]:
            location = mouse_hit[1]
            normal = mouse_hit[2]
            debug_text = self.level.scene.addObject("main_debug_text", self.level.game_object, 0)
            debug_text.worldPosition = location
            debug_text.worldOrientation = normal.to_track_quat("Z", "Y")
            debug_text.resolution = 12
            debug_text.setParent(self.cursor_plane)
            debug_text["Text"] = "debugging"

            return debug_text

        return None

    def update(self):
        mouse_hit = self.mouse_ray(self.level.input_manager.virtual_mouse, "cursor_plane")

        if mouse_hit[0]:
            location = mouse_hit[1]
            normal = mouse_hit[2]
            self.cursor.worldPosition = location
            self.cursor.worldOrientation = normal.to_track_quat("Z", "Y")

        self.process()
        self.debug_text["Text"] = self.level.debug_text
        self.set_cursor()

    def set_cursor(self):

        if self.context == "SELECT":
            self.cursor.replaceMesh("select_cursor")
        else:
            self.cursor.replaceMesh("standard_cursor")

    def process(self):
        pass

    def mouse_ray(self, position, hit_string):
        x, y = position

        camera = self.camera
        screen_vect = camera.getScreenVect(x, y)
        target_position = camera.worldPosition.copy() - screen_vect
        mouse_hit = camera.rayCast(target_position, camera, 50.0, hit_string, 0, 1, 0)

        return mouse_hit

    def end(self):
        self.cursor.endObject()
        self.debug_text.endObject()


class EditorInterface(UiModule):

    def __init__(self, level):
        super().__init__(level)

        for i in range(13):
            spawn = self.cursor_plane
            ox = -0.3
            oy = 0.2
            button = Button(self, spawn, "button_editor_{}".format(i), ox + (i * 0.055), oy, 0.1)
            self.buttons.append(button)

    def process(self):

        ui_hit = self.mouse_ray(self.level.input_manager.virtual_mouse, "ui_element")

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
            if "left_button" in self.level.input_manager.buttons:
                hit_button["owner"].pressed = True

    def process_messages(self):
        if self.messages:
            message_content = self.messages[0]
            print(message_content)

            elements = message_content.split("_")
            for button in self.buttons:
                if button.name == message_content:
                    button.selected = True
                else:
                    button.selected = False

            if elements[0] == "button":
                if elements[1] == "editor":
                    number = elements[2]
                    self.level.paint = int(number)
                    self.messages = []

    def end(self):
        super().end()

        for button in self.buttons:
            button.end()


class GamePlayInterface(UiModule):

    def __init__(self, level):
        super().__init__(level)





