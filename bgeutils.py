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


def up_vector(target_vector):
    new_vector = mathutils.Vector(target_vector).to_track_quat("Y", "Z").to_matrix().to_3x3()
    return new_vector


def position_to_location(position):
    def n_clamp(i):
        # TODO set clamp to level size, maybe move to environment function
        return max(0, min(31, int(round(i))))

    return tuple([n_clamp(v) for v in position][:2])


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
    #value *= 2.6

    if maximum - minimum == 0:
        color = 0.0
    elif minimum > 0 or maximum > 0:
        color = (value - minimum) / (maximum - minimum)
    else:
        color = 0.0

    return color


def dice_probability(number, target):

    single_roll = {0: 0,
                   1: 16.67,
                   2: 33.33,
                   3: 50,
                   4: 66.67,
                   5: 83.33,
                   6: 100}

    double_roll = {1: 0,
                   2: 2.78,
                   3: 8.33,
                   4: 16.67,
                   5: 27.78,
                   6: 41.67,
                   7: 58.33,
                   8: 72.22,
                   9: 83.33,
                   10: 91.67,
                   11: 97.22,
                   12: 100}

    treble_roll = {2: 0,
                   3: 0.46,
                   4: 1.85,
                   5: 4.63,
                   6: 9.26,
                   7: 16.2,
                   8: 25.93,
                   9: 37.5,
                   10: 50,
                   11: 62.5,
                   12: 74.07,
                   13: 83.8,
                   14: 90.74,
                   15: 95.37,
                   16: 98.15,
                   17: 99.54,
                   18: 100}

    if number == 1:
        return single_roll[max(0, min(6, target))]

    elif number == 2:
        return double_roll[max(1, min(12, target))]

    elif number == 3:
        return treble_roll[max(2, min(18, target))]

    else:
        return 0
