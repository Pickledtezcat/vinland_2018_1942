import bge
import json


def build_test_vehicles():
    test_vehicles = {
        "medium tank": [2, 2, 2, 1, "tracked", "high velocity gun", "machinegun", "", "machinegun", [5, 2, 5], 50,
                        ["SIGHTS", "RADIO", "COMMANDER", ""], 100, 100, 6],
        "light tank": [3, 3, 3, 1, "tracked", "autocannon", "", "", "machinegun", [3, 2, 3], 30,
                       ["RIVETS", "RADIO", "", ""], 100, 100, 4],
        "assault gun": [2, 2, 3, 0, "tracked", "", "", "heavy gun", "", [7, 4, 0], 40, ["RIVETS", "RADIO", "", ""], 100,
                        0, 4],
        "truck": [3, 2, 2, 0, "half_track", "", "", "", "", [2, 1, 0], 20, ["RIVETS", "STORAGE", "", ""], 0, 0, 4],
        "anti tank gun": [1, 1, 1, 0, "gun_carriage", "super heavy gun", "", "", "", [1, 0, 0], 10, ["", "", "", ""],
                          100, 0, 3],
        "artillery": [1, 1, 1, 0, "gun_carriage", "artillery", "", "", "", [1, 0, 0], 10, ["COMPUTER", "", "", ""], 100,
                      0, 4],
        "scout car": [3, 2, 2, 1, "wheeled", "light gun", "", "", "", [2, 2, 2], 30, ["PERISCOPE", "RADIO", "", ""],
                      100, 0, 5]}

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
              "secondary_ammo",
              "size"]

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


