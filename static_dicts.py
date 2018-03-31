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


def get_action_stats():

    actions = None

    action_path = bge.logic.expandPath("//saves/actions.txt")
    with open(action_path, "r") as infile:
        actions = json.load(infile)

    return actions


def get_infantry_stats():
    infantry = None

    infantry_path = bge.logic.expandPath("//saves/infantry.txt")
    with open(infantry_path, "r") as infile:
        infantry = json.load(infile)

    return infantry

