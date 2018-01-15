import bge
import json


def build_test_vehicles():
    test_vehicles = {"medium_tank": [2, 2, 2, 1, "tracked", "medium gun", "machinegun", "", "machinegun", [5, 2, 5], 50,
                                     ["sights", "radio", "commander", ""], 100, 100],
                     "light tank": [3, 3, 3, 1, "tracked", "autocannon", "", "", "machinegun", [3, 2, 3], 30,
                                    ["rivets", "", "", ""], 100, 100],
                     "assault_gun": [2, 2, 3, 0, "tracked", "medium gun", "", "", "", [7, 4, 0], 40,
                                     ["rivets", "radio", "", ""], 100, 0],
                     "truck": [3, 2, 2, 0, "half_track", "", "", "", "", [2, 1, 0], 20, ["rivets", "storage", "", ""],
                               0,
                               0],
                     "anti_tank_gun": [1, 1, 1, 0, "gun_carriage", "medium gun", "", "", "", [1, 0, 0], 10,
                                       ["", "", "", ""], 100, 0],
                     "artillery": [1, 1, 1, 0, "gun_carriage", "artillery", "", "", "", [1, 0, 0], 10,
                                   ["computer", "", "", ""], 100, 0],
                     "scout_car": [3, 2, 2, 1, "wheeled", "autocannon", "", "", "", [2, 2, 2], 30, ["", "", "", ""],
                                   100,
                                   0]}

    titles = ["on_road",
              "off_road",
              "handling",
              "turret",
              "drive_type",
              "turret_primary",
              "turret_secondary",
              "hull_primary",
              "hull_secondary",
              "armor",
              "hps",
              "special",
              "primary_ammo",
              "secondary_ammo"]

    out_path = "D:/projects/vinland_1942/game_folder/saves/test_vehicles.txt"

    new_dict = {}

    for dict_key in test_vehicles:
        entries = test_vehicles[dict_key]

        entry_dict = {}

        for t in range(len(titles)):
            title = titles[t]
            entry = entries[t]

            if title == "special":
                entry = [special for special in entry if special != ""]

            entry_dict[title] = entry

        new_dict[dict_key] = entry_dict

    with open(out_path, "w") as outfile:
        json.dump(new_dict, outfile)


