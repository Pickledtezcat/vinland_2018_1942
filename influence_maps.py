import bge
import bgeutils


class InfluenceMap(object):
    def __init__(self, environment):
        self.environment = environment

    def get_base_map(self):

        max_x = self.environment.max_x
        max_y = self.environment.max_y

        base_map = {}

        for x in range(0, max_x):
            for y in range(0, max_y):
                base_map[(x, y)] = 0

        return base_map

    def generate_influence_map(self):
        pass

    def process_influence_map(self, new_map):
        search_array = [[-1, 0], [-1, 1], [1, 0], [1, 1], [0, -1], [1, -1], [0, 1], [-1, -1]]
        #search_array = [[-1, 0], [1, 0], [0, -1], [0, 1]]

        running = True

        while running:
            running = False
            process_map = {}

            for map_key in new_map:
                ox, oy = map_key
                current_value = new_map[map_key]
                n_max = 500

                for n in search_array:
                    neighbor_key = (ox + n[0], oy + n[1])

                    nx, ny = neighbor_key
                    if 0 <= nx < self.environment.max_x:
                        if 0 <= ny < self.environment.max_y:

                            n_value = new_map[neighbor_key]
                            if n_value < n_max:
                                n_max = n_value

                if current_value - n_max > 1 and current_value < 100:
                    running = True
                    process_map[map_key] = n_max + 1
                else:
                    process_map[map_key] = current_value

            new_map = process_map

        return new_map

