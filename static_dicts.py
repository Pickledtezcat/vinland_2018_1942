import json
import bge

objective_color_dict = {1: [0.9, 0.9, 0.1, 1.0],
                        2: [0.0, 0.8, 0.05, 1.0],
                        3: [0.0, 0.14, 1.0, 1.0],
                        4: [1.0, 0.0, 0.0, 1.0],
                        5: [0.0, 1.0, 1.0, 1.0],
                        6: [1.0, 0.5, 0.0, 1.0],
                        7: [0.9, 0.0, 0.9, 1.0],
                        8: [1.0, 1.0, 1.0, 1.0],
                        9: [0.0, 0.0, 0.0, 1.0]}

ui_results = {"BUSY": ["WAITING", "Waiting..."],
              "NO_RADIO": ["NO_TARGET", "Target has no radio."],
              "NO_AMMO": ["NO_TARGET", "Out of ammo for this weapon."],
              "JAMMED": ["NO_TARGET", "Weapons jammed. Clear jam or wait."],
              "AIR_SUPPORT": ["MAP_TARGET", "Call air support to this location."],
              "INVISIBLE": ["UNKNOWN", "No line of sight or not visible."],
              "NOT_VALID": ["NOT_VALID", "Action not valid."],
              "IMMOBILE": ["NO_TARGET", "Can not move."],
              "IMPASSABLE": ["BAD_TARGET", "Location impassable."],
              "OFF_BOARD": ["BAD_TARGET", "Outside mission area."],
              "NO_ACTIONS": ["CYCLE", "Out of actions."],
              "TRIGGERED": ["CYCLE", "Action already triggered."],
              "SELECT_FRIEND": ["SELECT", "Select friendly troops."],
              "MOVE": ["NONE", "Move to target."],
              "BUILDING": ["TARGET", "Enter building."],
              "ROTATE": ["NONE", "Rotate to target."],
              "VALID_TARGET": ["TARGET", "Valid target."],
              "TOO_FAR": ["BAD_TARGET", "Out of movement range."],
              "INVALID_TARGET": ["NO_TARGET", "Invalid target."]}

status_icons = {"AMBUSH": ["BUILDING", 4],
                "BAILED_OUT": ["LOADED", 5],
                "BUTTONED_UP": ["NONE", 0],
                "OVERWATCH": ["SPOTTING", 4],
                "PLACING_MINES": ["MINES", 4],
                "REMOVING_MINES": ["MINES", 1],
                "JAMMED": ["JAMMED", 3],
                "PRONE": ["NONE", 0],
                "CRIPPLED": ["DAMAGE", 3],
                "MOVED": ["MOVED", 1],
                "FAST": ["MOVED", 2],
                "MARKED": ["SPOTTING", 2],
                "HAS_RADIO": ["RADIO", 1],
                "UNRELIABLE": ["NONE", 0],
                "RELIABLE": ["NONE", 0],
                "RAW_RECRUITS": ["HIT_MOD", 3],
                "VETERANS": ["HIT_MOD", 1],
                "VISION": ["SPOTTING", 1],
                "RECOGNIZED": ["HIT_MOD", 3],
                "CONFUSED": ["RADIO", 3],
                "IN_BUILDING": ["BUILDING", 1],
                "BUNKERED_UP": ["BUILDING", 2],
                "SPOTTED": ["SPOTTING", 2],
                "LOW_AMMO": ["AMMO", 2],
                "OUT_OF_AMMO": ["AMMO", 5],
                "LOADED_UP": ["LOADED", 1],
                "FULL_LOAD": ["LOADED", 3],
                "STEADY_AIM": ["HIT_MOD", 4],
                "RAPID_FIRE": ["HIT_MOD", 4],
                "SPECIAL_AMMO": ["AMMO", 4],
                "QUICK_MARCH": ["MOVED", 4],
                "OVERDRIVE": ["MOVED", 4],
                "COMMAND_RADIO": ["RADIO", 4],
                "AIR_FORCE_RADIO": ["RADIO", 4],
                "TACTICAL_RADIO": ["RADIO", 4],
                "RADIO_JAMMING": ["RADIO", 5]}

agent_rotations = {0: [0, -1],
                   1: [-1, -1],
                   2: [-1, 0],
                   3: [-1, 1],
                   4: [0, 1],
                   5: [1, 1],
                   6: [1, 0],
                   7: [1, -1]}


def get_weapon_stats():
    weapons = None

    weapon_path = bge.logic.expandPath("//saves/weapons.txt")
    with open(weapon_path, "r") as infile:
        weapons = json.load(infile)

    return weapons


def get_vehicle_stats():
    vehicles = None

    vehicle_path = bge.logic.expandPath("//saves/test_vehicles.txt")
    with open(vehicle_path, "r") as infile:
        vehicles = json.load(infile)

    return vehicles


def get_ai_painter():
    ai_painter = None

    ai_painter_path = bge.logic.expandPath("//saves/ai_painter.txt")
    with open(ai_painter_path, "r") as infile:
        ai_painter = json.load(infile)

    return ai_painter


def get_action_stats():
    actions = None

    action_path = bge.logic.expandPath("//saves/actions.txt")
    with open(action_path, "r") as infile:
        actions = json.load(infile)

    return actions


def get_building_stats():
    buildings = None

    building_path = bge.logic.expandPath("//saves/buildings.txt")
    with open(building_path, "r") as infile:
        buildings = json.load(infile)

    return buildings


def get_infantry_stats():
    infantry = None

    infantry_path = bge.logic.expandPath("//saves/infantry.txt")
    with open(infantry_path, "r") as infile:
        infantry = json.load(infile)

    return infantry