def build_components():
    vehicle_items = {0: ["gun mantlet", "armor", 1, 1, 0, 6, 1, "", ["mantlet", ""], "description goes here"],
                     1: ["bolt on armor", "armor", 1, 2, 0, 6, 3, "", ["rivets", ""], "description goes here"],
                     2: ["bolt on armor", "armor", 1, 2, 0, 6, 3, "", ["rivets", ""], "description goes here"],
                     3: ["riveted armor", "armor", 1, 1, 0, 6, 2, "", ["rivets", ""], "description goes here"],
                     4: ["welded armor", "armor", 1, 2, 0, 6, 5, "", ["", ""], "description goes here"],
                     5: ["cast armor", "armor", 1, 3, 0, 6, 8, "", ["cast", ""], "description goes here"],
                     6: ["thick armor section", "armor", 1, 4, 0, 6, 12, "", ["", ""], "description goes here"],
                     7: ["automobile engine", "drive", 1, 1, 0, 6, 1, "", ["cheap", "reliable"],
                         "description goes here"],
                     8: ["truck engine", "drive", 1, 1, 0, 6, 2, "", ["reliable", ""], "description goes here"],
                     9: ["combo engine", "drive", 1, 2, 0, 6, 5, "", ["reliable", ""], "description goes here"],
                     10: ["industrial engine", "drive", 1, 4, 0, 6, 8, "", ["cheap", ""], "description goes here"],
                     11: ["performance engine", "drive", 1, 2, 0, 6, 6, "", ["unreliable", ""],
                          "description goes here"],
                     12: ["radial engine", "drive", 1, 2, 0, 6, 7, "", ["", ""], "description goes here"],
                     13: ["aircraft engine", "drive", 2, 2, 0, 6, 12, "", ["unreliable", ""], "description goes here"],
                     14: ["marine engine", "drive", 2, 3, 0, 6, 16, "", ["safe", ""], "description goes here"],
                     15: ["compact engine", "drive", 1, 3, 0, 6, 10, "", ["", ""], "description goes here"],
                     16: ["turboshaft engine", "drive", 1, 4, 0, 6, 20, "", ["unreliable", "dangerous"],
                          "description goes here"],
                     17: ["leaf spring", "drive", 1, 1, 0, 6, 7, "", ["leaf spring", "cheap"], "description goes here"],
                     18: ["coil spring", "drive", 1, 1, 0, 6, 8, "", ["coil spring", ""], "description goes here"],
                     19: ["conical coil spring", "drive", 1, 2, 0, 6, 18, "", ["coil spring", ""],
                          "description goes here"],
                     20: ["bell crank", "drive", 1, 3, 0, 6, 20, "", ["bell crank", "unstable"],
                          "description goes here"],
                     21: ["torsion bar", "drive", 1, 3, 0, 6, 16, "", ["torsion bar", ""], "description goes here"],
                     22: ["disc spring", "drive", 1, 1, 0, 6, 8, "", ["disc spring", "cheap"], "description goes here"],
                     23: ["hydraulic system", "drive", 1, 4, 0, 6, 35, "", ["unreliable", ""], "description goes here"],
                     24: ["extra fuel", "utility", 1, 1, 0, 6, 1, "", ["extra fuel", ""], "description goes here"],
                     25: ["bulkhead", "utility", 1, 2, 0, 6, 0, "", ["bulkhead", ""], "description goes here"],
                     26: ["storage space", "utility", 1, 1, 0, 6, 2, "", ["storage", ""], "description goes here"],
                     27: ["extra ammo", "utility", 1, 1, 0, 6, 1, "", ["ammo", ""], "description goes here"],
                     28: ["improved turret control", "utility", 1, 1, 0, 6, 0, "", ["turret control", ""],
                          "description goes here"],
                     29: ["gyroscopic stabilizer", "utility", 1, 1, 0, 6, 0, "", ["gyro", ""], "description goes here"],
                     30: ["extra loader", "utility", 1, 1, 0, 6, 0, "", ["loader", ""], "description goes here"],
                     31: ["divisional radio", "utility", 1, 2, 0, 6, 0, "", ["divisional radio", ""],
                          "description goes here"],
                     32: ["improved transmission", "utility", 1, 1, 0, 6, 0, "", ["transmission", ""],
                          "description goes here"],
                     33: ["armored cupola", "utility", 1, 1, 0, 6, 0, "", ["cupola", ""], "description goes here"],
                     34: ["primitive machinegun", "weapon", 1, 1, 0, 6, 1, "", ["2 shots", "secondary"],
                          "description goes here"],
                     35: ["machinegun", "weapon", 1, 1, 0, 6, 1, "", ["5 shots", "secondary"], "description goes here"],
                     36: ["quad machineguns", "weapon", 1, 2, 0, 6, 1, "", ["5 shots", "quad mount"],
                          "description goes here"],
                     37: ["heavy machinegun", "weapon", 1, 1, 0, 6, 2, "", ["3 shots", "secondary"],
                          "description goes here"],
                     38: ["quad heavy machineguns", "weapon", 1, 2, 0, 6, 2, "", ["3 shots", "quad mount"],
                          "description goes here"],
                     39: ["primitive autocannon", "weapon", 1, 2, 0, 6, 2, "", ["2 shots", "jam"],
                          "description goes here"],
                     40: ["autocannon", "weapon", 1, 1, 0, 6, 3, "", ["3 shots", "secondary"], "description goes here"],
                     41: ["quad autocannon", "weapon", 1, 3, 0, 6, 3, "", ["3 shots", "quad mount"],
                          "description goes here"],
                     42: ["heavy autocannon", "weapon", 1, 2, 0, 6, 4, "", ["2 shots", "jam"], "description goes here"],
                     43: ["twin heavy autocannon", "weapon", 1, 3, 0, 6, 4, "", ["2 shots", "twin mount"],
                          "description goes here"],
                     44: ["anti tank rifle", "weapon", 1, 1, 0, 6, 2, "", ["at1", ""], "description goes here"],
                     45: ["primitive gun", "weapon", 1, 3, 0, 6, 3, "", ["slow", "cheap"], "description goes here"],
                     46: ["light gun", "weapon", 1, 2, 0, 6, 4, "", ["at1", ""], "description goes here"],
                     47: ["squeeze gun", "weapon", 1, 2, 0, 6, 4, "", ["at2", "jam"], "description goes here"],
                     48: ["medium gun", "weapon", 1, 2, 0, 6, 5, "", ["cheap", ""], "description goes here"],
                     49: ["quick firing gun", "weapon", 1, 3, 0, 6, 6, "", ["2 shots", ""], "description goes here"],
                     50: ["high velocity gun", "weapon", 2, 2, 0, 6, 6, "", ["at2", ""], "description goes here"],
                     51: ["heavy gun", "weapon", 1, 3, 0, 6, 8, "", ["slow", "slow"], "description goes here"],
                     52: ["advanced gun", "weapon", 1, 4, 0, 6, 8, "", ["at2", "slow"], "description goes here"],
                     53: ["compact gun", "weapon", 1, 2, 0, 6, 8, "", ["jam", ""], "description goes here"],
                     54: ["all purpose gun", "weapon", 2, 2, 0, 6, 9, "", ["at1", "slow"], "description goes here"],
                     55: ["support gun", "weapon", 1, 2, 0, 6, 8, "", ["indirect", "slow"], "description goes here"],
                     56: ["heavy support gun", "weapon", 2, 2, 0, 6, 15, "", ["indirect", "slow"],
                          "description goes here"],
                     57: ["artillery", "weapon", 1, 4, 0, 6, 10, "", ["artillery", ""], "description goes here"],
                     58: ["heavy artillery", "weapon", 2, 3, 0, 6, 15, "", ["artillery", ""], "description goes here"],
                     59: ["super heavy gun", "weapon", 2, 3, 0, 6, 12, "", ["at1", "very slow"],
                          "description goes here"],
                     60: ["breech mortar", "weapon", 1, 2, 0, 6, 10, "", ["mortar", ""], "description goes here"],
                     61: ["heavy breech mortar", "weapon", 1, 2, 0, 6, 15, "", ["mortar", ""], "description goes here"],
                     62: ["light breech mortar", "weapon", 1, 1, 0, 6, 5, "", ["mortar", ""], "description goes here"],
                     63: ["small rockets", "weapon", 2, 2, 0, 6, 6, "", ["rocket", "24 shots"],
                          "description goes here"],
                     64: ["large rockets", "weapon", 2, 2, 0, 6, 12, "", ["rocket", "5 shots"],
                          "description goes here"],
                     65: ["medium rockets", "weapon", 2, 2, 0, 6, 9, "", ["rocket", "12 shots"],
                          "description goes here"],
                     66: ["anti mine coating", "module", 1, 1, 0, 6, 0, "", ["anti mine", ""], "description goes here"],
                     67: ["engine turbocharger", "module", 1, 1, 0, 6, 0, "", ["turbocharger", ""],
                          "description goes here"],
                     68: ["engine dust filters", "module", 1, 1, 0, 6, 0, "", ["filters", ""], "description goes here"],
                     69: ["improved radiator", "module", 1, 1, 0, 6, 0, "", ["radiator", ""], "description goes here"],
                     70: ["wide tracks", "module", 1, 1, 0, 6, 0, "", ["wide tracks", ""], "description goes here"],
                     71: ["radio operator", "module", 1, 1, 0, 6, 0, "", ["radio", ""], "description goes here"],
                     72: ["commander", "module", 1, 1, 0, 6, 0, "", ["commander", ""], "description goes here"],
                     73: ["modular engine bay", "module", 1, 1, 0, 6, 0, "", ["easy repair", ""],
                          "description goes here"],
                     74: ["engine block heater", "module", 1, 1, 0, 6, 0, "", ["heater", ""], "description goes here"],
                     75: ["extra escape hatches", "module", 1, 1, 0, 6, 0, "", ["escape hatches", ""],
                          "description goes here"],
                     76: ["applique armor plates", "module", 1, 1, 0, 6, 0, "", ["extra plates", ""],
                          "description goes here"],
                     77: ["grenade net", "module", 1, 1, 0, 6, 0, "", ["net", ""], "description goes here"],
                     78: ["fire extinquishers", "module", 1, 1, 0, 6, 0, "", ["extinquishers", ""],
                          "description goes here"],
                     79: ["wet ammo storage", "module", 1, 1, 0, 6, 0, "", ["wet ammo", ""], "description goes here"],
                     80: ["improved weapon sights", "module", 1, 1, 0, 6, 0, "", ["sights", ""],
                          "description goes here"],
                     81: ["semiautomatic breech", "module", 1, 1, 0, 6, 0, "", ["quick reload", ""],
                          "description goes here"],
                     82: ["periscope", "module", 1, 1, 0, 6, 0, "", ["periscope", ""], "description goes here"],
                     83: ["armor skirts", "module", 1, 1, 0, 6, 0, "", ["skirts", ""], "description goes here"],
                     84: ["repair tools", "module", 1, 1, 0, 6, 0, "", ["tools", ""], "description goes here"],
                     85: ["engine noise reducer", "module", 1, 1, 0, 6, 0, "", ["silencer", ""],
                          "description goes here"],
                     86: ["armor hardening", "module", 1, 1, 0, 6, 0, "", ["hardening", ""], "description goes here"],
                     87: ["sandbags", "module", 1, 1, 0, 6, 0, "", ["sandbags", ""], "description goes here"],
                     88: ["analog computer", "module", 1, 1, 0, 6, 0, "", ["computer", ""], "description goes here"]}

    titles = ["name",
              "type",
              "x",
              "y",
              "level",
              "obsolete",
              "rating",
              "visual flag",
              "special",
              "description"]

    out_path = "D:/projects/vinland_1942/game_folder/saves/components.txt"

    new_dict = {}
    weapons_dict = {}

    for dict_key in vehicle_items:
        entries = vehicle_items[dict_key]

        entry_dict = {}

        for t in range(len(titles)):
            title = titles[t]
            entry = entries[t]

            if title == "special":
                entry = [special for special in entry if special != ""]

            entry_dict[title] = entry

        new_dict[dict_key] = entry_dict

    with open(out_path, "w") as outfile:
        json.dump(new_dict, outfile)


