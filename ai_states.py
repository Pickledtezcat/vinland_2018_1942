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
        self.chosen_action = None
        self.best_options = None

        self.moved = False
        self.fired = False

        self.ending = 60
        self.finished = False
        self.recycle = 0
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

    def change_stance(self):
        origin = self.agent.get_stat("position")
        prone_action = self.agent.get_action_key("TOGGLE_STANCE")
        if prone_action:
            action_trigger = self.agent.trigger_action(prone_action, origin)

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

    def set_movement(self, remaining_actions, position):
        movement_target = None

        selected = self.agent
        origin = selected.get_position()

        movement_cost = selected.get_movement_cost()
        if movement_cost:
            on_road_cost, off_road_cost = movement_cost

            self.environment.pathfinder.generate_paths(origin, on_road_cost, off_road_cost)
            self.environment.update_map()

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

                    potential_target = (armor_target > 1 and base_target > 1) or not direct_attack

                    if potential_target:
                        valid_action = self.agent.check_action_valid(action_id, tile_over)

                        if valid_action:
                            if valid_action[0] == "VALID_TARGET":
                                options.append([action_id, enemy_id, damage, base_target, armor_target, tile_over])

        options = sorted(options, key=operator.itemgetter(4, 3), reverse=True)
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
            self.recycle = 30
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
            action_trigger = self.agent.trigger_action(rotation_action, target_position)
        self.moved = True

    def process_attack(self):

        best_option = self.best_options[0]
        action_id, enemy_id, damage, base_target, armor_target, tile_over = best_option
        action_trigger = self.agent.trigger_action(action_id, tile_over)

    def process(self):

        if self.exit_check():
            return False

        infantry_types = ["INFANTRY", "ARTILLERY"]

        if self.agent.agent_type in infantry_types and not self.agent.has_effect("PRONE"):
            self.change_stance()
            return True

        if self.agent.agent_type == "VEHICLE" and not self.agent.has_effect("BUTTONED_UP"):
            self.toggle_buttoned_up()
            return True

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
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

    def process_movement(self):
        free_actions = self.agent.get_stat("free_actions")
        position = self.get_movement_target()
        movement_target = self.set_movement(free_actions, position)
        if not movement_target:
            return False

        movement_action = self.agent.get_action_key("MOVE")
        action_trigger = self.agent.trigger_action(movement_action, movement_target)
        self.moved = True

    def process(self):

        if self.exit_check():
            return False

        infantry_types = ["INFANTRY", "ARTILLERY"]

        if self.agent.agent_type in infantry_types and self.agent.has_effect("PRONE"):
            self.change_stance()
            return True

        if self.agent.agent_type == "VEHICLE" and not self.agent.has_effect("BUTTONED_UP"):
            self.toggle_buttoned_up()
            return True

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
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

    def process_movement(self):
        free_actions = self.agent.get_stat("free_actions")
        position = self.get_movement_target()

        movement_target = self.set_movement(free_actions, position)
        if not movement_target:
            return False

        movement_action = self.agent.get_action_key("MOVE")
        action_trigger = self.agent.trigger_action(movement_action, movement_target)
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

        infantry_types = ["INFANTRY", "ARTILLERY"]

        if self.agent.agent_type in infantry_types and not self.agent.has_effect("PRONE"):
            self.change_stance()
            return True

        if self.agent.agent_type == "VEHICLE" and not self.agent.has_effect("BUTTONED_UP"):
            self.toggle_buttoned_up()
            return True

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
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

        infantry_types = ["INFANTRY", "ARTILLERY"]

        if self.agent.agent_type in infantry_types and self.agent.has_effect("PRONE"):
            self.change_stance()
            return True

        if self.agent.agent_type == "VEHICLE" and not self.agent.has_effect("BUTTONED_UP"):
            self.toggle_buttoned_up()
            return True

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
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
            if target_distance > 3:
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

        infantry_types = ["INFANTRY", "ARTILLERY"]

        if self.agent.agent_type in infantry_types and self.agent.has_effect("PRONE"):
            self.change_stance()
            return True

        if self.agent.agent_type == "VEHICLE" and not self.agent.has_effect("BUTTONED_UP"):
            self.toggle_buttoned_up()
            return True

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
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

    def process(self):

        if self.exit_check():
            return False

        infantry_types = ["INFANTRY", "ARTILLERY"]

        if self.agent.agent_type in infantry_types and not self.agent.has_effect("PRONE"):
            self.change_stance()
            return True

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                self.best_options = self.get_target_options(False)
                if not self.best_options:
                    return False
                else:
                    self.process_attack()
                    return True
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
            if not self.agent.has_effect("PRONE"):
                self.change_stance()
                return True

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

        if self.agent.agent_type == "VEHICLE" and not self.agent.has_effect("BUTTONED_UP"):
            self.toggle_buttoned_up()
            return True

        if self.agent.has_effect("JAMMED"):
            return False

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
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

        infantry_types = ["INFANTRY", "ARTILLERY"]

        if self.agent.agent_type in infantry_types and not self.agent.has_effect("PRONE"):
            self.change_stance()
            return True

        if self.agent.agent_type == "VEHICLE" and not self.agent.has_effect("BUTTONED_UP"):
            self.toggle_buttoned_up()
            return True

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
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

    def get_support_actions(self):
        support_actions = []

        action_dict = self.agent.get_stat("action_dict")
        free_actions = self.agent.get_stat("free_actions")

        for action_key in action_dict:
            checking_action = action_dict[action_key]
            action_cost = checking_action["action_cost"]
            triggered = checking_action["triggered"]

            if action_cost <= free_actions and not triggered:
                ai_tactic = checking_action["ai_tactics"]

                if ai_tactic == "DEFENSIVE_SUPPORT":
                    support_actions.append(action_key)

        return support_actions

    def get_support_options(self):
        # TODO shift rapid fire and some other options to support?

        support_actions = self.get_support_actions()
        print(support_actions, "AVAILABLE")

        action_dict = self.agent.get_stat("action_dict")
        options = []

        for action_key in support_actions:
            support_action = action_dict[action_key]

            morale_boost = support_action["action_name"] == "RECOVER_MORALE"
            un_jam = support_action["action_name"] == "CHANGE_FREQUENCIES"
            order = support_action["action_name"] == "DIRECT_ORDER"

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
                            elif un_jam:
                                if target_agent.has_effect("RADIO_JAMMING"):
                                    if target_agent.has_effect("COMMAND_RADIO"):
                                        tactical_points = 3
                                    elif target_agent.has_effect("HAS_RADIO"):
                                        tactical_points = 1
                            elif order and target_agent.get_stat("free_actions") == 0:
                                if target_agent.agent_type == "VEHICLE":
                                    tactical_points = 1
                                else:
                                    tactical_points = 0
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

    def process_support(self):

        support_options = self.get_support_options()
        if not support_options:
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

        infantry_types = ["INFANTRY", "ARTILLERY"]

        if self.agent.agent_type in infantry_types and not self.agent.has_effect("PRONE"):
            self.change_stance()
            return True

        if self.agent.agent_type == "VEHICLE" and not self.agent.has_effect("BUTTONED_UP"):
            self.toggle_buttoned_up()
            return True

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
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





