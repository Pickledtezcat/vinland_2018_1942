import bge
import mathutils
import heapq
import bgeutils


class NavNode(object):

    def __init__(self, position, off_road, impassable, blocking, cover):
        self.position = position
        self.g = 0.0
        self.parent = None
        self.neighbors = []
        self.off_road = off_road
        self.impassable = impassable
        self.blocks_vision = blocking
        self.cover = cover
        self.cover_directions = None
        self.occupied = False

    def clean_node(self, occupied):
        self.g = 0.0
        self.parent = None
        self.occupied = occupied
        self.neighbors = []

    def check_valid_target(self):
        if self.impassable:
            return False
        if self.occupied:
            return False
        if len(self.neighbors) == 0:
            return False

        return True

    def get_movement_cost(self):
        if not self.parent:
            return 0

        movement_cost = int(self.g)

        if movement_cost * 10 != int(self.g * 10.0):
            movement_cost += 1

        return movement_cost


class Pathfinder(object):
    def __init__(self, environment):
        self.environment = environment
        self.graph = self.rebuild_graph()
        self.update_graph()
        self.flooded = False

        self.current_path = []
        self.movement_cost = 0
        self.start = None
        self.on_road_cost = 1.0
        self.off_road_cost = 1.0

        self.cover_maps = {}
        #self.generate_cover_maps()

    def generate_cover_maps(self):
        directions = ["NORTH", "EAST", "SOUTH", "WEST"]
        for direction in directions:
            cover_map = self.generate_cover(direction)
            self.cover_maps[direction] = cover_map

    def rebuild_graph(self):
        level_map = self.environment.level_map
        graph = {}

        for map_key in level_map:
            position = bgeutils.get_loc(map_key)

            tile = level_map[map_key]
            impassable_types = ["water", "heights", "wall", "rocks", "trees"]
            blocking_types = ["trees", "heights"]
            cover_types = ["bushes", "wall", "rocks"]
            rough_types = ["bushes"]

            off_road = True
            blocking = False
            impassable = False
            cover = False

            for terrain in cover_types:
                if tile[terrain]:
                    cover = True

            for terrain in impassable_types:
                if tile[terrain]:
                    impassable = True

            for terrain in blocking_types:
                if tile[terrain]:
                    blocking = True

            if tile["softness"] < 2:
                off_road = False

            if tile["softness"] == 4:
                impassable = True

            if tile["road"] or tile["bridge"]:
                off_road = False
                impassable = False

            for terrain in rough_types:
                if tile[terrain]:
                    off_road = True

            graph_key = tuple(position)
            graph[graph_key] = NavNode(graph_key, off_road, impassable, blocking, cover)

        for map_key in graph:
            search_array = [[0, 1, "NORTH"], [1, 0, "EAST"], [0, -1, "SOUTH"], [-1, 0, "WEST"]]

            cover_directions = []
            x, y = map_key

            current_tile = graph[map_key]
            if current_tile.cover:
                cover_directions = ["NORTH", "EAST", "SOUTH", "WEST"]
            else:
                for n in search_array:
                    neighbor_key = (x + n[0], y + n[1])

                    nx, ny = neighbor_key
                    if 0 <= nx < self.environment.max_x:
                        if 0 <= ny < self.environment.max_y:
                            neighbor_tile = graph[neighbor_key]
                            if neighbor_tile.cover:
                                cover_directions.append(n[2])

            graph[map_key].cover_directions = cover_directions

        return graph

    def get_neighbors(self):
        for map_key in self.graph:

            node = self.graph[map_key]
            if not node.impassable:
                neighbors = []

                x, y = map_key
                search_array = [[-1, 0], [-1, 1], [1, 0], [1, 1], [0, -1], [1, -1], [0, 1], [-1, -1]]

                for n in search_array:
                    neighbor_key = (x + n[0], y + n[1])
                    nx, ny = neighbor_key
                    if 0 <= nx < self.environment.max_x:
                        if 0 <= ny < self.environment.max_y:
                            blocked = False

                            if bgeutils.diagonal(n):
                                cost = 1.4
                                adjacent_neighbors = [(x + n[0], y), (x, y + n[1])]
                                for adjacent in adjacent_neighbors:
                                    adjacent_tile = self.graph[adjacent]
                                    if adjacent_tile.impassable or adjacent_tile.occupied:
                                        blocked = True
                            else:
                                cost = 1.0

                            neighbor_node = self.graph[neighbor_key]

                            if not blocked:
                                if not neighbor_node.impassable:
                                    if not neighbor_node.occupied:
                                        neighbors.append([neighbor_key, cost])

                self.graph[map_key].neighbors = neighbors

    def update_graph(self):

        self.flooded = False

        for map_key in self.graph:
            tile = self.environment.get_tile(map_key)
            if tile:
                if tile["occupied"]:
                    occupied = True
                else:
                    occupied = False

                self.graph[map_key].clean_node(occupied)

        self.get_neighbors()

    def generate_paths(self, start, on_road, off_road):

        self.start = tuple(start)
        self.on_road_cost = on_road
        self.off_road_cost = off_road
        self.flood_fill()

    def flood_fill(self):
        current_key = self.start

        open_set = set()
        closed_set = set()

        open_set.add(current_key)

        while open_set:

            current_key = open_set.pop()
            closed_set.add(current_key)

            current_node = self.graph[current_key]
            neighbors = current_node.neighbors

            for n in neighbors:
                neighbor_key = n[0]
                neighbor_cost = n[1]

                target = self.graph[neighbor_key]
                off_road = target.off_road

                if off_road:
                    neighbor_cost *= self.off_road_cost
                else:
                    neighbor_cost *= self.on_road_cost

                g_score = current_node.g + neighbor_cost

                if g_score >= self.graph[neighbor_key].g and neighbor_key in closed_set:
                    continue

                if neighbor_key not in open_set or g_score < self.graph[neighbor_key].g:
                    self.graph[neighbor_key].parent = current_key
                    self.graph[neighbor_key].g = g_score

                    if neighbor_key not in open_set:
                        open_set.add(neighbor_key)

        self.flooded = True

    def find_path(self, target):

        def path_gen(starting_key):

            current = self.graph[starting_key]
            new_path = []

            while current.parent:
                current = self.graph[current.parent]

                new_path.append(current.position)

            return new_path

        target = tuple(target)
        if target in self.graph:
            path = path_gen(target)
            self.movement_cost = self.graph[target].get_movement_cost()
        else:
            self.movement_cost = 0
            path = []

        if path:
            path.reverse()
            path.append(target)

        self.current_path = path

    def process_influence_map(self, new_map):

        # search_array = [[-1, 0], [-1, 1], [1, 0], [1, 1], [0, -1], [1, -1], [0, 1], [-1, -1]]
        search_array = [[-1, 0], [1, 0], [0, -1], [0, 1]]

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

    def generate_cover(self, direction):
        new_map = {}

        for map_key in self.graph:
            value = 50

            tile = self.graph[map_key]
            if tile.impassable:
                value = 100

            elif direction in tile.cover_directions:
                value = 0

            new_map[map_key] = value

        new_map = self.process_influence_map(new_map)
        return new_map

    def generate_influence_map(self):

        new_map = {}
        for map_key in self.graph:
            tile = self.graph[map_key]
            if tile.impassable or tile.occupied:
                value = 100
            else:
                if tile.off_road:
                    value = 75
                else:
                    value = 50

            new_map[map_key] = value

        visible_enemies = []

        for agent_key in self.environment.agents:
            agent = self.environment.agents[agent_key]
            if agent.get_stat("team") == 1:
                x, y = agent.get_stat("position")

                # if self.environment.enemy_visibility.lit(x, y):
                #    visible_enemies.append((x, y))

                visible_enemies.append((x, y))

        for enemy_position in visible_enemies:
            new_map[enemy_position] = 0

        new_map = self.process_influence_map(new_map)
        return new_map