#build_components()

def create_action(name, recycle, action_cost):
    new_action = {"name": name, "recycle": recycle, "progress": 0, "triggered": False,
                  "action_cost": action_cost}
    return new_action


def build_weapons():
    components = None
    weapon_dict = {}

    in_path = "D:/projects/vinland_1942/game_folder/saves/components.txt"
    with open(in_path, "r") as infile:
        components = json.load(infile)

    for component_key in components:
        entry = components[component_key]
        component_type = entry["type"]
        if component_type == "weapon":
            weapon = {}

            special = entry["special"]
            rating = entry['rating']

            rockets = "rocket" in special
            artillery = "artillery" in special
            mortar = "mortar" in special
            indirect = "indirect" in special
            twin_mount = "twin mount" in special
            quad_mount = "quad mount" in special
            small_caliber = rating < 4
            large_caliber = rating > 5
            anti_tank_1 = "at1" in special
            anti_tank_2 = "at2" in special
            very_slow = "very slow" in special
            slow = "slow" in special
            secondary = "secondary" in special
            jamming = "jam" in special

            name_key = entry["name"]
            weapon["power"] = rating

            if secondary:
                weapon["mount"] = "secondary"
            else:
                weapon["mount"] = "primary"

            # if slow in special, don't allow rapid fire action

            multi_shot = True

            if "3 shots" in special:
                weapon["shots"] = 3
            elif "5 shots" in special:
                weapon["shots"] = 5
            elif "12 shots" in special:
                weapon["shots"] = 12
            elif "24 shots" in special:
                weapon["shots"] = 24
            elif "2 shots" in special:
                weapon["shots"] = 2
            else:
                multi_shot = False
                weapon["shots"] = 1

            if twin_mount:
                weapon["shots"] *= 2
            elif quad_mount:
                weapon["shots"] *= 4

            non_aimed = rockets or mortar or artillery

            weapon_actions = []
            if not non_aimed and not anti_tank_1 and not anti_tank_2:
                if very_slow:
                    weapon_actions.append(create_action("SHOOT", 0, 2))
                else:
                    weapon_actions.append(create_action("SHOOT", 0, 1))

            if large_caliber and not rockets and not artillery and not mortar:
                weapon_actions.append(create_action("HIGH_EXPLOSIVE", 0, 1))

            if non_aimed or indirect:
                weapon_actions.append(create_action("ARTILLERY", 0, 2))
                if not rockets:
                    weapon_actions.append(create_action("SNAP_ARTILLERY", 4, 1))

            if multi_shot and not non_aimed:
                weapon_actions.append(create_action("SUPPRESSION", 3, 2))

            if anti_tank_1:
                weapon_actions.append(create_action("ANTI_TANK", 0, 1))

            if anti_tank_2:
                weapon_actions.append(create_action("PIERCING", 0, 1))

            if not small_caliber and not non_aimed and not slow and not very_slow and not multi_shot:
                weapon_actions.append(create_action("SNAP_SHOT", 6, 0))
                weapon_actions.append(create_action("AIMED", 3, 2))

            if rockets:
                weapon_actions.append(create_action("HASTY_BARRAGE", 3, 1))

            if not jamming:
                weapon_actions.append(create_action("CLEAR_JAM", 0, 1))
            else:
                weapon_actions.append(create_action("CLEAR_JAM", 0, 2))

            action_dictionary = {}
            for action in weapon_actions:
                action_dictionary[action["name"]] = action

            weapon["actions"] = action_dictionary

            weapon_dict[name_key] = weapon

        out_path = "D:/projects/vinland_1942/game_folder/saves/weapons.txt"

        with open(out_path, "w") as outfile:
            json.dump(weapon_dict, outfile)


build_weapons()



