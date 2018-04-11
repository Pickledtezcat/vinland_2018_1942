import mathutils
import bge
import json
import random

vinland_version = 0.1


def get_key(position):
    return "{}${}".format(int(round(position[0])), int(round(position[1])))


def get_loc(key):
    return [int(v) for v in key.split("$")]


def track_vector(facing):
    new_vector = mathutils.Vector(facing).to_3d().to_track_quat("Y", "Z").to_matrix().to_3x3()
    return new_vector


def position_to_location(position):

    def n_clamp(i):
        return max(0, min(31, int(round(i))))

    return [n_clamp(v) for v in position][:2]


def smoothstep(x):
    return x * x * (3 - 2 * x)


def get_distance(a, b):
    vector = mathutils.Vector(b).to_3d() - mathutils.Vector(a).to_3d()
    return vector.length


def get_ob(string, ob_list):
    ob_list = [ob for ob in ob_list if string in ob]
    if ob_list:
        return ob_list[0]


def get_ob_list(string, ob_list):
    ob_list = [ob for ob in ob_list if string in ob]

    return ob_list


def interpolate_float(current, target, factor):

    return (current * (1.0 - factor)) + (target * factor)


def diagonal(location):
    x, y = location
    if abs(x) - abs(y) == 0:
        return True


def get_facing(target_vector):

    search_array = [[1, 0], [1, 1], [0, 1], [1, -1], [-1, 0], [-1, 1], [0, -1], [-1, -1]]

    best_facing = None
    best_angle = 4.0

    for facing in search_array:
        facing_vector = mathutils.Vector(facing)
        angle = target_vector.to_2d().angle(facing_vector)
        if angle < best_angle:
            best_facing = facing
            best_angle = angle

    return best_facing


def d6(number):
    total = 0
    for i in range(number):
        total += random.randint(1, 6)

    return total


def save_level(level):
    save_name = "level_{}".format(bge.logic.globalDict["active_profile"])
    bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["saved_map"] = save_name

    out_path = bge.logic.expandPath("//saves/{}.txt".format(save_name))
    with open(out_path, "w") as outfile:
        json.dump(level, outfile)
    save_settings()


def load_level():
    load_name = bge.logic.globalDict["profiles"][bge.logic.globalDict["active_profile"]]["saved_map"]

    if not load_name:
        return None

    in_path = bge.logic.expandPath("//saves/{}.txt".format(load_name))
    with open(in_path, "r") as infile:
        level = json.load(infile)

    return level


def load_settings(new=False):

    def new_settings():
        bge.logic.globalDict = {"version": vinland_version, "profiles": {}}
        add_new_profile("default_profile")
        save_settings()

    if new:
        new_settings()
        return

    in_path = bge.logic.expandPath("//saves/saves.txt")
    with open(in_path, "r") as infile:
        bge.logic.globalDict = json.load(infile)

    if not bge.logic.globalDict.get("version"):
        new_settings()

    bge.logic.globalDict["mode_change"] = False


def save_settings():
    out_path = bge.logic.expandPath("//saves/saves.txt")
    with open(out_path, "w") as outfile:
        json.dump(bge.logic.globalDict, outfile)


def add_new_profile(profile_name):

    default_profile = {"version": vinland_version, "volume": 1.0, "sensitivity": 1.0, "saved_map": None}
    bge.logic.globalDict["profiles"][profile_name] = default_profile
    bge.logic.globalDict["active_profile"] = profile_name


def rgb(minimum, maximum, value):
    minimum, maximum = float(minimum + 0.8), float(maximum - 0.8)
    ratio = 2.0 * (value - minimum) / (maximum - minimum)
    b = max(0.0, (1.0 - ratio))
    r = max(0.0, (ratio - 1.0))
    g = 1.0 - b - r

    return r, g, b


def grayscale(minimum, maximum, value):
    value *= 2.6

    if minimum > 0 or maximum > 0:
        color = (value - minimum) / (maximum - minimum)
    else:
        color = 0.0

    return color

