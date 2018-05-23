import bge
import bgeutils
import mathutils
import random


class AiState(object):
    def __init__(self, environment, turn_manager, agent_id):
        self.environment = environment
        self.turn_manager = turn_manager
        self.agent_id = agent_id

        self.agent = self.environment.agents[self.agent_id]
        self.finished = False

    def update(self):
        if not self.process():
            self.finished = True

    def process(self):
        return False


class Hold(AiState):
    def __init__(self, environment, turn_manager, agent_id):
        super().__init__(environment, turn_manager, agent_id)

        self.best_target = self.get_best_target()
        self.targeted = False

    def get_attack_actions(self):

        free_actions = self.agent.get_stat("free_actions")

        def is_weapon(test_action):

            if test_action["action_type"] == "WEAPON":
                return True
            else:
                return False

        def requires_radio(test_action):

            if test_action["radio_points"] > 0:
                return True
            else:
                return False

        def triggered(test_action):
            if test_action["triggered"]:
                return True
            else:
                return False

        def free(test_action, free_action_amount):

            if test_action["action_cost"] <= free_action_amount:
                return True
            else:
                return False

        action_dict = self.agent.get_stat("action_dict")
        attack_actions = [action_key for action_key in action_dict if is_weapon(action_dict[action_key])]

        if not self.agent.has_effect("HAS_RADIO"):
            attack_actions = [action_key for action_key in attack_actions if not requires_radio(action_dict[action_key])]

        attack_actions = [action_key for action_key in attack_actions if not triggered(action_dict[action_key])]
        attack_actions = [action_key for action_key in attack_actions if free(action_dict[action_key], free_actions)]

        return attack_actions

    def get_best_target(self):
        position = self.agent.get_stat("position")
        closest = 10000.0
        target_agent = None

        for agent_key in self.environment.agents:
            other_agent = self.environment.agents[agent_key]
            if other_agent.get_stat("team") == 1:
                if not other_agent.has_effect("DYING") and not other_agent.has_effect("BAILED_OUT"):
                    other_position = other_agent.get_stat("position")
                    target_vector = mathutils.Vector(other_position) - mathutils.Vector(position)
                    distance = target_vector.length

                    if distance < closest:
                        closest = distance
                        target_agent = agent_key

        return target_agent

    def process(self):
        if self.agent.get_stat("free_actions") < 1:
            return False

        if self.agent.has_effect("DYING"):
            return False

        if self.best_target:
            target_agent = self.environment.agents[self.best_target]

            if self.agent.busy:
                return True
            else:
                if not self.targeted:
                    # TODO check for already facing
                    target_position = target_agent.get_stat("position")

                    if target_position:
                        self.agent.active_action = self.agent.get_action_key("FACE_TARGET")
                        action_trigger = self.agent.trigger_current_action(target_position)
                        self.targeted = True

                else:
                    attack_actions = self.get_attack_actions()
                    if attack_actions:
                        chosen_action = random.choice(attack_actions)
                        target_position = target_agent.get_stat("position")
                        self.agent.active_action = chosen_action
                        action_trigger = self.agent.trigger_current_action(target_position)

                        if not action_trigger:
                            return False

                    else:
                        return False

        return True
