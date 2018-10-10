import bge
import bgeutils
import mathutils
import random
import particles
import operator


class AiState(object):
    def __init__(self, environment, turn_manager, agent_id):
        self.environment = environment
        self.turn_manager = turn_manager
        self.agent_id = agent_id

        self.agent = self.environment.agents[self.agent_id]
        self.objective = self.get_objective()

        self.best_target = None
        self.best_options = None

        self.moved = False
        self.fired = False

        self.ending = 60
        self.finished = False
        self.recycle = 5
        self.environment.update_map()

    def get_objective(self):
        objective = None

        agent_objective_id = self.agent.get_stat("objective_index")
        if agent_objective_id != 9:
            for effect_id in self.environment.effects:
                effect = self.environment.effects[effect_id]
                objective_index = effect.get_objective_id()
                if objective_index == self.agent.get_stat("objective_index"):
                    objective = effect

        return objective

    def update(self):
        if not self.process():
            if not self.agent.busy:
                self.agent.set_stat("free_actions", 0)
                self.finished = True

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

    def get_closest_target(self):

        position = self.agent.get_stat("position")
        closest = 10000.0
        target_agent = None

        for enemy_key in self.environment.agents:
            enemy = self.environment.agents[enemy_key]
            valid_target = enemy.check_valid_target(False)
            if valid_target:
                other_position = enemy.get_stat("position")
                target_vector = mathutils.Vector(other_position) - mathutils.Vector(position)
                distance = target_vector.length

                if distance < closest:
                    closest = distance
                    target_agent = enemy_key

        return target_agent, closest

    def get_ai_actions(self, ai_setting):
        ai_actions = []

        action_dict = self.agent.get_stat("action_dict")
        free_actions = self.agent.get_stat("free_actions")

        for action_key in action_dict:
            checking_action = action_dict[action_key]
            action_cost = checking_action["action_cost"]
            triggered = checking_action["triggered"]

            if action_cost <= free_actions and not triggered:
                ai_tactic = checking_action["ai_tactics"]

                if ai_tactic == ai_setting:
                    ai_actions.append(action_key)

        return ai_actions

    def button_up(self):

        if self.agent.agent_type == "VEHICLE":

            if self.agent.has_effect("RADIO_JAMMING"):
                self.change_frequencies()
                return True

            # if self.agent.has_effect("JAMMED"):
            #     self.clear_jam()
            #     return True

            if self.agent.has_effect("STAY_BUTTONED_UP"):
                if not self.agent.has_effect("BUTTONED_UP"):
                    self.toggle_buttoned_up()
                    return True

        return False

    def stand_up(self):
        infantry_types = ["INFANTRY", "ARTILLERY"]

        if self.agent.agent_type in infantry_types and self.agent.has_effect("PRONE"):
            self.change_stance()
            return True

        return False

    def go_prone(self):
        infantry_types = ["INFANTRY", "ARTILLERY"]

        if self.agent.has_effect("STAY_PRONE"):
            if self.agent.agent_type in infantry_types and not self.agent.has_effect("PRONE"):
                self.change_stance()
                return True

        return False

    def change_stance(self):
        origin = self.agent.get_stat("position")
        prone_action = self.agent.get_action_key("TOGGLE_STANCE")
        if prone_action:
            action_trigger = self.agent.trigger_action(prone_action, origin)

    def clear_jam(self):
        origin = self.agent.get_stat("position")
        clear_action = self.agent.get_action_key("JAMMED")
        if clear_action:
            action_trigger = self.agent.trigger_action(clear_action, origin)

    def change_frequencies(self):
        origin = self.agent.get_stat("position")
        change_action = self.agent.get_action_key("CHANGE_FREQUENCIES")
        if change_action:
            action_trigger = self.agent.trigger_action(change_action, origin)

    def toggle_buttoned_up(self):
        origin = self.agent.get_stat("position")
        buttoned_action = self.agent.get_action_key("TOGGLE_BUTTONED_UP")
        if buttoned_action:
            action_trigger = self.agent.trigger_action(buttoned_action, origin)

    def get_objective_distance(self):
        if self.objective:
            position = self.objective.position
            origin = self.agent.get_stat("position")

            target_vector = mathutils.Vector(position).to_3d() - mathutils.Vector(origin).to_3d()
            return target_vector.length

        return 10000.0

    def get_movement_target(self):
        pass

    def process_movement(self):
        free_actions = self.agent.get_stat("free_actions")
        position = self.get_movement_target()
        if not position:
            return False

        movement_target = self.set_movement(free_actions, position)
        if not movement_target:
            return False

        movement_action = self.agent.get_action_key("MOVE")
        action_trigger = self.agent.trigger_action(movement_action, movement_target)
        if not action_trigger:
            return False
        self.moved = True
        return True

    def set_movement(self, remaining_actions, position):
        movement_target = None

        selected = self.agent
        origin = selected.get_position()

        movement_cost = selected.get_movement_cost()
        if movement_cost:
            on_road_cost, off_road_cost = movement_cost

            self.environment.pathfinder.generate_paths(origin, on_road_cost, off_road_cost)
            x, y = position
            targets = []
            target = None

            for ox in range(-2, 2):
                for oy in range(-2, 2):
                    tx = x + ox
                    ty = y + oy

                    if 0 <= tx < self.environment.max_x:
                        if 0 <= ty < self.environment.max_y:
                            targets.append((x + ox, y + oy))

            random.shuffle(targets)
            targets.insert(0, position)

            distances = [[target, (mathutils.Vector(target) - mathutils.Vector(origin)).length] for target in targets]
            distances = sorted(distances, key=lambda distance: distance[1], reverse=True)
            targets = [target[0] for target in distances]

            path_found = False

            while not path_found and targets:
                target = targets.pop(0)
                self.environment.pathfinder.find_path(target)
                if self.environment.pathfinder.current_path:
                    path_found = True

            if path_found:
                path = self.environment.pathfinder.current_path

                for tile_key in path:
                    movement_cost = self.environment.pathfinder.get_movement_cost(tile_key)
                    if movement_cost <= remaining_actions:
                        movement_target = tile_key
                    else:
                        return movement_target

        return movement_target

    def get_attacks(self, direct_attack):

        if direct_attack:
            ai_string = "DIRECT_ATTACK"
        else:
            ai_string = "ARTILLERY"

        attacks = []

        action_dict = self.agent.get_stat("action_dict")
        free_actions = self.agent.get_stat("free_actions")

        for action_key in action_dict:
            checking_action = action_dict[action_key]
            if checking_action["action_type"] == "WEAPON":
                action_cost = checking_action["action_cost"]
                triggered = checking_action["triggered"]

                if action_cost <= free_actions and not triggered:
                    ai_tactic = checking_action["ai_tactics"]

                    if ai_tactic == ai_string:
                        attacks.append(action_key)

        return attacks

    def get_target_options(self, direct_attack):

        self.environment.update_map()
        attacks = self.get_attacks(direct_attack)
        options = []

        if self.agent.has_effect("JAMMED"):
            return []

        for enemy_id in self.environment.agents:
            enemy = self.environment.agents[enemy_id]
            agent_id = self.agent.get_stat("agent_id")

            valid_target = enemy.check_valid_target(direct_attack)
            if valid_target:
                target_id = enemy.get_stat("agent_id")
                tile_over = enemy.get_stat("position")

                for action_id in attacks:
                    target_data = self.turn_manager.get_target_data(agent_id, target_id, action_id, tile_over)
                    contents = target_data["contents"]

                    base_target = 2
                    armor_target = 2
                    damage = 0

                    if target_data["target_type"] == "EXPLOSION":
                        damage, shock, base_target, penetration, explosion_reduction = contents
                        if enemy.agent_type == "INFANTRY":
                            armor_target = 7
                        else:
                            if not enemy.has_effect("BUTTONED_UP"):
                                armor_target = 3

                    elif target_data["target_type"] == "DIRECT_ATTACK":
                        damage, shock, flanked, covered, base_target, armor_target = contents

                    potential_target = (armor_target > -2 and base_target > 1) or not direct_attack

                    if potential_target:
                        valid_action = self.agent.check_action_valid(action_id, tile_over)

                        if valid_action:
                            if valid_action[0] == "VALID_TARGET":
                                options.append([action_id, enemy_id, damage, base_target, armor_target, tile_over])

        options = sorted(options, key=operator.itemgetter(4, 3, 2), reverse=True)
        best_options = options[:3]

        return best_options

    def process_attack(self):
        best_option = self.best_options[0]
        action_id, enemy_id, damage, base_target, armor_target, tile_over = best_option
        action_trigger = self.agent.trigger_action(action_id, tile_over)

    def process(self):
        return False

    def cycled(self):

        if self.recycle == 0:
            self.recycle = 15
            return True

        else:
            self.recycle -= 1
            return False

    def terminate(self):
        self.environment.update_map()


