import json
import bge


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