def build_infantry():
    infantry = {"rm": ["RIFLE", "rifleman", 3, 5, 3, ["SHOOT", "EXTRA_GRENADES", "PLACE_MINES", "SATCHEL_CHARGE"]],
                "sm": ["SMG", "shock troops", 3, 3, 2, ["BURST_FIRE", "EXTRA_GRENADES", "SATCHEL_CHARGE", ""]],
                "mg": ["MG", "machine-gunner", 4, 2, 3, ["BURST_FIRE", "RAPID_FIRE", "SUPPRESSING_FIRE", ""]],
                "hg": ["MG", "heavy-machine-gunner", 4, 2, 3, ["BURST_FIRE", "RAPID_FIRE", "SUPPRESSING_FIRE", ""]],
                "at": ["ANTI_TANK", "anti-tank rifleman", 4, 2, 3, ["ANTI_TANK", "TARGET_TRACKS", "", ""]],
                "en": ["ENGINEER", "engineer", 2, 2, 1, ["SHOOT", "REPAIR", "PLACE_MINES", ""]],
                "gr": ["RIFLE", "grenadier", 3, 3, 3, ["SHOOT", "RIFLE_GRENADE", "SATCHEL_CHARGE", ""]],
                "gc": ["ENGINEER", "crewman", 3, 5, 1, ["SHOOT", "CREW", "SATCHEL_CHARGE", ""]],
                "mk": ["RIFLE", "marksman", 2, 2, 5, ["SHOOT", "SPOTTING", "", ""]],
                "ht": ["ANTI_TANK", "heavy anti-tank", 4, 2, 4, ["ANTI_TANK", "TARGET_TRACKS", "", ""]],
                "pt": ["RIFLE", "paratrooper", 5, 5, 3, ["BURST_FIRE", "PLACE_MINES", "SPOTTING", ""]],
                "cm": ["OFFICER", "commander", 2, 1, 1, ["SHOOT", "SPOTTING", "", ""]]}

    titles = ["mesh",
              "display_name",
              "toughness",
              "number",
              "base_accuracy",
              "actions"]

    out_path = "D:/projects/vinland_1942/game_folder/saves/infantry.txt"

    new_dict = {}

    for dict_key in infantry:
        entries = infantry[dict_key]

        entry_dict = {}
        extra_grenades = False

        for t in range(len(titles)):
            title = titles[t]
            entry = entries[t]
            action_strings = []

            if title == "actions":
                action_list = [action for action in entry if action != ""]

                for s in action_list:

                    if s != "EXTRA_GRENADES":
                        action_strings.append(s)
                    else:
                        extra_grenades = True

                basic_actions = ["THROW_GRENADE", "ENTER_BUILDING", "MOVE", "TOGGLE_STANCE", "QUICK_MARCH",
                                 "RECOVER_MORALE", "OVERWATCH", "DIRECT_ORDER", "FACE_TARGET", "REMOVE_MINES"]

                for basic in basic_actions:
                    action_strings.append(basic)

                if "SPOTTING" in action_list:
                    action_strings.append("MARK_TARGET")

                entry = action_strings

            entry_dict[title] = entry

        if extra_grenades:
            entry_dict["primary_ammo"] = 2 * entry_dict["number"]
        else:
            entry_dict["primary_ammo"] = 1 * entry_dict["number"]

        entry_dict["secondary_ammo"] = 100
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
                     17: ["leaf spring", "drive", 1, 1, 0, 6, 7, "", ["leaf_spring", "cheap"], "description goes here"],
                     18: ["coil spring", "drive", 1, 1, 0, 6, 8, "", ["coil_spring", ""], "description goes here"],
                     19: ["conical coil spring", "drive", 1, 2, 0, 6, 18, "", ["coil_spring", ""],
                          "description goes here"],
                     20: ["bell crank", "drive", 1, 3, 0, 6, 20, "", ["bell_crank", "unstable"],
                          "description goes here"],
                     21: ["torsion bar", "drive", 1, 3, 0, 6, 16, "", ["torsion_bar", ""], "description goes here"],
                     22: ["disc spring", "drive", 1, 1, 0, 6, 8, "", ["disc_spring", "cheap"], "description goes here"],
                     23: ["hydraulic system", "drive", 1, 4, 0, 6, 35, "", ["unreliable", ""], "description goes here"],
                     24: ["extra fuel", "utility", 1, 1, 0, 6, 1, "", ["extra_fuel", ""], "description goes here"],
                     25: ["bulkhead", "utility", 1, 2, 0, 6, 0, "", ["bulkhead", ""], "description goes here"],
                     26: ["storage space", "utility", 1, 1, 0, 6, 2, "", ["storage", ""], "description goes here"],
                     27: ["extra ammo", "utility", 1, 1, 0, 6, 1, "", ["ammo", ""], "description goes here"],
                     28: ["improved turret control", "utility", 1, 1, 0, 6, 0, "", ["turret_control", ""],
                          "description goes here"],
                     29: ["gyroscopic stabilizer", "utility", 1, 1, 0, 6, 0, "", ["gyro", ""], "description goes here"],
                     30: ["extra loader", "utility", 1, 1, 0, 6, 0, "", ["loader", ""], "description goes here"],
                     31: ["divisional radio", "utility", 1, 2, 0, 6, 0, "", ["divisional_radio", ""],
                          "description goes here"],
                     32: ["improved transmission", "utility", 1, 1, 0, 6, 0, "", ["transmission", ""],
                          "description goes here"],
                     33: ["armored cupola", "utility", 1, 1, 0, 6, 0, "", ["cupola", ""], "description goes here"],
                     34: ["primitive machinegun", "weapon", 1, 1, 0, 6, 1, "", ["burst_fire", "secondary"],
                          "description goes here"],
                     35: ["machinegun", "weapon", 1, 1, 0, 6, 1, "", ["rapid_fire", "secondary"],
                          "description goes here"],
                     36: ["quad machineguns", "weapon", 1, 2, 0, 6, 1, "", ["rapid_fire", "quad_mount"],
                          "description goes here"],
                     37: ["heavy machinegun", "weapon", 1, 1, 0, 6, 2, "", ["rapid_fire", "secondary"],
                          "description goes here"],
                     38: ["quad heavy machineguns", "weapon", 1, 2, 0, 6, 2, "", ["rapid_fire", "quad_mount"],
                          "description goes here"],
                     39: ["primitive autocannon", "weapon", 1, 2, 0, 6, 2, "", ["burst_fire", "jam"],
                          "description goes here"],
                     40: ["autocannon", "weapon", 1, 1, 0, 6, 3, "", ["rapid_fire", "secondary"],
                          "description goes here"],
                     41: ["quad autocannon", "weapon", 1, 3, 0, 6, 3, "", ["rapid_fire", "quad_mount"],
                          "description goes here"],
                     42: ["heavy autocannon", "weapon", 1, 2, 0, 6, 4, "", ["burst_fire", "jam"],
                          "description goes here"],
                     43: ["twin heavy autocannon", "weapon", 1, 3, 0, 6, 4, "", ["burst_fire", "twin_mount"],
                          "description goes here"],
                     44: ["anti tank rifle", "weapon", 1, 1, 0, 6, 2, "", ["at1", "quick"], "description goes here"],
                     45: ["primitive gun", "weapon", 1, 3, 0, 6, 3, "", ["slow", "cheap"], "description goes here"],
                     46: ["light gun", "weapon", 1, 2, 0, 6, 4, "", ["at1", "quick"], "description goes here"],
                     47: ["squeeze gun", "weapon", 1, 2, 0, 6, 4, "", ["at2", "jam"], "description goes here"],
                     48: ["medium gun", "weapon", 1, 2, 0, 6, 5, "", ["cheap", ""], "description goes here"],
                     49: ["quick firing gun", "weapon", 1, 3, 0, 6, 6, "", ["quick", ""], "description goes here"],
                     50: ["high velocity gun", "weapon", 2, 2, 0, 6, 6, "", ["at2", ""], "description goes here"],
                     51: ["heavy gun", "weapon", 1, 3, 0, 6, 8, "", ["slow", ""], "description goes here"],
                     52: ["advanced gun", "weapon", 1, 4, 0, 6, 8, "", ["at2", "slow"], "description goes here"],
                     53: ["compact gun", "weapon", 1, 2, 0, 6, 8, "", ["jam", "slow"], "description goes here"],
                     54: ["all purpose gun", "weapon", 2, 2, 0, 6, 9, "", ["at1", "quick"], "description goes here"],
                     55: ["support gun", "weapon", 1, 3, 0, 6, 8, "", ["indirect", ""], "description goes here"],
                     56: ["heavy support gun", "weapon", 2, 2, 0, 6, 14, "", ["indirect", "very_slow"],
                          "description goes here"],
                     57: ["artillery", "weapon", 1, 4, 0, 6, 10, "", ["artillery", "slow"], "description goes here"],
                     58: ["heavy artillery", "weapon", 2, 3, 0, 6, 15, "", ["artillery", "very_slow"],
                          "description goes here"],
                     59: ["super heavy gun", "weapon", 2, 3, 0, 6, 12, "", ["at1", "very_slow"],
                          "description goes here"],
                     60: ["breech mortar", "weapon", 1, 2, 0, 6, 10, "", ["mortar", "slow"], "description goes here"],
                     61: ["heavy breech mortar", "weapon", 1, 2, 0, 6, 15, "", ["mortar", "very_slow"],
                          "description goes here"],
                     62: ["light breech mortar", "weapon", 1, 1, 0, 6, 5, "", ["mortar", ""], "description goes here"],
                     63: ["small rockets", "weapon", 2, 2, 0, 6, 6, "", ["rocket", "small"], "description goes here"],
                     64: ["large rockets", "weapon", 2, 2, 0, 6, 12, "", ["rocket", "large"], "description goes here"],
                     65: ["medium rockets", "weapon", 2, 2, 0, 6, 9, "", ["rocket", "medium"], "description goes here"],
                     66: ["anti mine coating", "module", 1, 1, 0, 6, 0, "", ["anti_mine", ""], "description goes here"],
                     67: ["engine turbocharger", "module", 1, 1, 0, 6, 0, "", ["turbocharger", ""],
                          "description goes here"],
                     68: ["engine dust filters", "module", 1, 1, 0, 6, 0, "", ["filters", ""], "description goes here"],
                     69: ["improved radiator", "module", 1, 1, 0, 6, 0, "", ["radiator", ""], "description goes here"],
                     70: ["wide tracks", "module", 1, 1, 0, 6, 0, "", ["wide_tracks", ""], "description goes here"],
                     71: ["radio operator", "module", 1, 1, 0, 6, 0, "", ["radio", ""], "description goes here"],
                     72: ["commander", "module", 1, 1, 0, 6, 0, "", ["commander", ""], "description goes here"],
                     73: ["modular engine bay", "module", 1, 1, 0, 6, 0, "", ["easy_repair", ""],
                          "description goes here"],
                     74: ["engine block heater", "module", 1, 1, 0, 6, 0, "", ["heater", ""], "description goes here"],
                     75: ["extra escape hatches", "module", 1, 1, 0, 6, 0, "", ["escape_hatches", ""],
                          "description goes here"],
                     76: ["applique armor plates", "module", 1, 1, 0, 6, 0, "", ["extra_plates", ""],
                          "description goes here"],
                     77: ["grenade net", "module", 1, 1, 0, 6, 0, "", ["net", ""], "description goes here"],
                     78: ["fire extinguishers", "module", 1, 1, 0, 6, 0, "", ["extinguishers", ""],
                          "description goes here"],
                     79: ["wet ammo storage", "module", 1, 1, 0, 6, 0, "", ["wet_ammo", ""], "description goes here"],
                     80: ["improved weapon sights", "module", 1, 1, 0, 6, 0, "", ["sights", ""],
                          "description goes here"],
                     81: ["semiautomatic breech", "module", 1, 1, 0, 6, 0, "", ["quick_reload", ""],
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
            small_rockets = "rocket" in special and "small" in special
            medium_rockets = "rocket" in special and "medium" in special
            large_rockets = "rocket" in special and "large" in special

            artillery = "artillery" in special
            mortar = "mortar" in special
            indirect = "indirect" in special
            twin_mount = "twin_mount" in special
            quad_mount = "quad_mount" in special
            large_caliber = rating > 5
            anti_tank_1 = "at1" in special
            anti_tank_2 = "at2" in special
            very_slow = "very_slow" in special
            slow = "slow" in special
            secondary = "secondary" in special
            jamming = "jam" in special
            quick = "quick" in special
            burst_fire = "burst_fire" in special
            rapid_fire = "rapid_fire" in special

            name_key = entry["name"]
            weapon["power"] = rating

            if secondary:
                weapon["mount"] = "secondary"
            else:
                weapon["mount"] = "primary"

            # if slow in special, don't allow rapid fire action

            multi_shot = burst_fire or rapid_fire

            if twin_mount:
                weapon["shots"] = 2
            elif quad_mount:
                weapon["shots"] = 4
            else:
                weapon["shots"] = 1

            weapon_actions = []
            artillery_type_weapon = indirect or mortar or artillery

            if rockets:
                if small_rockets:
                    weapon_actions.append("SMALL_ROCKETS")
                if medium_rockets:
                    weapon_actions.append("MEDIUM_ROCKETS")
                    weapon_actions.append("SMOKE_ROCKETS")
                if large_rockets:
                    weapon_actions.append("LARGE_ROCKETS")
                    weapon_actions.append("SMOKE_ROCKETS")

            elif artillery_type_weapon:
                if large_caliber:
                    weapon_actions.append("SMOKE_SHELLS")

                weapon_actions.append("HIGH_EXPLOSIVE")

                if indirect or mortar:
                    weapon_actions.append("RANGED_SUPPORT_FIRE")

                if artillery:
                    weapon_actions.append("ARTILLERY_SHOT")
                    weapon_actions.append("ZEROED_ARTILLERY")

            elif multi_shot:
                weapon_actions.append("BURST_FIRE")
                weapon_actions.append("HASTY_BURST")

                if rapid_fire:
                    weapon_actions.append("SUPPRESSING_FIRE")
                    weapon_actions.append("RAPID_FIRE")

            else:
                if anti_tank_1 or anti_tank_2:
                    if not very_slow:
                        weapon_actions.append("CALLED_SHOT")
                        if large_caliber:
                            weapon_actions.append("TARGET_TRACKS")

                    if anti_tank_1:
                        weapon_actions.append("ANTI_TANK")
                    if anti_tank_2:
                        weapon_actions.append("ARMOR_PIERCING")
                else:
                    weapon_actions.append("AIMED_SHOT")
                    weapon_actions.append("SHOOT")

                    if large_caliber:
                        weapon_actions.append("SPECIAL_AMMO")
                        weapon_actions.append("HIGH_EXPLOSIVE")

                    if quick:
                        weapon_actions.append("QUICK_FIRE")
                    else:
                        if not very_slow:
                            weapon_actions.append("SNAP_SHOT")

            if jamming:
                weapon_actions.append("CLEAR_JAM")

            if slow or twin_mount:
                base_recharge = 2
            elif very_slow or quad_mount:
                base_recharge = 3
            elif quick:
                base_recharge = 0
            else:
                base_recharge = 1

            if very_slow:
                base_actions = 1
            else:
                base_actions = 0

            weapon["base_recharge"] = base_recharge
            weapon["base_actions"] = base_actions

            weapon["actions"] = weapon_actions
            weapon["name"] = name_key
            weapon_dict[name_key] = weapon

        out_path = "D:/projects/vinland_1942/game_folder/saves/weapons.txt"

        with open(out_path, "w") as outfile:
            json.dump(weapon_dict, outfile)


def build_actions():
    action_items = {"AMBUSH": ["spotting", "ORDERS", 2, 1, 0, "SELF", "TRIGGER_AMBUSH", 1, 0, 0, 0, 0, 0, 0, ""],
                    "ANTI_ARICRAFT_FIRE": ["aa_fire", "ORDERS", 2, 1, 0, "SELF", "TRIGGER_ANTI_AIRCRAFT", 0, 0, 0, 0, 0,
                                           0, 0, ""],
                    "BAIL_OUT": ["crew", "ORDERS", 1, 0, 0, "SELF", "BAILING_OUT", 0, 0, 0, 0, 0, 0, 0, ""],
                    "TOGGLE_BUTTONED_UP": ["spotting", "ORDERS", 1, 0, 0, "SELF", "TOGGLE_BUTTONED_UP", 0, 0, 0, 0, 0,
                                           0, 0, ""],
                    "CANCEL_ACTIONS": ["cancel", "ORDERS", 0, 0, 0, "SELF", "CANCEL", 0, 0, 0, 0, 0, 0, 0, ""],
                    "CREW": ["crew", "ORDERS", 1, 0, 0, "FRIEND", "CREW", 0, 0, 0, 0, 0, 0, 0, ""],
                    "DIRECT_ORDER": ["radio", "ORDERS", 1, 1, 1, "SELF", "DIRECT_ORDER", 0, 0, 0, 0, 0, 0, 0, ""],
                    "MOVE": ["move", "ORDERS", 1, 0, 0, "MOVE", "MOVE", 0, 0, 0, 0, 0, 0, 0, ""],
                    "ENTER_BUILDING": ["building", "ORDERS", 1, 0, 0, "BUILDING", "ENTER_BUILDING", 0, 0, 0, 0, 0, 0, 0,
                                       ""],
                    "LOAD_TROOPS": ["load", "ORDERS", 1, 0, 0, "FRIEND", "LOAD_TROOPS", 0, 0, 0, 0, 0, 0, 0, ""],
                    "UNLOAD_TROOPS": ["unload", "ORDERS", 1, 0, 0, "SELF", "UNLOAD_TROOPS", 1, 0, 0, 0, 0, 0, 0, ""],
                    "OVERDRIVE": ["supply", "ORDERS", 0, 3, 1, "SELF", "OVERDRIVE", 0, 2, 0, 0, 0, 0, 0, ""],
                    "OVERWATCH": ["radio", "ORDERS", 1, 0, 1, "SELF", "SET_OVERWATCH", 1, 0, 0, 0, 0, 0, 0, ""],
                    "PLACE_MINES": ["mines", "ORDERS", 2, 1, 0, "SELF", "PLACE_MINE", 1, 0, 0, 0, 0, 0, 0, ""],
                    "TOGGLE_STANCE": ["crew", "ORDERS", 1, 0, 0, "SELF", "TOGGLE_PRONE", 0, 0, 0, 0, 0, 0, 0, ""],
                    "QUICK_MARCH": ["move", "ORDERS", 0, 3, 1, "SELF", "QUICK_MARCH", 0, 2, 0, 0, 0, 0, 0, ""],
                    "RECOVER_MORALE": ["radio", "ORDERS", 1, 0, 0, "SELF", "RECOVER", 0, 0, 0, 0, 0, 0, 0, ""],
                    "REARM_AND_RELOAD": ["repair", "ORDERS", 1, 0, 0, "FRIEND", "RELOAD", 0, 0, 0, 0, 0, 0, 0, ""],
                    "REMOVE_MINES": ["mines", "ORDERS", 2, 1, 0, "SELF", "REMOVE_MINE", 1, 0, 0, 0, 0, 0, 0, ""],
                    "REPAIR": ["repair", "ORDERS", 2, 0, 0, "FRIEND", "REPAIR", 0, 0, 0, 0, 0, 0, 0, ""],
                    "FACE_TARGET": ["rotate", "ORDERS", 1, 0, 0, "MOVE", "ROTATE", 0, 0, 0, 0, 0, 0, 0, ""],
                    "SPOTTING": ["spotting", "ORDERS", 2, 0, 0, "SELF", "SPOTTING", 0, 0, 0, 0, 0, 0, 0, ""],
                    "STEADY_AIM": ["aimed_shot", "ORDERS", 1, 0, 1, "SELF", "STEADY_AIM", 1, 0, 0, 0, 0, 0, 0, ""],
                    "FAST_RELOAD": ["supply", "ORDERS", 1, 6, 1, "SELF", "FAST_RELOAD", 0, 0, 0, 0, 0, 0, 0, ""],
                    "MARK_TARGET": ["spotting", "ORDERS", 1, 1, 1, "ENEMY", "MARKING", 0, 0, 0, 0, 0, 0, 0, ""],
                    "CLEAR_JAM": ["cancel", "ORDERS", 2, 0, 0, "SELF", "CLEAR_JAM", 0, 0, 0, 0, 0, 0, 0, ""],
                    "TARGET_TRACKS": ["tracks", "WEAPON", 2, 1, 0, "ENEMY", "HIT_TRACKS", 0, 0, 0.3, 0.5, 0.5, 1, 1,
                                      ""],
                    "HIGH_EXPLOSIVE": ["explosion", "WEAPON", 1, 0, 0, "ENEMY", "EXPLOSION", 0, 0, 0.6, 0.5, 2, 1, 3,
                                       ""],
                    "ARTILLERY_SHOT": ["explosion", "WEAPON", 2, 0, 0, "MAP", "ARTILLERY_EXPLOSION", 0, 0, 0, 0.2, 2, 1,
                                       3, ""],
                    "ZEROED_ARTILLERY": ["explosion", "WEAPON", 2, 3, 0, "MAP", "ARTILLERY_EXPLOSION", 0, 0, 0.3, 0.2,
                                         2, 1, 3, ""],
                    "SMALL_ROCKETS": ["explosion", "WEAPON", 2, 3, 0, "MAP", "ROCKET_EXPLOSION", 0, 0, 0.3, 0.2, 1.5, 9,
                                      3, ""],
                    "MEDIUM_ROCKETS": ["explosion", "WEAPON", 2, 3, 0, "MAP", "ROCKET_EXPLOSION", 0, 0, 0, 0.2, 2, 6, 3,
                                       ""],
                    "LARGE_ROCKETS": ["explosion", "WEAPON", 2, 3, 0, "MAP", "ROCKET_EXPLOSION", 0, 0, 0, 0.5, 2.5, 3,
                                      3, ""],
                    "SMOKE_ROCKETS": ["explosion", "WEAPON", 2, 3, 0, "MAP", "ROCKET_SMOKE", 0, 0, 0.3, 0, 0, 6, 0, ""],
                    "RANGED_SUPPORT_FIRE": ["explosion", "WEAPON", 1, 3, 0, "MAP", "ARTILLERY_EXPLOSION", 0, 0, 0, 0.2,
                                            1.5, 1, 2, ""],
                    "THROW_GRENADE": ["grenade", "WEAPON", 1, 3, 0, "ENEMY", "GRENADE_EXPLOSION", 0, 0, 0.3, 2, 2, 1, 2,
                                      ""],
                    "SATCHEL_CHARGE": ["grenade", "WEAPON", 1, 3, 0, "ENEMY", "GRENADE_EXPLOSION", 0, 0, 0, 4, 4, 1, 8,
                                       ""],
                    "RIFLE_GRENADE": ["grenade", "WEAPON", 1, 3, 0, "ENEMY", "GRENADE_EXPLOSION", 0, 0, 0.3, 2, 2, 1, 2,
                                      ""],
                    "SHOOT": ["shoot", "WEAPON", 1, 0, 0, "ENEMY", "HIT", 0, 0, 1, 1.5, 1.2, 1, 1, ""],
                    "BURST_FIRE": ["shoot", "WEAPON", 1, 0, 0, "ENEMY", "HIT", 0, 0, 0.6, 1, 1, 3, 1, ""],
                    "ANTI_TANK": ["shoot", "WEAPON", 1, 0, 0, "ENEMY", "HIT", 0, 0, 1.2, 2, 1, 1, 1, ""],
                    "SUPPRESSING_FIRE": ["rapid_fire", "WEAPON", 2, 3, 0, "ENEMY", "HIT", 0, 0, 0, 1, 1, 6, 4, ""],
                    "AIMED_SHOT": ["aimed_shot", "WEAPON", 2, 3, 0, "ENEMY", "HIT", 0, 0, 1.5, 1.5, 1.2, 1, 1, ""],
                    "CALLED_SHOT": ["aimed_shot", "WEAPON", 1, 0, 1, "ENEMY", "HIT", 0, 0, 1, 2, 2, 1, 2, ""],
                    "RAPID_FIRE": ["rapid_fire", "WEAPON", 1, 0, 1, "ENEMY", "HIT", 0, 0, 0.6, 1, 1, 6, 1, ""],
                    "QUICK_FIRE": ["rapid_fire", "WEAPON", 0, 3, 1, "ENEMY", "HIT", 0, 0, 0.8, 1, 1, 1, 1, ""],
                    "ARMOR_PIERCING": ["aimed_shot", "WEAPON", 1, 0, 0, "ENEMY", "HIT", 0, 0, 1.2, 3, 1, 1, 1, ""],
                    "HASTY_BURST": ["rapid_fire", "WEAPON", 0, 3, 0, "ENEMY", "HIT", 0, 0, 0, 1, 1, 3, 1, ""],
                    "SPECIAL_AMMO": ["aimed_shot", "WEAPON", 1, 0, 0, "ENEMY", "HIT", 0, 0, 1, 3, 2, 1, 2, ""],
                    "SNAP_SHOT": ["shoot", "WEAPON", 0, 3, 0, "ENEMY", "HIT", 0, 0, 0.3, 1, 1, 1, 1, ""],
                    "SMOKE_SHELLS": ["smoke", "WEAPON", 1, 1, 0, "MAP", "SMOKE", 0, 0, 0.3, 0, 0, 1, 0, ""]}

    titles = ["icon",
              "action_type",
              "action_cost",
              "recharge_time",
              "radio_points",
              "target",
              "effect",
              "end_turn",
              "effect_duration",
              "accuracy_multiplier",
              "armor_multiplier",
              "damage_multiplier",
              "shot_multiplier",
              "shock_multiplier",
              "description"]

    out_path = "D:/projects/vinland_1942/game_folder/saves/actions.txt"
    new_dict = {}

    for dict_key in action_items:
        entries = action_items[dict_key]
        entry_dict = {}

        for t in range(len(titles)):

            title = titles[t]
            entry = entries[t]

            if title == "special":
                entry = [special for special in entry if special != ""]

            entry_dict[title] = entry

        entry_dict["triggered"] = False
        entry_dict["recharged"] = 0

        entry_dict["action_name"] = dict_key
        new_dict[dict_key] = entry_dict

    with open(out_path, "w") as outfile:
        json.dump(new_dict, outfile)


def build_buildings():

    buildings = {"building_1": ["small building", 1, 1, 1, 0, 1, 40, 10],
                 "building_2": ["large shed", 2, 1, 1, 0, 1, 60, 10],
                 "building_3": ["supply crates", 1, 1, 0, 1, 0, 20, 10]}

    titles = ["building_label",
              "x_size",
              "y_size",
              "can_enter",
              "supplies",
              "height",
              "hps",
              "damage_reduction"]

    out_path = "D:/projects/vinland_1942/game_folder/saves/buildings.txt"
    new_dict = {}

    for dict_key in buildings:
        entries = buildings[dict_key]
        entry_dict = {}

        for t in range(len(titles)):

            title = titles[t]
            entry = entries[t]

            entry_dict[title] = entry

        entry_dict["destroyed"] = False
        entry_dict["damage"] = 0

        new_dict[dict_key] = entry_dict

    with open(out_path, "w") as outfile:
        json.dump(new_dict, outfile)


def write_unique_icons():
    actions = ["spotting",
               "aa_fire",
               "crew",
               "spotting",
               "cancel",
               "crew",
               "radio",
               "move",
               "move",
               "move",
               "radio",
               "mines",
               "crew",
               "move",
               "radio",
               "repair",
               "mines",
               "repair",
               "rotate",
               "spotting",
               "cancel",
               "tracks",
               "explosion",
               "explosion",
               "explosion",
               "explosion",
               "explosion",
               "explosion",
               "explosion",
               "explosion",
               "grenade",
               "grenade",
               "grenade",
               "shoot",
               "shoot",
               "shoot",
               "rapid_fire",
               "shoot",
               "shoot",
               "aimed_shot",
               "aimed_shot",
               "rapid_fire",
               "rapid_fire",
               "aimed_shot",
               "aimed_shot",
               "shoot",
               "smoke"]

    unique_actions = []

    for action in actions:
        if action not in unique_actions:
            unique_actions.append(action)

    out_path = "D:/projects/vinland_1942/game_folder/saves/unique_actions.txt"
    with open(out_path, "w") as outfile:
        json.dump({"unique_actions": unique_actions}, outfile)


# build_components()
# build_weapons()
build_test_vehicles()
# build_infantry()
# build_actions()
# build_buildings()

# write_unique_icons()
print("FINISHED")
