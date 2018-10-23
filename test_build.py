import bge
import json


def build_test_vehicles():
    test_vehicles = {
        "HRR_scout_car_1": ["ASR-I-CARRO", "anser scout car", 3, 1, 1, 0, "TRACKED", "", "", "", "", [0, 0], 15,
                            ["RADIO", "AIR_FORCE_RADIO", "OPEN_TOP", ""], "AIR_SUPPORT", 0, 3],
        "HRR_scout_car_2": ["ASR-II-CARRO", "anser scout car", 2, 1, 1, 0, "TRACKED", "", "", "machinegun", "", [1, 1],
                            15, ["RADIO", "PERISCOPE", "COMMANDER", ""], "JAMMER", 1, 3],
        "HRR_scout_tank_1": ["PLM-I-PANZER", "pullum scout tank", 2, 2, 2, 0, "TRACKED", "short gun", "", "", "",
                             [2, 1], 20, ["RIVETS", "", "", ""], "HOLD", 2, 4],
        "HRR_scout_gun_1": ["CPA-I-GESHUTZ", "capra scout gun", 2, 2, 2, 0, "TRACKED", "", "", "medium gun", "", [1, 1],
                            15, ["RIVETS", "OPEN_TOP", "LOADER", ""], "HOLD", 2, 3],
        "HRR_medium _aa_tank": ["CTS-IIC-LUFTTELUM", "cetus medium tank", 2, 2, 2, 0, "TRACKED", "light autocannon", "",
                                "", "", [2, 2], 25, ["RADIO", "AA_TURRET", "LOADER", ""], "ANTI_AIR", 3, 5],
        "HRR_medium_mortar_tank": ["CTS-IIP-GESHUTZ", "cetus medium tank", 2, 2, 2, 0, "TRACKED", "", "",
                                   "breech mortar", "", [2, 2], 25, ["RADIO", "OPEN_TOP", "", ""], "ARTILLERY", 4, 5],
        "HRR_medium_scout_tank": ["CTS-IIE-PANZER", "cetus medium tank", 2, 2, 3, 0, "TRACKED", "", "",
                                  "anti tank rifle", "machinegun", [2, 2], 25,
                                  ["RADIO", "COMMAND_RADIO", "OPEN_TOP", "COMMANDER"], "SUPPORT", 1, 5],
        "HRR_medium_escort_tank": ["CTS-IIS-PANZER", "cetus medium tank", 2, 2, 2, 1, "TRACKED", "light gun",
                                   "machinegun", "", "", [3, 2], 25, ["RADIO", "COMMANDER", "", ""], "HOLD", 2, 5],
        "HRR_aquatic_truck_scout": ["CND-VE-CARRO", "canard truck", 2, 1, 1, 1, "WHEELED", "anti tank rifle",
                                    "machinegun", "", "", [2, 1], 30, ["RADIO", "COMMANDER", "", ""], "HOLD", 2, 6],
        "HRR_aquatic_truck_radio": ["CND-VR-APPARAT", "canard truck", 2, 1, 1, 0, "WHEELED", "", "", "machinegun", "",
                                    [2, 1], 25, ["RADIO", "TACTICAL_RADIO", "COMMANDER", ""], "JAMMER", 2, 5],
        "HRR_aquatic_truck_cargo": ["CND-VN-CARRO", "canard truck", 2, 1, 1, 0, "WHEELED", "", "", "", "", [1, 1], 25,
                                    ["STORAGE", "OPEN_TOP", "", ""], "SUPPLY", 0, 5],
        "HRR_aquatic_truck_hauler": ["CND-VN-CARRO", "canard truck", 2, 1, 1, 0, "WHEELED", "", "", "", "", [1, 1], 25,
                                     ["OPEN_TOP", "", "", ""], "HOLD", 0, 5],
        "HRR_primitive_tank_1": ["PST-I-PANZER", "pristis tank", 1, 1, 3, 1, "TRACKED", "medium gun", "", "short gun",
                                 "short gun", [3, 1], 30, ["RIVETS", "LOADER", "", ""], "HOLD", 4, 6],
        "HRR_primitive_tank_2": ["PST-II-PANZER", "pristis tank", 1, 1, 3, 1, "TRACKED", "medium autocannon",
                                 "medium autocannon", "medium gun", "medium machinegun", [3, 1], 30,
                                 ["RIVETS", "COMMANDER", "", ""], "HOLD", 4, 6],
        "HRR_landing_vehicle_1": ["SQS-I-TANSPORTEUR", "squalus landing vehicle", 1, 1, 1, 0, "TRACKED", "", "", "", "",
                                  [1, 1], 30, ["STORAGE", "OPEN_TOP", "", ""], "SUPPLY", 0, 6],
        "HRR_landing_vehicle_2": ["SQS-II-TANSPORTEUR", "squalus landing vehicle", 1, 1, 1, 0, "TRACKED", "medium gun",
                                  "machinegun", "", "", [2, 1], 30, ["RADIO", "COMMANDER", "LOADER", ""], "ARTILLERY",
                                  3, 6],
        "HRR_landing_vehicle_3": ["SQS-III-TANSPORTEUR", "squalus landing vehicle", 1, 1, 1, 1, "TRACKED", "", "",
                                  "short gun", "medium autocannon", [2, 1], 30, ["RADIO", "COMMANDER", "LOADER", ""],
                                  "HOLD", 3, 6],
        "HRR_infantry_mortar": ["PVS-MORTIER", "light mortar", 1, 1, 1, 0, "GUN_CARRIAGE", "", "",
                                "light breech mortar", "", [0, 0], 10, ["LOADER", "", "", ""], "ARTILLERY", 1, 2],
        "HRR_heavy_infantry_mortar": ["MGN-MORTIER", "heavy mortar", 1, 1, 1, 0, "GUN_CARRIAGE", "", "",
                                      "breech mortar", "", [0, 0], 20, ["LOADER", "", "", ""], "ARTILLERY", 1, 4],
        "HRR_infantry_mg": ["MGN-MACHINENTELUM", "machine gun", 1, 1, 1, 0, "GUN_CARRIAGE", "", "", "medium machinegun",
                            "", [1, 0], 10, ["LOADER", "", "", ""], "HOLD", 1, 2],
        "HRR_infantry_autocannon": ["MGN-CELERITELUM", "light autocannon", 1, 1, 1, 0, "GUN_CARRIAGE", "", "",
                                    "medium autocannon", "", [0, 0], 15, ["LOADER", "", "", ""], "HOLD", 1, 3],
        "HRR_infantry_anti_tank": ["PVS-PANZERKANON", "anti tank rifle", 1, 1, 1, 0, "GUN_CARRIAGE", "", "",
                                   "anti tank rifle", "", [0, 0], 15, ["LOADER", "", "", ""], "HOLD", 1, 3],
        "HRR_static_anti_air_gun": ["PVS-LUFTTELUM", "anti air gun", 0, 0, 1, 1, "GUN_CARRIAGE", "medium autocannon",
                                    "", "", "", [1, 0], 20, ["AA_TURRET", "LOADER", "", ""], "ANTI_AIR", 1, 4],
        "HRR_infantry_gun": ["PVS-INFANTRIEKANON", "light autocannon", 1, 1, 1, 0, "GUN_CARRIAGE", "", "", "short gun",
                             "", [0, 0], 15, ["LOADER", "", "", ""], "HOLD", 1, 3],
        "VIN_primitive_tank_3": ["JT-4-KAMPV", "jotun tank", 1, 1, 3, 0, "TRACKED", "", "", "short gun",
                                 "medium machinegun", [2, 1], 30, ["RIVETS", "", "", ""], "HOLD", 2, 6],
        "VIN_primitive_gun_carrier": ["JN-2-KANON", "jotun gun carrier", 1, 1, 3, 1, "TRACKED", "light artillery", "",
                                      "", "", [1, 1], 30, ["RIVETS", "ARTILLERY_TURRET", "", ""], "ARTILLERY", 4, 6],
        "VIN_scout_tank_1": ["KR-1-KAMPV", "kylling scout tank", 2, 2, 2, 1, "TRACKED", "short gun", "", "", "", [2, 1],
                             20, ["RIVETS", "", "", ""], "HOLD", 2, 4],
        "VIN_scout_gun_1": ["GN-1-KANON", "ged scout gun", 2, 2, 2, 0, "TRACKED", "", "", "medium gun", "", [1, 1], 15,
                            ["RIVETS", "OPEN_TOP", "", ""], "HOLD", 2, 3],
        "VIN_scout_car_1": ["DF-2-VOGN", "dverg scout car", 3, 1, 1, 1, "WHEELED", "medium autocannon",
                            "anti tank rifle", "", "", [1, 1], 25, ["RADIO", "PERISCOPE", "", ""], "JAMMER", 2, 5],
        "VIN_scout_car_2": ["DF-6-VOGN", "dverg scout car", 3, 1, 1, 1, "WHEELED", "light autocannon", "",
                            "medium machinegun", "", [1, 1], 25, ["RADIO", "TACTICAL_RADIO", "COMMANDER", ""], "JAMMER",
                            2, 5],
        "VIN_light_tank_1": ["HF-1-KAMPV", "huginn light tank", 2, 2, 3, 1, "TRACKED", "light gun", "",
                             "medium machinegun", "", [3, 2], 25, ["RADIO", "RIVETS", "COMMANDER", ""], "HOLD", 2, 5],
        "VIN_command_tank_1": ["MP-1-KOMMANDO", "muninn command tank", 2, 2, 3, 0, "TRACKED", "", "", "anti tank rifle",
                               "medium machinegun", [2, 2], 20, ["RADIO", "COMMAND_RADIO", "RIVETS", "COMMANDER"],
                               "SUPPORT", 1, 4],
        "VIN_large_gun_tank_1": ["UN3-KANON", "ullr gun carrier", 1, 1, 2, 0, "TRACKED", "", "", "light artillery",
                                 "medium machinegun", [4, 2], 30, ["RADIO", "RIVETS", "LOADER", ""], "HOLD", 3, 6],
        "VIN_large_tank_1": ["TK-1-KAMPV", "thrud large tank", 1, 1, 2, 1, "TRACKED", "medium gun", "light autocannon",
                             "medium machinegun", "", [3, 2], 30, ["RADIO", "RIVETS", "COMMANDER", ""], "HOLD", 3, 6],
        "VIN_aa_truck": ["RD-1-KANON", "rati truck", 2, 1, 1, 1, "WHEELED", "light autocannon", "", "", "", [0, 0], 30,
                         ["RADIO", "AA_TURRET", "", ""], "HOLD", 4, 6],
        "VIN_medium_truck_cargo": ["LASTBIL-1", "lastbil truck", 2, 1, 1, 0, "WHEELED", "", "", "", "", [0, 0], 25,
                                   ["STORAGE", "LOADER", "", ""], "SUPPLY", 0, 5],
        "VIN_medium_truck_hauler": ["LASTBIL-1", "lastbil truck", 2, 1, 1, 0, "WHEELED", "", "", "", "", [0, 0], 25,
                                    ["", "", "", ""], "HOLD", 0, 5],
        "VIN_large_truck_cargo": ["LASTVOGN-1", "lastvogn truck", 2, 1, 1, 0, "WHEELED", "", "", "", "", [0, 0], 30,
                                  ["STORAGE", "", "", ""], "SUPPLY", 0, 6],
        "VIN_radio_truck": ["LASTBIL-KOMANDO", "lastbil car", 3, 1, 1, 0, "WHEELED", "", "", "", "", [0, 0], 20,
                            ["RADIO", "AIR_FORCE_RADIO", "", ""], "AIR_SUPPORT", 0, 4],
        "VIN_medium_support_gun": ["BN-29-ARTILLERI", "support gun", 0, 0, 1, 0, "GUN_CARRIAGE", "", "",
                                   "light artillery", "", [1, 0], 25, ["RADIO", "LOADER", "", ""], "ARTILLERY", 1, 5],
        "VIN_medium_anti_tank_gun": ["KN-23-KANON ", "medium gun", 1, 1, 1, 0, "GUN_CARRIAGE", "", "", "medium gun", "",
                                     [1, 0], 25, ["LOADER", "", "", ""], "HOLD", 1, 5],
        "VIN_light_anti_tank_gun": ["NN-11-KANON", "light gun", 1, 1, 1, 0, "GUN_CARRIAGE", "", "", "light gun", "",
                                    [1, 0], 15, ["LOADER", "", "", ""], "HOLD", 1, 3],
        "VIN_prototype_rockets": ["RKN-15-RAKETKAST", "rocket launcher", 1, 1, 1, 0, "GUN_CARRIAGE", "", "",
                                  "primitive rockets", "", [0, 0], 15, ["LOADER", "", "", ""], "ARTILLERY", 1, 3],
        "VIN_static_anti_air_gun": ["RI-07-LUFTKANON", "anti air gun", 0, 0, 1, 1, "GUN_CARRIAGE", "light autocannon",
                                    "", "", "", [1, 0], 20, ["RADIO", "AA_TURRET", "LOADER", ""], "ANTI_AIR", 1, 4],
        "VIN_infantry_mortar": ["GN-23-GRENATKAST", "light mortar", 1, 1, 1, 0, "GUN_CARRIAGE", "", "",
                                "light breech mortar", "", [0, 0], 10, ["LOADER", "", "", ""], "ARTILLERY", 1, 2],
        "VIN_infantry_mg": ["MR-05-MASKINGEVAER", "machine gun", 1, 1, 1, 0, "GUN_CARRIAGE", "", "",
                            "medium machinegun", "", [0, 0], 10, ["LOADER", "", "", ""], "HOLD", 1, 2]}

    titles = ["display_name",
              "description",
              "on_road",
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
              "ai_default",
              "ammo",
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

            if title == "ammo":
                entry *= 100

            entry_dict[title] = entry

        new_dict[dict_key] = entry_dict

    with open(out_path, "w") as outfile:
        json.dump(new_dict, outfile)


def build_infantry():
    infantry = {"rm": ["RIFLE", "rifleman", 10, 6, "HOLD", ["RIFLES", "EXTRA_GRENADES", "PLACE_MINES", ""]],
                "sm": ["SMG", "shock troops", 15, 4, "AGGRESSIVE", ["SMG", "EXTRA_GRENADES", "SATCHEL_CHARGE", ""]],
                "mg": ["MG", "machine-gunner", 15, 2, "HOLD", ["SUPPORT_FIRE", "", "", ""]],
                "hg": ["MG", "heavy-machine-gunner", 15, 2, "HOLD", ["HEAVY_SUPPORT_FIRE", "DAMAGE_TRACKS", "", ""]],
                "at": ["ANTI_TANK", "anti-tank rifleman", 15, 2, "HOLD", ["HEAVY_RIFLES", "DAMAGE_TRACKS", "", ""]],
                "en": ["ENGINEER", "engineer", 10, 2, "HOLD", ["SIDE_ARMS", "REPAIR", "PLACE_MINES", ""]],
                "gr": ["RIFLE", "grenadier", 15, 3, "HOLD", ["RIFLES", "RIFLE_GRENADE", "", ""]],
                "gc": ["ENGINEER", "crewman", 10, 5, "HOLD", ["SIDE_ARMS", "CREW", "SATCHEL_CHARGE", ""]],
                "mk": ["RIFLE", "marksman", 10, 3, "FLANKING", ["SNIPER_RIFLES", "SPOTTING", "", ""]],
                "ht": ["ANTI_TANK", "heavy anti-tank", 15, 2, "HOLD", ["HEAVY_RIFLES", "DAMAGE_TRACKS", "", ""]],
                "pt": ["RIFLE", "paratrooper", 15, 5, "AGGRESSIVE", ["ASSAULT_RIFLES", "PLACE_MINES", "SPOTTING", ""]],
                "cm": ["OFFICER", "commander", 20, 1, "JAMMER", ["SIDE_ARMS", "SPOTTING", "", ""]]}

    titles = ["mesh",
              "display_name",
              "toughness",
              "number",
              "ai_default",
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

                entry = action_strings

            entry_dict[title] = entry

        if extra_grenades:
            entry_dict["ammo"] = 400
        else:
            entry_dict["ammo"] = 200

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
                     30: ["extra loader", "module", 1, 2, 0, 6, 0, "", ["loader", ""], "description goes here"],
                     31: ["improved transmission", "utility", 1, 1, 0, 6, 0, "", ["transmission", ""],
                          "description goes here"],
                     32: ["armored cupola", "utility", 1, 1, 0, 6, 0, "", ["cupola", ""], "description goes here"],
                     33: ["medium machinegun", "weapon", 1, 1, 0, 6, 2, "", ["burst_fire", "secondary"],
                          "description goes here"],
                     34: ["machinegun", "weapon", 1, 1, 0, 6, 1, "", ["rapid_fire", "secondary"],
                          "description goes here"],
                     35: ["quad machineguns", "weapon", 1, 2, 0, 6, 1, "", ["rapid_fire", "quad_mount"],
                          "description goes here"],
                     36: ["heavy machinegun", "weapon", 1, 1, 0, 6, 2, "", ["rapid_fire", "secondary"],
                          "description goes here"],
                     37: ["quad heavy machineguns", "weapon", 1, 2, 0, 6, 2, "", ["rapid_fire", "quad_mount"],
                          "description goes here"],
                     38: ["medium autocannon", "weapon", 1, 2, 0, 6, 3, "", ["burst_fire", "jam"],
                          "description goes here"],
                     39: ["light autocannon", "weapon", 1, 2, 0, 6, 2, "", ["rapid_fire", "secondary"],
                          "description goes here"],
                     40: ["quad light autocannon", "weapon", 1, 3, 0, 6, 2, "", ["rapid_fire", "quad_mount"],
                          "description goes here"],
                     41: ["heavy autocannon", "weapon", 1, 2, 0, 6, 4, "", ["burst_fire", "jam"],
                          "description goes here"],
                     42: ["twin heavy autocannon", "weapon", 1, 3, 0, 6, 4, "", ["burst_fire", "twin_mount"],
                          "description goes here"],
                     43: ["anti tank rifle", "weapon", 1, 1, 0, 6, 3, "", ["at2", "quick"], "description goes here"],
                     44: ["short gun", "weapon", 1, 3, 0, 6, 5, "", ["cheap", "slow"], "description goes here"],
                     45: ["light gun", "weapon", 1, 2, 0, 6, 4, "", ["at1", "quick"], "description goes here"],
                     46: ["squeeze gun", "weapon", 1, 2, 0, 6, 4, "", ["at2", "jam"], "description goes here"],
                     47: ["medium gun", "weapon", 1, 3, 0, 6, 6, "", ["cheap", "slow"], "description goes here"],
                     48: ["quick firing gun", "weapon", 1, 3, 0, 6, 5, "", ["quick", ""], "description goes here"],
                     49: ["high velocity gun", "weapon", 2, 2, 0, 6, 5, "", ["at2", ""], "description goes here"],
                     50: ["heavy gun", "weapon", 2, 2, 0, 6, 8, "", ["slow", ""], "description goes here"],
                     51: ["advanced gun", "weapon", 1, 4, 0, 6, 7, "", ["at2", ""], "description goes here"],
                     52: ["compact gun", "weapon", 1, 2, 0, 6, 8, "", ["jam", "slow"], "description goes here"],
                     53: ["all purpose gun", "weapon", 2, 2, 0, 6, 9, "", ["at1", "quick"], "description goes here"],
                     54: ["support gun", "weapon", 1, 3, 0, 6, 7, "", ["indirect", "slow"], "description goes here"],
                     55: ["heavy support gun", "weapon", 1, 4, 0, 6, 14, "", ["indirect", "very_slow"],
                          "description goes here"],
                     56: ["light artillery", "weapon", 1, 4, 0, 6, 8, "", ["artillery", "very_slow"],
                          "description goes here"],
                     57: ["artillery", "weapon", 1, 5, 0, 6, 10, "", ["artillery", "slow"], "description goes here"],
                     58: ["heavy artillery", "weapon", 2, 3, 0, 6, 15, "", ["artillery", "very_slow"],
                          "description goes here"],
                     59: ["super heavy gun", "weapon", 2, 3, 0, 6, 12, "", ["at1", "very_slow"],
                          "description goes here"],
                     60: ["breech mortar", "weapon", 1, 1, 0, 6, 8, "", ["mortar", "slow"], "description goes here"],
                     61: ["heavy breech mortar", "weapon", 1, 2, 0, 6, 12, "", ["mortar", "slow"],
                          "description goes here"],
                     62: ["light breech mortar", "weapon", 1, 1, 0, 6, 4, "", ["mortar", ""], "description goes here"],
                     63: ["primitive rockets", "weapon", 2, 3, 0, 6, 4, "", ["rocket", "small"],
                          "description goes here"],
                     64: ["small rockets", "weapon", 2, 2, 0, 6, 6, "", ["rocket", "small"], "description goes here"],
                     65: ["large rockets", "weapon", 2, 3, 0, 6, 12, "", ["rocket", "large"], "description goes here"],
                     66: ["medium rockets", "weapon", 2, 2, 0, 6, 9, "", ["rocket", "medium"], "description goes here"],
                     67: ["anti mine coating", "module", 1, 1, 0, 6, 0, "", ["anti_mine", ""], "description goes here"],
                     68: ["engine turbocharger", "module", 1, 1, 0, 6, 0, "", ["turbocharger", ""],
                          "description goes here"],
                     69: ["engine dust filters", "module", 1, 1, 0, 6, 0, "", ["filters", ""], "description goes here"],
                     70: ["improved radiator", "module", 1, 1, 0, 6, 0, "", ["radiator", ""], "description goes here"],
                     71: ["wide tracks", "module", 1, 1, 0, 6, 0, "", ["wide_tracks", ""], "description goes here"],
                     72: ["individual radio", "module", 1, 1, 0, 6, 0, "", ["individual_radio", ""],
                          "description goes here"],
                     73: ["tactical radio", "module", 1, 1, 0, 6, 0, "", ["tactical_radio", ""],
                          "description goes here"],
                     74: ["air force radio", "module", 1, 1, 0, 6, 0, "", ["air_force_radio", ""],
                          "description goes here"],
                     75: ["command radio", "module", 1, 1, 0, 6, 0, "", ["command_radio", ""], "description goes here"],
                     76: ["commander", "module", 1, 1, 0, 6, 0, "", ["commander", ""], "description goes here"],
                     77: ["modular engine bay", "module", 1, 1, 0, 6, 0, "", ["easy_repair", ""],
                          "description goes here"],
                     78: ["engine block heater", "module", 1, 1, 0, 6, 0, "", ["heater", ""], "description goes here"],
                     79: ["extra escape hatches", "module", 1, 1, 0, 6, 0, "", ["escape_hatches", ""],
                          "description goes here"],
                     80: ["applique armor plates", "module", 1, 1, 0, 6, 0, "", ["extra_plates", ""],
                          "description goes here"],
                     81: ["grenade net", "module", 1, 1, 0, 6, 0, "", ["net", ""], "description goes here"],
                     82: ["fire extinguishers", "module", 1, 1, 0, 6, 0, "", ["extinquishers", ""],
                          "description goes here"],
                     83: ["wet ammo storage", "module", 1, 1, 0, 6, 0, "", ["wet_ammo", ""], "description goes here"],
                     84: ["improved weapon sights", "module", 1, 1, 0, 6, 0, "", ["sights", ""],
                          "description goes here"],
                     85: ["semiautomatic breech", "module", 1, 1, 0, 6, 0, "", ["quick_reload", ""],
                          "description goes here"],
                     86: ["periscope", "module", 1, 1, 0, 6, 0, "", ["periscope", ""], "description goes here"],
                     87: ["armor skirts", "module", 1, 1, 0, 6, 0, "", ["skirts", ""], "description goes here"],
                     88: ["repair tools", "module", 1, 1, 0, 6, 0, "", ["tools", ""], "description goes here"],
                     89: ["engine noise reducer", "module", 1, 1, 0, 6, 0, "", ["silencer", ""],
                          "description goes here"],
                     90: ["armor hardening", "module", 1, 1, 0, 6, 0, "", ["hardening", ""], "description goes here"],
                     91: ["sandbags", "module", 1, 1, 0, 6, 0, "", ["sandbags", ""], "description goes here"],
                     92: ["analog computer", "module", 1, 1, 0, 6, 0, "", ["computer", ""], "description goes here"]}

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
            small_caliber = rating < 4
            large_caliber = rating > 6
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

            multi_shot = burst_fire or rapid_fire

            if twin_mount:
                weapon["shots"] = 2
            elif quad_mount:
                weapon["shots"] = 4
            else:
                weapon["shots"] = 1

            if jamming:
                jamming_chance = 2
            else:
                jamming_chance = 1

            weapon["jamming_chance"] = jamming_chance

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
                if mortar:
                    weapon_actions.append("RANGED_SUPPORT_FIRE")
                    if not very_slow:
                        weapon_actions.append("CLOSE_SUPPORT_FIRE")
                    if large_caliber:
                        weapon_actions.append("SMOKE_SHELLS")

                if indirect:
                    weapon_actions.append("RANGED_SUPPORT_FIRE")
                    if not very_slow:
                        weapon_actions.append("CLOSE_SUPPORT_FIRE")
                    weapon_actions.append("SHOOT")
                    weapon_actions.append("HIGH_EXPLOSIVE")
                    if large_caliber:
                        weapon_actions.append("SMOKE_SHELLS")

                if artillery:
                    weapon_actions.append("HIGH_EXPLOSIVE")
                    weapon_actions.append("ARTILLERY_SHOT")
                    weapon_actions.append("ZEROED_ARTILLERY")
                    if large_caliber:
                        weapon_actions.append("SMOKE_SHELLS")

            elif multi_shot:
                if rapid_fire:
                    weapon_actions.append("RAPID_BURST")
                    weapon_actions.append("SUPPRESSING_FIRE")
                else:
                    weapon_actions.append("BURST_FIRE")

            else:
                weapon_actions.append("SHOOT")
                if anti_tank_1 or anti_tank_2:
                    if not very_slow:
                        weapon_actions.append("CALLED_SHOT")
                        if large_caliber:
                            weapon_actions.append("TARGET_TRACKS")

                    if large_caliber:
                        weapon_actions.append("HIGH_EXPLOSIVE")

                    if anti_tank_1:
                        weapon_actions.append("ANTI_TANK")
                    if anti_tank_2:
                        weapon_actions.append("ARMOR_PIERCING")
                else:
                    weapon_actions.append("AIMED_SHOT")

                    if large_caliber:
                        weapon_actions.append("HIGH_EXPLOSIVE")

                    if quick:
                        weapon_actions.append("QUICK_FIRE")

            slow_actions = [large_caliber, slow, quad_mount, anti_tank_2]
            very_slow_actions = [very_slow]
            fast_actions = [quick, small_caliber]

            if True in fast_actions:
                base_actions = 0
                base_recharge = -2
            elif True in slow_actions:
                base_actions = 1
                base_recharge = 0
            elif True in very_slow_actions:
                base_actions = 1
                base_recharge = 3
            else:
                base_actions = 0
                base_recharge = 0

            weapon["base_recharge"] = base_recharge
            weapon["base_actions"] = base_actions

            if indirect or quad_mount:
                base_accuracy = 2
            elif anti_tank_1 or anti_tank_2:
                base_accuracy = 4
            else:
                base_accuracy = 3

            weapon["base_accuracy"] = base_accuracy

            weapon["actions"] = weapon_actions
            weapon["name"] = name_key
            weapon_dict[name_key] = weapon

        out_path = "D:/projects/vinland_1942/game_folder/saves/weapons.txt"

        with open(out_path, "w") as outfile:
            json.dump(weapon_dict, outfile)


def build_actions():
    action_items = {
        "BAIL_OUT": ["bail_out", "ORDERS", 1, 0, 0, "SELF", "BAILING_OUT", "NEVER", 0, 0, 0, 0, 0, 0, 0, ""],
        "CLEAR_JAM": ["cancel", "ORDERS", 1, 0, 0, "SELF", "CLEAR_JAM", "NORMAL", 0, 0, 0, 0, 0, 0, 0, ""],
        "CREW": ["crew", "ORDERS", 1, 0, 0, "FRIEND", "CREW", "SUPPLY", 0, 0, 0, 0, 0, 0, 0, ""],
        "DIRECT_ORDER": ["radio", "ORDERS", 2, 3, 1, "ALLIES", "DIRECT_ORDER", "DEFENSIVE_SUPPORT", 0, 0, 0, 0, 0, 0, 0,
                         ""],
        "ENTER_BUILDING": ["building", "ORDERS", 1, 0, 0, "BUILDING", "ENTER_BUILDING", "NEVER", 0, 0, 0, 0, 0, 0, 0,
                           ""],
        "FAST_RELOAD": ["supply", "ORDERS", 1, 6, 0, "SELF", "FAST_RELOAD", "NEVER", 0, 0, 0, 0, 0, 0, 0, ""],
        "COMMANDER": ["crew", "ORDERS", 1, 6, 1, "SELF", "COMMANDER", "NEVER", 0, 3, 0, 0, 0, 0, 0, ""],
        "LOAD_TROOPS": ["load", "ORDERS", 1, 0, 0, "FRIEND", "LOAD_TROOPS", "NEVER", 0, 0, 0, 0, 0, 0, 0, ""],
        "MARK_TARGET": ["aimed_shot", "ORDERS", 2, 3, 1, "ENEMY", "MARKING", "OFFENSIVE_SUPPORT", 0, 0, 0, 0, 0, 0, 0,
                        ""],
        "TARGET_RECOGNITION": ["spotting", "ORDERS", 2, 3, 1, "ENEMY", "RECOGNITION", "OFFENSIVE_SUPPORT", 0, 0, 0, 0,
                               0, 0, 0, ""],
        "RADIO_CONFUSION": ["jamming", "ORDERS", 2, 3, 1, "ENEMY", "CONFUSION", "OFFENSIVE_SUPPORT", 0, 0, 0, 0, 0, 0,
                            0, ""],
        "RADIO_JAMMING": ["jamming", "ORDERS", 2, 3, 1, "ENEMY", "RADIO_JAMMING", "OFFENSIVE_SUPPORT", 0, 0, 0, 0, 0, 0,
                          0, ""],
        "CHANGE_FREQUENCIES": ["radio", "ORDERS", 2, 0, 0, "SELF", "REMOVE_JAMMING", "NORMAL", 0, 0, 0, 0, 0, 0, 0, ""],
        "MOVE": ["move", "ORDERS", 0, 0, 0, "MOVE", "MOVE", "NORMAL", 0, 0, 0, 0, 0, 0, 0, ""],
        "OVERDRIVE": ["wheels", "ORDERS", 0, 3, 1, "SELF", "OVERDRIVE", "NEVER", 0, 3, 0, 0, 0, 0, 0, ""],
        "PLACE_MINES": ["mines", "ORDERS", 2, 1, 0, "SELF", "PLACE_MINE", "NEVER", 1, 0, 0, 0, 0, 0, 0, ""],
        "QUICK_MARCH": ["wheels", "ORDERS", 2, 3, 1, "ALLIES", "SET_QUICK_MARCH", "DEFENSIVE_SUPPORT", 0, 0, 0, 0, 0, 0,
                        0, ""],
        "RAPID_FIRE": ["rapid_fire", "ORDERS", 1, 4, 1, "SELF", "RAPID_FIRE", "DEFEND", 1, 3, 0, 0, 0, 0, 0, ""],
        "RECOVER_MORALE": ["crew", "ORDERS", 1, 0, 1, "ALLIES", "RECOVER", "DEFENSIVE_SUPPORT", 0, 0, 0, 0, 0, 0, 0,
                           ""],
        "REARM_AND_RELOAD": ["supply", "ORDERS", 1, 0, 0, "FRIEND", "RELOAD", "SUPPLY", 0, 0, 0, 0, 0, 0, 0, ""],
        "REMOVE_MINES": ["mines", "ORDERS", 2, 1, 0, "SELF", "REMOVE_MINE", "NORMAL", 1, 0, 0, 0, 0, 0, 0, ""],
        "REPAIR": ["repair", "ORDERS", 1, 0, 0, "FRIEND", "REPAIR", "SUPPLY", 0, 0, 0, 0, 0, 0, 0, ""],
        "FACE_TARGET": ["rotate", "ORDERS", 0, 0, 0, "MOVE", "ROTATE", "NORMAL", 0, 0, 0, 0, 0, 0, 0, ""],
        "REDEPLOY": ["rotate", "ORDERS", 1, 0, 0, "MOVE", "ROTATE", "NORMAL", 0, 0, 0, 0, 0, 0, 0, ""],
        "OVERWATCH": ["radio", "ORDERS", 2, 3, 0, "SELF", "SET_OVERWATCH", "DEFEND", 1, 0, 0, 0, 0, 0, 0, ""],
        "SPOTTING": ["spotting", "ORDERS", 2, 0, 0, "SELF", "SPOTTING", "NEVER", 1, 0, 0, 0, 0, 0, 0, ""],
        "STEADY_AIM": ["aimed_shot", "ORDERS", 1, 4, 1, "SELF", "STEADY_AIM", "DEFEND", 1, 3, 0, 0, 0, 0, 0, ""],
        "SPECIAL_AMMO": ["rapid_fire", "ORDERS", 1, 4, 1, "SELF", "SPECIAL_AMMO", "DEFEND", 1, 3, 0, 0, 0, 0, 0, ""],
        "TOGGLE_BUTTONED_UP": ["stance", "ORDERS", 1, 0, 0, "SELF", "TOGGLE_BUTTONED_UP", "NORMAL", 0, 0, 0, 0, 0, 0, 0,
                               ""],
        "TOGGLE_STANCE": ["stance", "ORDERS", 1, 0, 0, "SELF", "TOGGLE_PRONE", "NORMAL", 0, 0, 0, 0, 0, 0, 0, ""],
        "AMBUSH": ["spotting", "ORDERS", 2, 1, 0, "SELF", "TRIGGER_AMBUSH", "NEVER", 1, 0, 0, 0, 0, 0, 0, ""],
        "ANTI_AIRCRAFT_FIRE": ["aa_fire", "ORDERS", 2, 1, 0, "SELF", "TRIGGER_ANTI_AIRCRAFT", "ANTI_AIR", 1, 0, 0, 0, 0,
                               0, 0, ""],
        "UNLOAD_TROOPS": ["unload", "ORDERS", 1, 0, 0, "SELF", "UNLOAD_TROOPS", "NEVER", 1, 0, 0, 0, 0, 0, 0, ""],
        "SPOTTER_PLANE": ["camera", "ORDERS", 2, 12, 1, "AIRCRAFT", "SPOTTER_PLANE", "AIR_SUPPORT", 1, 0, 0, 0, 0, 0, 0,
                          ""],
        "PARADROP": ["paradrop", "ORDERS", 2, 12, 1, "AIRCRAFT", "DROP_TROOPS", "AIR_SUPPORT", 1, 0, 0, 0, 0, 0, 0, ""],
        "AIR_STRIKE": ["plane", "ORDERS", 2, 12, 1, "AIRCRAFT", "AIR_STRIKE", "AIR_SUPPORT", 1, 0, 0, 0, 0, 3, 0, ""],
        "ARTILLERY_SHOT": ["explosion", "WEAPON", 1, 0, 0, "MAP", "ARTILLERY_EXPLOSION", "ARTILLERY", 0, 0, 0.8, 0.5, 2,
                           1, 2, ""],
        "ZEROED_ARTILLERY": ["zeroed", "WEAPON", 1, 3, 1, "MAP", "ARTILLERY_EXPLOSION", "ARTILLERY", 0, 0, 1, 0.5, 2, 1,
                             2, ""],
        "RANGED_SUPPORT_FIRE": ["explosion", "WEAPON", 1, 3, 0, "MAP", "ARTILLERY_EXPLOSION", "ARTILLERY", 0, 0, 0.1,
                                0.5, 1.5, 1, 2, ""],
        "CLOSE_SUPPORT_FIRE": ["zeroed", "WEAPON", 1, 0, 0, "ENEMY", "ARTILLERY_EXPLOSION", "DIRECT_ATTACK", 0, 0, 1,
                               0.5, 1.5, 1, 2, ""],
        "HIGH_EXPLOSIVE": ["explosion", "WEAPON", 1, 1, 0, "ENEMY", "HIT_SPLASH", "DIRECT_ATTACK", 0, 0, 0.8, 0.5, 2, 1,
                           2, ""],
        "THROW_GRENADE": ["grenade", "WEAPON", 2, 3, 0, "ENEMY", "GRENADE_EXPLOSION", "DIRECT_ATTACK", 0, 0, 0.6, 2, 2,
                          1, 4, ""],
        "SATCHEL_CHARGE": ["explosion", "WEAPON", 2, 3, 0, "ENEMY", "GRENADE_EXPLOSION", "DIRECT_ATTACK", 0, 0, 0, 4, 4,
                           1, 6, ""],
        "RIFLE_GRENADE": ["rifles", "WEAPON", 2, 0, 0, "ENEMY", "HIT_SPLASH", "DIRECT_ATTACK", 0, 0, 0.8, 2, 4, 1, 4,
                          ""],
        "SHOOT": ["shoot", "WEAPON", 1, 0, 0, "ENEMY", "HIT", "DIRECT_ATTACK", 0, 0, 1, 1.2, 1.2, 1, 1, ""],
        "RIFLES": ["rifles", "WEAPON", 2, 0, 0, "ENEMY", "HIT", "DIRECT_ATTACK", 0, 0, 1.5, 1, 1, 2, 2, ""],
        "SNIPER_RIFLES": ["aimed_shot", "WEAPON", 2, 0, 0, "ENEMY", "HIT", "DIRECT_ATTACK", 0, 0, 2, 2, 3, 1, 1, ""],
        "ASSAULT_RIFLES": ["rifles", "WEAPON", 1, 0, 0, "ENEMY", "HIT", "DIRECT_ATTACK", 0, 0, 1, 0, 1, 3, 1, ""],
        "HEAVY_RIFLES": ["rifles", "WEAPON", 2, 0, 0, "ENEMY", "HIT", "DIRECT_ATTACK", 0, 0, 1.2, 4, 4, 2, 4, ""],
        "SMG": ["smg", "WEAPON", 1, 0, 0, "ENEMY", "HIT", "DIRECT_ATTACK", 0, 0, 1, 0, 1, 4, 1, ""],
        "SIDE_ARMS": ["side_arms", "WEAPON", 1, 0, 0, "ENEMY", "HIT", "DIRECT_ATTACK", 0, 0, 0.8, 0, 1, 3, 1, ""],
        "SUPPORT_FIRE": ["support_fire", "WEAPON", 2, 0, 0, "ENEMY", "HIT", "DIRECT_ATTACK", 0, 0, 1, 1, 1, 12, 1, ""],
        "HEAVY_SUPPORT_FIRE": ["support_fire", "WEAPON", 2, 0, 0, "ENEMY", "HIT", "DIRECT_ATTACK", 0, 0, 1, 2, 2, 9, 1,
                               ""],
        "DAMAGE_TRACKS": ["tracks", "WEAPON", 2, 3, 0, "ENEMY", "HIT_TRACKS", "DIRECT_ATTACK", 0, 0, 1, 1, 1, 2, 1, ""],
        "BURST_FIRE": ["rapid_fire", "WEAPON", 1, 0, 0, "ENEMY", "HIT", "DIRECT_ATTACK", 0, 0, 1, 1, 1, 4, 1, ""],
        "RAPID_BURST": ["rapid_fire", "WEAPON", 1, 0, 0, "ENEMY", "HIT", "DIRECT_ATTACK", 0, 0, 1, 1, 1, 6, 1, ""],
        "ANTI_TANK": ["anti_tank", "WEAPON", 1, 0, 0, "ENEMY", "HIT", "DIRECT_ATTACK", 0, 0, 1.2, 1.8, 1, 1, 1, ""],
        "AIMED_SHOT": ["aimed_shot", "WEAPON", 1, 3, 0, "ENEMY", "HIT", "DIRECT_ATTACK", 0, 0, 1.5, 1.2, 1.2, 1, 1, ""],
        "CALLED_SHOT": ["aimed_shot", "WEAPON", 1, 3, 1, "ENEMY", "HIT", "DIRECT_ATTACK", 0, 0, 1, 1.2, 1, 1, 4, ""],
        "QUICK_FIRE": ["rapid_fire", "WEAPON", 0, 3, 1, "ENEMY", "HIT", "DIRECT_ATTACK", 0, 0, 1, 1, 1, 1, 1, ""],
        "ARMOR_PIERCING": ["aimed_shot", "WEAPON", 1, 0, 0, "ENEMY", "HIT", "DIRECT_ATTACK", 0, 0, 1.2, 2.2, 1, 1, 2,
                           ""],
        "SUPPRESSING_FIRE": ["rapid_fire", "WEAPON", 1, 3, 1, "ENEMY", "HIT", "DIRECT_ATTACK", 0, 0, 0.8, 1, 1, 8, 2,
                             ""],
        "TARGET_TRACKS": ["tracks", "WEAPON", 1, 3, 1, "ENEMY", "HIT_TRACKS", "DIRECT_ATTACK", 0, 0, 0.8, 1, 1, 1, 1,
                          ""],
        "SMALL_ROCKETS": ["rockets", "WEAPON", 1, 3, 0, "MAP", "ROCKET_EXPLOSION", "ARTILLERY", 1, 0, 0.6, 0.5, 1.5, 12,
                          3, ""],
        "MEDIUM_ROCKETS": ["rockets", "WEAPON", 1, 3, 0, "MAP", "ROCKET_EXPLOSION", "ARTILLERY", 1, 0, 0.3, 0.5, 2, 9,
                           3, ""],
        "LARGE_ROCKETS": ["rockets", "WEAPON", 1, 3, 0, "MAP", "ROCKET_EXPLOSION", "ARTILLERY", 1, 0, 0, 0.5, 2.5, 6, 3,
                          ""],
        "SMOKE_ROCKETS": ["smoke", "WEAPON", 1, 3, 1, "MAP", "ROCKET_SMOKE", "SMOKE", 1, 0, 0.3, 0, 0, 6, 0, ""],
        "SMOKE_SHELLS": ["smoke", "WEAPON", 1, 1, 1, "MAP", "SMOKE", "SMOKE", 0, 0, 0.6, 0, 0, 1, 0, ""]}

    titles = ["icon",
              "action_type",
              "action_cost",
              "recharge_time",
              "radio_points",
              "target",
              "effect",
              "ai_tactics",
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


def ai_labels():
    ai_painter = {"OBJECTIVE_ATTACK": ["ATTACK TARGET", 0, ""],
                  "OBJECTIVE_DEFEND": ["DEFEND TARGET", 0, ""],
                  "OBJECTIVE_SALVAGE": ["SALVAGE EQUIPMENT", 2, ""],
                  "OBJECTIVE_ESCORT": ["ESCORT TRUCKS", 0, ""],
                  "OBJECTIVE_DESTROY": ["DESTROY ENEMY HEADQUARTERS", 0, ""],
                  "OBJECTIVE_AMBUSH": ["FIND AMBUSH SITE", 1, ""],
                  "OBJECTIVE_CAPTURE": ["CAPTURE TARGET", 0, ""],
                  "OBJECTIVE_SEARCH": ["SEARCH AND DESTROY", 1, ""],
                  "OBJECTIVE_RESERVES": ["ENEMY RESERVES", 1, ""],
                  "OBJECTIVE_CAVALRY": ["WAIT FOR REINFORCEMENTS", 1, ""],
                  "OBJECTIVE_RETREAT": ["RETREAT ALL UNITS", 0, ""],
                  "OBJECTIVE_CUT_OFF_RETREAT": ["CUT OFF ENEMY RETREAT", 0, ""],
                  "OBJECTIVE_MINIMAL_CASUALTIES": ["KEEP CASUALTIES LOW", 2, ""],
                  "OBJECTIVE_NO_AIR_SUPPORT": ["NO AIR SUPPORT", 1, ""],
                  "OBJECTIVE_CAPTURE_SUPPLIES": ["CAPTURE ALL SUPPLY DUMPS", 1, ""],
                  "OBJECTIVE_CLEAN_UP": ["ELIMINATE ALL ENEMY TROOPS", 2, ""],
                  "OBJECTIVE_SURVIVAL": ["SURVIVE ALL ATTACKS", 1, ""],
                  "OBJECTIVE_MINES": ["CLEAR MINE FIELD", 0, ""],
                  "MODIFIER_TIMER_0_TURNS": ["TIMER 0 TURNS", -1, ""],
                  "MODIFIER_TIMER_15_TURNS": ["TIMER 15 TURNS", 15, ""],
                  "MODIFIER_TIMER_30_TURNS": ["TIMER 30 TURNS", 30, ""],
                  "MODIFIER_TIMER_45_TURNS": ["TIMER 45 TURNS", 45, ""],
                  "MODIFIER_TIMER_60_TURNS": ["TIMER 60 TURNS", 60, ""],
                  "MODIFIER_HIDDEN_TIME_LIMIT": ["HIDDEN TIME LIMIT", 0, ""],
                  "MODIFIER_HIDDEN_OBJECTIVE": ["HIDDEN OBJECTIVE", 0, ""],
                  "BEHAVIOR_ATTACK": ["ATTACK", -1, ""],
                  "BEHAVIOR_DEFEND": ["DEFEND", -1, ""],
                  "BEHAVIOR_HOLD": ["HOLD", -1, ""],
                  "BEHAVIOR_GO_TO": ["GO TO", -1, ""],
                  "BEHAVIOR_SCOUT": ["SCOUT", -1, ""],
                  "BEHAVIOR_SUPPORT": ["SUPPORT", -1, ""],
                  "BEHAVIOR_ARTILLERY": ["ARTILLERY", -1, ""],
                  "BEHAVIOR_AMBUSH": ["AMBUSH", -1, ""],
                  "BEHAVIOR_AIR_SUPPORT": ["AIR SUPPORT", -1, ""],
                  "BEHAVIOR_SUPPLY": ["SUPPLY", -1, ""],
                  "BEHAVIOR_ADVANCE": ["ADVANCE", -1, ""],
                  "BEHAVIOR_FLANKING": ["FLANKING", -1, ""],
                  "BEHAVIOR_AGGRESSIVE": ["AGGRESSIVE", -1, ""],
                  "AGENT_EFFECT_BAILED_OUT": ["BAILED OUT", -1, ""],
                  "AGENT_EFFECT_DAMAGED": ["DAMAGED", -1, ""],
                  "AGENT_EFFECT_OUT_OF_AMMO": ["OUT OF AMMO", -1, ""],
                  "BEHAVIOR_JAMMER": ["JAMMER", -1, ""],
                  "AGENT_EFFECT_RAW_RECRUITS": ["RAW RECRUITS", -1, ""],
                  "AGENT_EFFECT_VETERANS": ["VETERANS", -1, ""],
                  "BEHAVIOR_ANTI_AIR": ["ANTI AIR", -1, ""],
                  "AGENT_EFFECT_BUTTONED_UP": ["BUTTONED UP", -1, ""],
                  "AGENT_EFFECT_STAY_PRONE": ["STAY PRONE", -1, ""],
                  "BEHAVIOR_CLEAR_MINES": ["CLEAR MINES", -1, ""],
                  "COLOR_INDEX_YELLOW_OBJECTIVE": ["YELLOW OBJECTIVE", 1, ""],
                  "COLOR_INDEX_GREEN_OBJECTIVE": ["GREEN OBJECTIVE", 2, ""],
                  "COLOR_INDEX_BLUE_OBJECTIVE": ["BLUE OBJECTIVE", 3, ""],
                  "COLOR_INDEX_RED_OBJECTIVE": ["RED OBJECTIVE", 4, ""],
                  "COLOR_INDEX_CYAN_OBJECTIVE": ["CYAN OBJECTIVE", 5, ""],
                  "COLOR_INDEX_ORANGE_OBJECTIVE": ["ORANGE OBJECTIVE", 6, ""],
                  "COLOR_INDEX_PINK_OBJECTIVE": ["PINK OBJECTIVE", 7, ""],
                  "COLOR_INDEX_WHITE_OBJECTIVE": ["WHITE OBJECTIVE", 8, ""],
                  "COLOR_TRIGGER_YELLOW_OBJECTIVE": ["YELLOW OBJECTIVE", 1, ""],
                  "COLOR_TRIGGER_GREEN_OBJECTIVE": ["GREEN OBJECTIVE", 2, ""],
                  "COLOR_TRIGGER_BLUE_OBJECTIVE": ["BLUE OBJECTIVE", 3, ""],
                  "COLOR_TRIGGER_RED_OBJECTIVE": ["RED OBJECTIVE", 4, ""],
                  "COLOR_TRIGGER_CYAN_OBJECTIVE": ["CYAN OBJECTIVE", 5, ""],
                  "COLOR_TRIGGER_ORANGE_OBJECTIVE": ["ORANGE OBJECTIVE", 6, ""],
                  "COLOR_TRIGGER_PINK_OBJECTIVE": ["PINK OBJECTIVE", 7, ""],
                  "COLOR_TRIGGER_WHITE_OBJECTIVE": ["WHITE OBJECTIVE", 8, ""],
                  "COLOR_INDEX_CLEAR": ["CLEAR", 9, ""],
                  "MAP_EFFECTS_BOUNDARY_POINT": ["BOUNDARY POINT", 0, ""],
                  "MAP_EFFECTS_NAV_POINT": ["NAV POINT", 0, ""]}

    titles = ["label", "flag", "description"]

    out_path = "D:/projects/vinland_1942/game_folder/saves/ai_painter.txt"
    new_dict = {}

    for dict_key in ai_painter:
        entries = ai_painter[dict_key]
        entry_dict = {}

        for t in range(len(titles)):
            title = titles[t]
            entry = entries[t]

            entry_dict[title] = entry

        new_dict[dict_key] = entry_dict

    with open(out_path, "w") as outfile:
        json.dump(new_dict, outfile)


def build_buildings():
    test_buildings = {"large_stone_1": ["large stone house", 2, 2, 1, 0, 3, 60, 1, "town"],
                      "large_stone_2": ["large stone house", 2, 3, 1, 0, 3, 70, 1, "town"],
                      "large_stone_3": ["large stone house", 2, 2, 1, 0, 3, 60, 1, "town"],
                      "large_stone_4": ["large stone house", 2, 2, 1, 0, 3, 50, 1, "town"],
                      "large_stone_5": ["large stone house", 2, 2, 1, 0, 3, 50, 1, "town"],
                      "large_shed_1": ["large shed", 3, 3, 1, 1, 2, 60, 1, "town"],
                      "large_shed_2": ["large shed", 3, 2, 1, 1, 2, 60, 1, "town"],
                      "large_shed_3": ["large shed", 2, 2, 1, 1, 2, 45, 1, "town"],
                      "large_shed_4": ["large shed", 3, 3, 1, 1, 3, 80, 1, "town"],
                      "large_shed_5": ["large shed", 3, 2, 1, 1, 3, 80, 1, "town"],
                      "large_shed_6": ["large shed", 3, 2, 1, 1, 2, 60, 1, "town"],
                      "large_shed_7": ["large shed", 3, 2, 1, 1, 2, 60, 1, "town"],
                      "long_stone_1": ["long stone house", 2, 2, 1, 0, 2, 45, 1, "town"],
                      "long_stone_2": ["long stone house", 2, 2, 1, 0, 2, 45, 1, "town"],
                      "long_stone_3": ["long stone house", 2, 2, 1, 0, 2, 45, 1, "town"],
                      "long_stone_4": ["long stone house", 2, 2, 1, 0, 2, 45, 1, "town"],
                      "long_stone_5": ["long stone house", 2, 2, 1, 0, 2, 45, 1, "town"],
                      "supplies_1": ["supplies", 1, 1, 0, 1, 1, 15, 0, "military"],
                      "supplies_2": ["supplies", 1, 1, 0, 1, 1, 15, 0, "military"],
                      "supplies_3": ["supplies", 1, 1, 0, 1, 1, 15, 0, "military"],
                      "supplies_4": ["supplies", 1, 1, 0, 1, 1, 15, 0, "military"],
                      "tents_1": ["tent", 1, 1, 1, 0, 1, 10, 0, "military"],
                      "tents_2": ["tent", 1, 1, 1, 0, 1, 10, 0, "military"],
                      "tents_3": ["tent", 1, 1, 1, 0, 1, 10, 0, "military"],
                      "tents_4": ["tent", 1, 1, 1, 0, 1, 10, 0, "military"],
                      "tents_5": ["tent", 2, 1, 1, 0, 1, 15, 0, "military"],
                      "tents_6": ["tent", 2, 1, 1, 0, 1, 15, 0, "military"],
                      "church_1": ["church", 3, 3, 1, 0, 3, 80, 1, "town"],
                      "church_2": ["church", 3, 3, 1, 0, 3, 80, 1, "town"],
                      "church_3": ["church", 3, 2, 1, 0, 3, 65, 1, "town"],
                      "church_4": ["church", 3, 2, 1, 0, 3, 65, 1, "town"],
                      "watchtower_1": ["watchtower", 1, 1, 1, 0, 4, 35, 0, "military"],
                      "watchtower_2": ["watchtower", 1, 1, 1, 0, 4, 35, 0, "military"],
                      "watchtower_3": ["watchtower", 1, 1, 1, 0, 4, 35, 0, "military"],
                      "watchtower_4": ["watchtower", 1, 1, 1, 0, 4, 35, 0, "military"],
                      "watchtower_5": ["watchtower", 1, 1, 1, 0, 4, 20, 0, "military"],
                      "watchtower_6": ["watchtower", 1, 1, 1, 0, 4, 20, 0, "military"],
                      "watchtower_7": ["watchtower", 1, 1, 1, 0, 4, 20, 0, "military"],
                      "watchtower_8": ["watchtower", 1, 1, 1, 0, 4, 20, 0, "military"],
                      "stone_house_1": ["stone house", 1, 1, 1, 0, 2, 40, 1, "town"],
                      "stone_house_2": ["stone house", 1, 1, 1, 0, 2, 40, 1, "town"],
                      "stone_house_3": ["stone house", 1, 1, 1, 0, 2, 40, 1, "town"],
                      "stone_house_4": ["stone house", 1, 1, 1, 0, 2, 40, 1, "town"],
                      "crates_1": ["crates", 1, 1, 0, 0, 2, 25, 0, "misc"],
                      "crates_2": ["crates", 1, 1, 0, 0, 2, 25, 0, "misc"],
                      "crates_3": ["crates", 1, 1, 0, 0, 2, 25, 0, "misc"],
                      "crates_4": ["crates", 1, 1, 0, 0, 2, 25, 0, "misc"],
                      "water_tower_1": ["water tower", 1, 1, 0, 0, 2, 12, 1, "misc"],
                      "water_tower_2": ["water tower", 1, 1, 0, 0, 2, 12, 1, "misc"],
                      "small_stone_1": ["small stone building", 1, 1, 1, 0, 2, 35, 1, "village"],
                      "small_stone_2": ["small stone building", 1, 1, 1, 0, 2, 35, 1, "village"],
                      "small_stone_3": ["small stone building", 1, 1, 1, 0, 2, 35, 1, "village"],
                      "small_stone_4": ["small stone building", 1, 1, 1, 0, 2, 35, 1, "village"],
                      "small_stone_5": ["small stone building", 1, 1, 1, 0, 2, 35, 1, "village"],
                      "small_stone_6": ["small stone building", 1, 1, 1, 0, 2, 35, 1, "village"],
                      "small_stone_7": ["small stone building", 1, 1, 1, 0, 2, 35, 1, "village"],
                      "small_stone_8": ["small stone building", 1, 1, 1, 0, 2, 35, 1, "village"],
                      "wooden_house_1": ["wooden house", 1, 1, 1, 0, 2, 25, 0, "village"],
                      "wooden_house_2": ["wooden house", 1, 1, 1, 0, 2, 25, 0, "village"],
                      "wooden_house_3": ["wooden house", 1, 1, 1, 0, 2, 25, 0, "village"],
                      "wooden_house_4": ["wooden house", 1, 1, 1, 0, 2, 25, 0, "village"],
                      "wooden_house_5": ["wooden house", 1, 1, 1, 0, 2, 25, 0, "village"],
                      "wooden_house_6": ["wooden house", 1, 1, 1, 0, 2, 35, 0, "village"],
                      "wooden_house_7": ["wooden house", 1, 1, 1, 0, 2, 35, 0, "village"],
                      "wooden_shack_1": ["wooden shack", 1, 1, 1, 0, 2, 25, 0, "village"],
                      "wooden_shack_2": ["wooden shack", 1, 1, 1, 0, 2, 25, 0, "village"],
                      "wooden_shack_3": ["wooden shack", 1, 1, 1, 0, 2, 25, 0, "village"],
                      "wooden_shack_4": ["wooden shack", 1, 1, 1, 0, 2, 25, 0, "village"],
                      "wooden_shack_5": ["wooden shack", 1, 1, 1, 0, 2, 25, 0, "village"],
                      "wooden_shack_6": ["wooden shack", 1, 1, 1, 0, 2, 15, 0, "village"],
                      "wooden_shack_7": ["wooden shack", 1, 1, 1, 0, 2, 15, 0, "village"],
                      "wooden_shack_8": ["wooden shack", 1, 1, 1, 0, 2, 15, 0, "village"],
                      "bunker_1": ["bunker", 1, 1, 1, 0, 2, 40, 1, "military"],
                      "bunker_2": ["bunker", 2, 2, 1, 0, 2, 50, 1, "military"],
                      "bunker_3": ["bunker", 2, 2, 1, 0, 2, 60, 1, "military"],
                      "bunker_4": ["bunker", 1, 1, 1, 0, 2, 40, 2, "military"],
                      "bunker_5": ["bunker", 2, 2, 1, 0, 2, 50, 2, "military"],
                      "bunker_6": ["bunker", 2, 2, 1, 0, 2, 60, 3, "military"],
                      "ruins_1": ["ruins", 1, 1, 0, 0, 2, 30, 2, "misc"],
                      "ruins_2": ["ruins", 1, 1, 0, 0, 2, 30, 2, "misc"],
                      "ruins_3": ["ruins", 1, 1, 0, 0, 2, 30, 2, "misc"],
                      "ruins_4": ["ruins", 1, 1, 0, 0, 2, 30, 2, "misc"],
                      "fighter_plane_1": ["aeroplane", 2, 2, 0, 0, 1, 30, 0, "misc"],
                      "fighter_plane_2": ["aeroplane", 2, 2, 0, 0, 1, 30, 0, "misc"],
                      "supply_truck_1": ["truck", 1, 1, 0, 0, 1, 30, 0, "misc"],
                      "supply_truck_2": ["truck", 1, 1, 0, 0, 1, 30, 1, "misc"]}

    titles = ["building_label",
              "x_size",
              "y_size",
              "can_enter",
              "supplies",
              "height",
              "hps",
              "armor",
              "building_type"]

    out_path = "D:/projects/vinland_1942/game_folder/saves/buildings.txt"
    new_dict = {}

    for dict_key in test_buildings:
        entries = test_buildings[dict_key]
        entry_dict = {}

        for t in range(len(titles)):
            title = titles[t]
            entry = entries[t]

            entry_dict[title] = entry

        entry_dict["destroyed"] = False
        entry_dict["damage"] = 0
        entry_dict["damage_stage"] = 0

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
               "smoke",
               "rockets",
               "wheels",
               "plane",
               "stance"]

    unique_actions = []

    for action in actions:
        if action not in unique_actions:
            unique_actions.append(action)

    out_path = "D:/projects/vinland_1942/game_folder/saves/unique_actions.txt"
    with open(out_path, "w") as outfile:
        json.dump({"unique_actions": unique_actions}, outfile)


def build_formations():
    infantry_formations = {0: [[0.0, 0.0]],
                           1: [[3.0, 0.0]],
                           2: [[2.0, 0.0], [4.0, 0.0]],
                           3: [[0.0, -1.0], [3.0, 1.0], [5.0, -1.0]],
                           4: [[2.0, 1.0], [4.0, 1.0], [2.0, -1.0], [4.0, -1.0]],
                           5: [[2.0, 1.0], [4.0, 1.0], [0.0, -1.0], [3.0, -1.0], [5.0, -1.0]],
                           6: [[0.0, 1.0], [3.0, 1.0], [5.0, 1.0], [0.0, -1.0], [3.0, -1.0], [5.0, -1.0]]}

    formations = {}

    for formation_key in infantry_formations:
        formation = infantry_formations[formation_key]

        positions = []

        for position in formation:
            x, y = position

            x = (x - 3.0) * 2.0
            y = y * 2.0

            positions.append([x, y])

        formations[formation_key] = positions

    out_path = "D:/projects/vinland_1942/game_folder/saves/infantry_formations.txt"
    with open(out_path, "w") as outfile:
        json.dump(formations, outfile)


# build_components()
# build_weapons()
# build_test_vehicles()
# build_infantry()
# build_actions()
# ai_labels()
# build_buildings()
# build_formations()

# write_unique_icons()
print("FINISHED")