class Hold(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

    def get_movement_target(self):
        pass

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

    def process_movement(self):
        closest_enemy = self.get_closest_target()[0]
        if closest_enemy:
            target_agent = self.environment.agents[closest_enemy]
            target_position = target_agent.get_stat("position")
            rotation_action = self.agent.get_action_key("FACE_TARGET")
            if not rotation_action:
                rotation_action = self.agent.get_action_key("REDEPLOY")

            action_trigger = self.agent.trigger_action(rotation_action, target_position)
        self.moved = True

    def process_attack(self):

        best_option = self.best_options[0]
        action_id, enemy_id, damage, base_target, armor_target, tile_over = best_option
        action_trigger = self.agent.trigger_action(action_id, tile_over)

    def process(self):

        if self.exit_check():
            return False

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                if self.go_prone():
                    return True

                if self.button_up():
                    return True

                self.best_options = self.get_target_options(True)
                if not self.best_options:
                    if not self.moved:
                        self.process_movement()
                        return True
                    else:
                        return False
                else:
                    self.process_attack()
                    return True
            else:
                return True


class GoTo(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

        if self.agent.check_immobile():
            self.agent.set_behavior("HOLD")
            return True

        if not self.objective:
            self.agent.set_behavior("HOLD")
            return True

        objective_distance = self.get_objective_distance()
        if objective_distance <= 3.0:
            # TODO set exit behavior

            self.agent.set_behavior("HOLD")
            return True

    def get_movement_target(self):
        return self.objective.position

    def process(self):

        if self.exit_check():
            return False

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                if self.stand_up():
                    return True

                if self.button_up():
                    return True

                if not self.moved:
                    if not self.process_movement():
                        return False
                    return True
                else:
                    return False
            else:
                return True


class Attack(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

    def get_movement_target(self):
        return self.objective.position

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

        if self.agent.check_immobile():
            self.agent.set_behavior("HOLD")
            return True

        if not self.objective:
            self.agent.set_behavior("HOLD")
            return True

        objective_distance = self.get_objective_distance()
        if objective_distance <= 3.0:
            # TODO set exit behavior

            self.agent.set_behavior("HOLD")
            return True

    def process_attack(self):
        best_option = self.best_options[0]
        action_id, enemy_id, damage, base_target, armor_target, tile_over = best_option
        action_trigger = self.agent.trigger_action(action_id, tile_over)

    def process(self):

        if self.exit_check():
            return False

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                if self.stand_up():
                    return True

                if self.button_up():
                    return True

                self.best_options = self.get_target_options(True)
                if not self.best_options:
                    if not self.moved:
                        if not self.process_movement():
                            return False
                        return True
                    else:
                        return False
                else:
                    self.process_attack()
                    return True
            else:
                return True


class Advance(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

    def get_movement_target(self):
        return self.objective.position

    def process_movement(self):
        position = self.get_movement_target()

        movement_target = self.set_movement(1, position)
        if not movement_target:
            return False

        movement_action = self.agent.get_action_key("MOVE")
        action_trigger = self.agent.trigger_action(movement_action, movement_target)
        if not action_trigger:
            return False
        self.moved = True
        return True

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

        if self.agent.check_immobile():
            self.agent.set_behavior("HOLD")
            return True

        if not self.objective:
            self.agent.set_behavior("HOLD")
            return True

        objective_distance = self.get_objective_distance()
        if objective_distance <= 3.0:
            # TODO set exit behavior

            self.agent.set_behavior("HOLD")
            return True

    def process_attack(self):
        best_option = self.best_options[0]
        action_id, enemy_id, damage, base_target, armor_target, tile_over = best_option
        action_trigger = self.agent.trigger_action(action_id, tile_over)

    def process(self):

        if self.exit_check():
            return False

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                if self.stand_up():
                    return True

                if self.button_up():
                    return True

                if not self.moved:
                    if not self.process_movement():
                        return False
                    return True
                else:
                    self.best_options = self.get_target_options(True)
                    if not self.best_options:
                        self.moved = False
                        return True
                    else:
                        self.process_attack()
                        return True


class Aggressive(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

        if self.agent.check_immobile():
            self.agent.set_behavior("HOLD")
            return True

    def process_attack(self):
        best_option = self.best_options[0]
        action_id, enemy_id, damage, base_target, armor_target, tile_over = best_option
        action_trigger = self.agent.trigger_action(action_id, tile_over)

    def process_movement(self):
        closest_target = self.get_closest_target()

        if closest_target[0]:
            target_agent = self.environment.agents[closest_target[0]]
            target_position = target_agent.get_stat("position")

            target_distance = closest_target[1]
            if 3 < target_distance < 8:
                movement_target = self.set_movement(1, target_position)
                if not movement_target:
                    return False

                movement_action = self.agent.get_action_key("MOVE")
                action_trigger = self.agent.trigger_action(movement_action, movement_target)
                if not action_trigger:
                    return False

        self.moved = True
        return True

    def process(self):

        if self.exit_check():
            return False

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                if self.stand_up():
                    return True

                if self.button_up():
                    return True

                if not self.moved:
                    if not self.process_movement():
                        return False
                    return True
                else:
                    self.best_options = self.get_target_options(True)
                    if not self.best_options:
                        return False
                    else:
                        self.process_attack()
                        return True


class Artillery(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

        self.artillery_options = None

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

        if self.agent.check_immobile():
            self.agent.set_behavior("HOLD")
            return True

    def process_attack(self):
        best_option = self.best_options[0]
        action_id, enemy_id, damage, base_target, armor_target, tile_over = best_option
        action_trigger = self.agent.trigger_action(action_id, tile_over)

    def process_artillery(self):
        best_option = self.artillery_options[0]
        action_id, enemy_id, damage, base_target, armor_target, tile_over = best_option
        action_trigger = self.agent.trigger_action(action_id, tile_over)

    def process(self):
        if self.exit_check():
            return False

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                if self.go_prone():
                    return True

                self.best_options = self.get_target_options(True)
                if self.best_options:
                    self.process_attack()
                    return True
                else:
                    self.artillery_options = self.get_target_options(False)
                    if self.artillery_options:
                        self.process_artillery()
                        return True
                    return False
            else:
                return True


class Ambush(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

    def set_ambush(self):

        ambush_action = self.agent.get_action_key("AMBUSH")
        if ambush_action:
            position = self.agent.get_stat("position")
            action_trigger = self.agent.trigger_action(ambush_action, position)

    def process(self):

        if self.exit_check():
            return False

        infantry_types = ["INFANTRY", "ARTILLERY"]

        if self.agent.agent_type in infantry_types:
            if self.go_prone():
                return False

            if not self.agent.has_effect("AMBUSH"):
                self.set_ambush()
                self.agent.set_behavior("HOLD")
                return False

        else:
            self.agent.set_behavior("HOLD")
            return False


class AntiAir(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

        aa_action = self.agent.get_action_key("ANTI_AIRCRAFT_FIRE")
        if not aa_action:
            self.agent.set_behavior("HOLD")
            return True

    def aa_fire(self):
        # TODO find a way to handle aa fire

        has_target = False

        for effect_key in self.environment.effects:
            effect = self.environment.effects[effect_key]
            if effect.anti_air_target and effect.team != self.agent.get_stat("team"):
                has_target = True

        if has_target:
            aa_action = self.agent.get_action_key("ANTI_AIRCRAFT_FIRE")
            if aa_action:
                position = self.agent.get_stat("position")
                action_trigger = self.agent.trigger_action(aa_action, position)

    def process(self):
        if self.exit_check():
            return False

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                if self.button_up():
                    return True

                if self.agent.has_effect("JAMMED"):
                    return False

                self.best_options = self.get_target_options(True)
                if not self.best_options:
                    self.aa_fire()
                    return False
                else:
                    self.process_attack()
                    return True
            else:
                return True


class Defend(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

    def get_preparation_action(self):
        action_choices = ["OVERWATCH", "STEADY_AIM", "SPECIAL_AMMO", "RAPID_FIRE"]
        valid_choices = []
        position = self.agent.get_stat("position")

        for action_name in action_choices:
            action_string = self.agent.get_action_key(action_name)
            if action_string:
                validity = self.agent.check_action_valid(action_string, position)
                if validity:
                    if validity[0] == "VALID_TARGET":
                        valid_choices.append(action_string)

        if valid_choices:
            if len(valid_choices) > 1:
                best_action = random.choice(valid_choices)
            else:
                best_action = valid_choices[0]

            action_trigger = self.agent.trigger_action(best_action, position)

    def process_attack(self):

        best_option = self.best_options[0]
        action_id, enemy_id, damage, base_target, armor_target, tile_over = best_option
        action_trigger = self.agent.trigger_action(action_id, tile_over)

    def process(self):

        if self.exit_check():
            return False

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                if self.go_prone():
                    return True

                if self.button_up():
                    return True

                self.best_options = self.get_target_options(True)
                if not self.best_options:
                    self.get_preparation_action()
                    return False
                else:
                    self.process_attack()
                    return True
            else:
                return True


class Support(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

    def get_support_options(self):
        # TODO shift rapid fire and some other options to support?
        support_actions = self.get_ai_actions("DEFENSIVE_SUPPORT")

        action_dict = self.agent.get_stat("action_dict")
        options = []

        for action_key in support_actions:
            support_action = action_dict[action_key]

            morale_boost = support_action["action_name"] == "RECOVER_MORALE"
            order = support_action["action_name"] == "DIRECT_ORDER"
            quick_march = support_action["action_name"] == "QUICK_MARCH"

            for agent_key in self.environment.agents:
                target_agent = self.environment.agents[agent_key]
                valid_agent = target_agent.check_valid_support_target()

                if valid_agent:
                    target_position = target_agent.get_stat("position")
                    valid_target = self.agent.check_action_valid(action_key, target_position)
                    tactical_points = -1

                    if valid_target:
                        if valid_target[0] == "VALID_TARGET":
                            if morale_boost:
                                if target_agent.get_stat("shock") > 20:
                                    tactical_points = 1
                                elif target_agent.get_stat("shock") > 10:
                                    tactical_points = 2
                            if order and target_agent.get_stat("free_actions") == 0:
                                if target_agent.agent_type == "VEHICLE":
                                    tactical_points = 1
                                else:
                                    tactical_points = 0
                            if quick_march:
                                moving_behavior = ["ATTACK", "ADVANCE", "AGGRESSIVE", "SCOUT", "SUPPLY", "FLANKING"]
                                target_behavior = target_agent.get_behavior()

                                if target_behavior in moving_behavior:
                                    if target_agent.agent_type == "VEHICLE":
                                        tactical_points = 1
                                    else:
                                        tactical_points = 0

                    if tactical_points > -1:
                        visibility = self.environment.player_visibility.lit(*target_position)
                        if visibility > 0:
                            tactical_points += 2

                        options.append([action_key, target_position, tactical_points])

        if options:
            options = sorted(options, key=lambda option: option[2], reverse=True)
            best_options = options[:3]

            return best_options

        return None

    def try_spotting(self):
        spotting_key = self.agent.get_action_key("SPOTTING")
        if spotting_key:
            position = self.agent.get_stat("position")
            action_trigger = self.agent.trigger_action(spotting_key, position)

    def process_support(self):
        support_options = self.get_support_options()

        if not support_options:
            self.try_spotting()
            return False

        else:
            if len(support_options) > 1:
                support_option = random.choice(support_options)
            else:
                support_option = support_options[0]

            action_key, target_position, tactical_points = support_option
            action_trigger = self.agent.trigger_action(action_key, target_position)
            if not action_trigger:
                return False

        return True

    def process(self):
        if self.exit_check():
            return False

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                if self.button_up():
                    return True

                self.best_options = self.get_target_options(True)
                if not self.best_options:
                    if not self.process_support():
                        return False
                    return True
                else:
                    self.process_attack()
                    return True
            else:
                return True


class Scout(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

        self.nav_point, self.nav_distance = self.get_nav_point()

    def get_nav_point(self):

        if not self.objective:
            return None, 1000

        effects = self.environment.effects
        agent_objective_id = self.agent.get_stat("objective_index")
        nav_points = []

        for effect_key in effects:
            effect = effects[effect_key]
            if effect.effect_type == "MAP_POINT":
                if effect.get_stat("point_type") == "NAV_POINT":
                    if effect.get_stat("index") == agent_objective_id:
                        nav_points.append(effect)

        if not nav_points:
            return None, 1000

        origin = mathutils.Vector(self.agent.get_stat("position"))
        agent_id = self.agent_id
        target_nav_point = None
        target_distance = 1000

        visited_all = True

        for nav_point in nav_points:
            visiting = nav_point.get_stat("visiting")
            visited = nav_point.get_stat("visited")

            if agent_id in visiting:
                if agent_id not in visited:
                    visited_all = False
                    target_nav_point = nav_point
                    target_point = mathutils.Vector(nav_point.position)
                    target_vector = target_point - origin
                    target_distance = target_vector.length
            else:
                visited_all = False

        if visited_all:
            for nav_point in nav_points:
                nav_point.clear_visited(agent_id)

        if target_nav_point:
            return target_nav_point, target_distance
        else:
            closest = 1000
            best = None

            for nav_point in nav_points:
                visited = nav_point.get_stat("visited")

                if agent_id not in visited:
                    target_point = mathutils.Vector(nav_point.position)
                    target_vector = target_point - origin
                    target_distance = target_vector.length
                    if target_distance < closest:
                        closest = target_distance
                        best = nav_point
            if best:
                best.add_visiting(self.agent_id)
                return best, closest

        return None, 1000

    def process_movement(self):

        if self.nav_distance < 3.0:
            self.nav_point.add_visited(self.agent_id)
            self.nav_point, self.nav_distance = self.get_nav_point()

        free_actions = self.agent.get_stat("free_actions")
        position = self.nav_point.position

        movement_target = self.set_movement(free_actions, position)
        if not movement_target:
            return False

        movement_action = self.agent.get_action_key("MOVE")
        action_trigger = self.agent.trigger_action(movement_action, movement_target)
        if not action_trigger:
            return False
        self.moved = True
        return True

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

        if self.agent.check_immobile():
            self.agent.set_behavior("HOLD")
            return True

        if not self.objective:
            self.agent.set_behavior("HOLD")
            return True

        if not self.nav_point:
            self.agent.set_behavior("HOLD")
            return True

    def process_attack(self):
        best_option = self.best_options[0]
        action_id, enemy_id, damage, base_target, armor_target, tile_over = best_option
        action_trigger = self.agent.trigger_action(action_id, tile_over)

    def process(self):

        if self.exit_check():
            return False

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                if self.stand_up():
                    return True

                if self.button_up():
                    return True

                self.best_options = self.get_target_options(True)
                if not self.best_options:
                    if not self.moved:
                        if not self.process_movement():
                            return False
                        return True
                    else:
                        return False
                else:
                    self.process_attack()
                    return True
            else:
                return True


class Supply(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

        self.ally = self.get_closest_ally()

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

        if self.agent.check_immobile():
            self.agent.set_behavior("HOLD")
            return True

    def get_closest_ally(self):

        selected = self.agent
        origin = selected.get_position()
        movement_cost = selected.get_movement_cost()
        if movement_cost:
            on_road_cost, off_road_cost = movement_cost
            self.environment.pathfinder.generate_paths(origin, on_road_cost, off_road_cost)
        else:
            return None

        allies = []
        owned_actions = self.get_ai_actions("SUPPLY")

        for agent_key in self.environment.agents:
            agent = self.environment.agents[agent_key]
            same_team = agent.get_stat("team") == self.agent.get_stat("team")
            shared_objective = agent.get_stat("objective_index") == self.agent.get_stat("objective_index")
            no_objective = not self.objective

            if same_team:
                if shared_objective or no_objective:
                    needs_supply = agent.check_needs_supply()
                    if needs_supply[0] != "NONE" and needs_supply[0] in owned_actions:
                        allies.append(needs_supply)

        if allies:
            allies = sorted(allies, key=operator.itemgetter(1, 2))
            return allies[0]

        return None

    def get_movement_target(self):
        ally = self.ally[3]
        return ally.get_stat("position")

    def process_supply(self):

        target_tile = None

        ally_id = self.ally[3].get_stat("agent_id")
        adjacent = self.environment.pathfinder.adjacent_tiles

        for tile_key in adjacent:
            tile = self.environment.get_tile(tile_key)
            if tile:
                if tile["occupied"] == ally_id:
                    target_tile = tile_key

        if target_tile:
            target_condition = self.ally[0]
            if target_condition == "CREW":
                target_position = self.agent.get_stat("position")
            else:
                target_position = target_tile

            target_action = self.agent.get_action_key(target_condition)
            trigger_action = self.agent.trigger_action(target_action, target_position)
            return True

        return False

    def process(self):
        if self.exit_check():
            return False

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                if self.stand_up():
                    return True

                if self.button_up():
                    return True

                self.ally = self.get_closest_ally()
                if self.ally:
                    if not self.process_supply():
                        if not self.process_movement():
                            return False
                        return True
                else:
                    return False
            else:
                return True


class Jammer(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

    def get_jamming_options(self):
        support_actions = self.get_ai_actions("OFFENSIVE_SUPPORT")

        action_dict = self.agent.get_stat("action_dict")
        options = []

        for action_key in support_actions:
            support_action = action_dict[action_key]

            marking = support_action["action_name"] == "MARK_TARGET"
            recognition = support_action["action_name"] == "TARGET_RECOGNITION"
            confusion = support_action["action_name"] == "RADIO_CONFUSION"
            jamming = support_action["action_name"] == "RADIO_JAMMING"

            for agent_key in self.environment.agents:
                target_agent = self.environment.agents[agent_key]
                valid_agent = target_agent.check_valid_jammer_target()

                if valid_agent:

                    target_position = target_agent.get_stat("position")
                    valid_target = self.agent.check_action_valid(action_key, target_position)

                    if valid_target:
                        radio_jammed = target_agent.has_effect("RADIO_JAMMING")
                        air_force = target_agent.has_effect("AIR_FORCE_RADIO")
                        command = target_agent.has_effect("COMMAND_RADIO")
                        tactical = target_agent.has_effect("TACTICAL_RADIO")
                        standard = target_agent.has_effect("HAS_RADIO")
                        vehicle = target_agent.agent_type == "VEHICLE"

                        tactical_bonus = 0
                        if air_force:
                            tactical_bonus = 5
                        elif command:
                            tactical_bonus = 4
                        elif tactical:
                            tactical_bonus = 3
                        elif standard:
                            tactical_bonus = 2
                        elif vehicle:
                            tactical_bonus = 1

                        tactical_points = -1
                        if valid_target[0] == "VALID_TARGET":
                            if jamming and not radio_jammed:
                                tactical_points = tactical_bonus + 2
                            if recognition:
                                if target_agent.get_stat("armor")[0] > 1:
                                    tactical_points = 0
                                if target_agent.get_stat("armor")[0] > 3:
                                    tactical_points = 1
                                if target_agent.get_stat("armor")[0] > 5:
                                    tactical_points = 2
                                if target_agent.get_stat("armor")[0] > 7:
                                    tactical_points = 3
                            if confusion:
                                tactical_points = tactical_bonus + 1
                            if marking:
                                tactical_points = tactical_bonus

                        if tactical_points > -1:
                            options.append([action_key, target_position, tactical_points])

        if options:
            options = sorted(options, key=lambda option: option[2], reverse=True)
            return options

        return None

    def process_jamming(self):
        support_options = self.get_jamming_options()

        if not support_options:
            return False
        else:
            support_option = support_options[0]

            action_key, target_position, tactical_points = support_option
            action_trigger = self.agent.trigger_action(action_key, target_position)
            if not action_trigger:
                return False

        return True

    def try_spotting(self):
        spotting_key = self.agent.get_action_key("SPOTTING")
        if spotting_key:
            position = self.agent.get_stat("position")
            action_trigger = self.agent.trigger_action(spotting_key, position)
            if action_trigger:
                return True

        return False

    def process(self):
        if self.exit_check():
            return False

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                if self.button_up():
                    return True

                if not self.process_jamming():
                    if not self.try_spotting():
                        self.best_options = self.get_target_options(True)
                        if not self.best_options:
                            return False
                        else:
                            self.process_attack()
                            return True
            else:
                return True


class AirSupport(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

        if self.agent.check_immobile():
            self.agent.set_behavior("HOLD")
            return True

    def get_air_support_options(self):
        support_actions = self.get_ai_actions("AIR_SUPPORT")

        action_dict = self.agent.get_stat("action_dict")
        options = []

        for action_key in support_actions:
            support_action = action_dict[action_key]

            spotter = support_action["action_name"] == "SPOTTER_PLANE"
            # TODO add other air support actions
            air_strikes = ["AIR_STRIKE"]
            air_support = support_action["action_name"] in air_strikes
            paradrop = support_action["action_name"] == "PARADROP"

            if air_support or paradrop:
                if air_support:
                    tactical_points = 6
                else:
                    tactical_points = 4

                for effect_key in self.environment.effects:
                    effect = self.environment.effects[effect_key]
                    target_position = effect.position
                    if effect.effect_type == "REVEAL" and effect.team == 1:
                        options.append([action_key, target_position, tactical_points])

            for agent_key in self.environment.agents:
                target_agent = self.environment.agents[agent_key]
                valid_target = target_agent.check_valid_target(False)
                if valid_target:

                    target_position = target_agent.get_stat("position")
                    command_units = ["AIR_FORCE_RADIO", "COMMAND_RADIO", "TACTICAL_RADIO"]
                    is_command_unit = False
                    for command_string in command_units:
                        if target_agent.has_effect(command_string):
                            is_command_unit = True

                    tactical_points = -1

                    if air_support:
                        if is_command_unit:
                            tactical_points = 3
                        else:
                            tactical_points = 1

                    if paradrop:
                        if is_command_unit:
                            tactical_points = 2
                        else:
                            tactical_points = 0

                    if tactical_points > -1:
                        options.append([action_key, target_position, tactical_points])

        if options:
            options = sorted(options, key=lambda option: option[2], reverse=True)
            return options

        else:
            for action_key in support_actions:
                support_action = action_dict[action_key]
                spotter = support_action["action_name"] == "SPOTTER_PLANE"
                if spotter:
                    unseen = self.get_unseen()
                    if unseen:
                        return [[action_key, unseen, 0]]

        return None

    def get_unseen(self):
        padding = 10
        radius = 4
        choices = []

        for x in range(padding, self.environment.max_x - padding):
            for y in range(padding, self.environment.max_y - padding):

                visible = self.environment.enemy_visibility.lit(x, y)
                if not visible:
                    revealed = False

                    for vx in range(-radius, radius):
                        for vy in range(-radius, radius):
                            cx = x + vx
                            cy = y + vy
                            check_visible = self.environment.enemy_visibility.lit(cx, cy)
                            if check_visible:
                                revealed = True

                    if not revealed:
                        choices.append((x, y))

        if choices:
            if len(choices) > 1:
                return random.choice(choices)
            else:
                return choices[0]

    def process_air_support(self):
        support_options = self.get_air_support_options()

        if not support_options:
            return False
        else:
            support_option = support_options[0]

            action_key, target_position, tactical_points = support_option
            action_trigger = self.agent.trigger_action(action_key, target_position)
            if not action_trigger:
                return False

        return True

    def process(self):
        if self.exit_check():
            return False

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                if self.button_up():
                    return True

                self.best_options = self.get_target_options(True)
                if not self.best_options:
                    if not self.process_air_support():
                        return False
                    return True
                else:
                    self.process_attack()
                    return True

            else:
                return True


class ClearMines(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

        if self.agent.check_immobile():
            self.agent.set_behavior("HOLD")
            return True

    def get_movement_target(self):
        origin = self.agent.get_stat("position")

        best = None
        closest = 1000

        for effect_key in self.environment.effects:
            effect = self.environment.effects[effect_key]
            if effect.effect_type == "MINES":
                enemy_mines = effect.team != self.agent.get_stat("team")
                if enemy_mines:
                    position = effect.position
                    visibility = self.environment.enemy_visibility.lit(*position)
                    if visibility > 0:
                        distance = bgeutils.get_distance(origin, position)
                        if distance < closest:
                            best = position
                            closest = distance

        if best:
            return best

        return None

    def process_movement(self):
        position = self.get_movement_target()
        if not position:
            return False

        max_movement = self.agent.get_stat("free_actions")
        if max_movement < 1:
            return False

        movement_target = self.set_movement(max_movement, position)
        if not movement_target:
            return False

        movement_action = self.agent.get_action_key("MOVE")
        action_trigger = self.agent.trigger_action(movement_action, movement_target)
        if not action_trigger:
            return False
        self.moved = True
        return True

    def process_mine_removal(self):
        mines = self.agent.get_mines()
        if mines:
            action_key = self.agent.get_action_key("REMOVE_MINES")
            if action_key:
                action_trigger = self.agent.trigger_action(action_key, self.agent.get_stat("position"))
                if action_trigger:
                    return True

        return False

    def process(self):
        if self.exit_check():
            return False

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                if self.button_up():
                    return True

                if self.stand_up():
                    return True

                self.best_options = self.get_target_options(True)
                if not self.best_options:
                    if not self.process_mine_removal():
                        if not self.process_movement():
                            return False
                    return True
                else:
                    self.process_attack()
                    return True

            else:
                return True


class Retreating(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

        if self.agent.check_immobile():
            self.agent.set_behavior("HOLD")
            return True

        position = self.agent.get_stat("position")
        if self.environment.player_visibility.lit(*position) == 0:
            return True

    def check_valid_tile(self, target):
        tile = self.environment.get_tile(target)
        if tile:
            if self.environment.player_visibility.lit(*target) == 0:
                barred_types = ["occupied", "heights", "water", "rocks", "wall", "trees", "mines"]
                barred = False
                for terrain_type in barred_types:
                    if tile[terrain_type]:
                        barred = True

                if not barred:
                    return True

        return False

    def get_retreat_target(self):
        start_point = self.agent.get_stat("position")
        x, y = start_point

        radius = 8
        options = []

        for rx in range(-radius, radius):
            for ry in range(-radius, radius):
                nx = x + rx
                ny = y + ry

                if 0 <= nx < self.environment.max_x:
                    if 0 <= ny < self.environment.max_y:
                        if self.environment.player_visibility.lit(nx, ny) == 0:
                            target = (nx, ny)
                            distance = bgeutils.get_distance(start_point, target)
                            options.append([distance, target])

        options = sorted(options, key=lambda option: option[0])
        if options:
            best_target = options[0][1]

            return best_target

        return start_point

    def get_movement_target(self):
        target = self.get_retreat_target()
        return target

    def process(self):

        if self.exit_check():
            return False

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                if self.stand_up():
                    return True

                if self.button_up():
                    return True

                if not self.moved:
                    if not self.process_movement():
                        return False
                    return True
                else:
                    return False
            else:
                return True


class Flanking(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

    def exit_check(self):

        if self.agent.get_stat("free_actions") < 1:
            return True

        if self.agent.has_effect("DYING"):
            return True

        if self.agent.has_effect("BAILED_OUT"):
            return True

        if self.agent.check_immobile():
            self.agent.set_behavior("HOLD")
            return True

    def get_movement_target(self):
        origin = self.agent.get_stat("position")

        best = None
        closest = 1000

        for effect_key in self.environment.effects:
            effect = self.environment.effects[effect_key]
            if effect.effect_type == "REVEAL":
                enemy_reveal = effect.team != self.agent.get_stat("team")
                if enemy_reveal:
                    position = effect.position
                    visibility = self.environment.enemy_visibility.lit(*position)
                    if visibility > 0:
                        distance = bgeutils.get_distance(origin, position)
                        if distance < closest:
                            best = position
                            closest = distance

        if best:
            return best

        return None

    def process_movement(self):
        position = self.get_movement_target()
        if not position:
            return False

        max_movement = self.agent.get_stat("free_actions")
        if max_movement < 1:
            return False

        movement_target = self.set_movement(max_movement, position)
        if not movement_target:
            return False

        movement_action = self.agent.get_action_key("MOVE")
        action_trigger = self.agent.trigger_action(movement_action, movement_target)
        if not action_trigger:
            return False
        self.moved = True
        return True

    def process(self):
        if self.exit_check():
            return False

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                if self.button_up():
                    return True

                if self.stand_up():
                    return True

                self.best_options = self.get_target_options(True)
                if not self.best_options:
                    if not self.process_movement():
                        return False
                    return True
                else:
                    self.process_attack()
                    return True
            else:
                return True

