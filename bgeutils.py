import mathutils
import bge
import json

vinland_version = 0.1

def get_key(position):
    return "{}${}".format(int(round(position[0])), int(round(position[1])))


def get_loc(key):
    return [int(v) for v in key.split("$")]


def position_to_location(position):

    def clamp(i):
        return max(0, min(31, int(round(i))))

    return [clamp(v) for v in position][:2]


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


def load_settings():
    in_path = bge.logic.expandPath("//saves/saves.txt")
    with open(in_path, "r") as infile:
        bge.logic.globalDict = json.load(infile)

    if not bge.logic.globalDict.get("version"):
        bge.logic.globalDict["version"] = vinland_version
        bge.logic.globalDict["profiles"] = {}
        add_new_profile("default_profile")
        save_settings()

    bge.logic.globalDict["mode_change"] = False


def save_settings():
    out_path = bge.logic.expandPath("//saves/saves.txt")
    with open(out_path, "w") as outfile:
        json.dump(bge.logic.globalDict, outfile)


def add_new_profile(profile_name):

    default_profile = {"version": vinland_version, "volume": 1.0, "sensitivity": 1.0, "saved_map": None}
    bge.logic.globalDict["profiles"][profile_name] = default_profile
    bge.logic.globalDict["active_profile"] = profile_name

