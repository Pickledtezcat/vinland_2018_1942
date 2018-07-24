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
              "NO_RADIO": ["NO_TARGET", "Has no radio."],
              "NO_AMMO": ["NO_TARGET", "Out of ammo for this weapon."],
              "JAMMED": ["NO_TARGET", "Weapons jammed. Clear jam or wait."],
              "AIR_SUPPORT": ["MAP_TARGET", "Call air support to this location."],
              "INVISIBLE": ["UNKNOWN", "No line of sight or not visible."],
              "IMMOBILE": ["NO_TARGET", "Can not move."],
              "IMPASSABLE": ["BAD_TARGET", "Location impassable."],
              "NO_ACTIONS": ["CYCLE", "Out of actions."],
              "TRIGGERED": ["CYCLE", "Action already triggered."],
              "SELECT_FRIEND": ["SELECT", "Select friendly troops."],
              "MOVE": ["NONE", "Move to target."],
              "BUILDING": ["TARGET", "Enter building."],
              "ROTATE": ["NONE", "Rotate to target."],
              "VALID_TARGET": ["TARGET", "Valid target."],
              "TOO_FAR": ["BAD_TARGET", "Out of movement range."],
              "INVALID_TARGET": ["NO_TARGET", "Invalid target."]}


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
