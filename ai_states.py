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

        self.best_target = None
        self.targeted = False
        self.chosen_action = None

        self.agent = self.environment.agents[self.agent_id]
        self.objective = self.get_objective()

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

    def get_closest_target(self):

        position = self.agent.get_stat("position")
        closest = 10000.0
        target_agent = None

        for enemy_key in self.environment.agents:
            enemy = self.environment.agents[enemy_key]
            valid_target = enemy.check_valid_target(True)
            if valid_target:
                other_position = enemy.get_stat("position")
                target_vector = mathutils.Vector(other_position) - mathutils.Vector(position)
                distance = target_vector.length

                if distance < closest:
                    closest = distance
                    target_agent = enemy_key

        return target_agent

    def get_movement_target(self, remaining_actions):
        # TODO set movement target near objective in unoccupied tile
        position = None
        movement_target = None

        if self.objective:
            position = self.objective.position

        if position:
            selected = self.agent
            origin = selected.get_position()

            movement_cost = selected.get_movement_cost()
            if movement_cost:
                on_road_cost, off_road_cost = movement_cost

                self.environment.pathfinder.generate_paths(origin, on_road_cost, off_road_cost)
                self.environment.update_map()

            self.environment.pathfinder.find_path(position)

        if self.environment.pathfinder.current_path:

            path = self.environment.pathfinder.current_path

            for tile_key in path:
                movement_cost = self.environment.pathfinder.get_movement_cost(tile_key)
                if movement_cost <= remaining_actions:
                    movement_target = tile_key
                else:
                    return movement_target

        return movement_target

    def get_target_options(self):

        self.environment.update_map()

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

                    if ai_tactic == "DIRECT_ATTACK":
                        attacks.append(action_key)

        options = []

        for enemy_id in self.environment.agents:
            enemy = self.environment.agents[enemy_id]
            agent_id = self.agent.get_stat("agent_id")

            valid_target = enemy.check_valid_target(True)
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

                    if armor_target > 1 and base_target > 1:
                        valid_action = self.agent.check_action_valid(action_id, tile_over)

                        if valid_action:
                            if valid_action[0] == "VALID_TARGET":
                                options.append([action_id, enemy_id, damage, base_target, armor_target, tile_over])

        options = sorted(options, key=operator.itemgetter(4, 3), reverse=True)
        best_options = options[:3]

        return best_options

    def process(self):
        return False

    def cycled(self):

        if self.recycle == 0:
            self.recycle = 30
            return True

        else:
            self.recycle -= 1
            return False


class Hold(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

        self.best_options = self.get_target_options()
        self.triggered = False

    def process(self):

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:

                if self.agent.get_stat("free_actions") < 1:
                    return False

                if self.agent.has_effect("DYING"):
                    return False

                if self.agent.has_effect("JAMMED"):
                    return False

                if len(self.best_options) < 1:

                    if not self.triggered:
                        closest_enemy = self.get_closest_target()
                        if closest_enemy:
                            target_agent = self.environment.agents[closest_enemy]
                            target_position = target_agent.get_stat("position")
                            rotation_action = self.agent.get_action_key("FACE_TARGET")
                            action_trigger = self.agent.trigger_action(rotation_action, target_position)

                        self.triggered = True
                        return True

                    else:
                        return False

                else:
                    best_option = self.best_options[0]
                    action_id, enemy_id, damage, base_target, armor_target, tile_over = best_option
                    action_trigger = self.agent.trigger_action(action_id, tile_over)
                    self.best_options = self.get_target_options()
                    return True

            else:
                return True


class GoTo(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

        self.triggered = False

    def process(self):

        if not self.cycled():
            return True
        else:
            if not self.agent.busy:
                if not self.triggered:
                    free_actions = self.agent.get_stat("free_actions")
                    print(free_actions, "FREE ACTIONS")
                    movement_target = self.get_movement_target(free_actions)
                    print(movement_target)
                    if not movement_target:
                        return False

                    movement_action = self.agent.get_action_key("MOVE")
                    action_trigger = self.agent.trigger_action(movement_action, movement_target)
                    print(action_trigger, "TRIGGERED")
                    self.triggered = True
                    return True
                else:
                    return False

            else:
                return True
