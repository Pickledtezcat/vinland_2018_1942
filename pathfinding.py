import bge
import mathutils
import heapq
import bgeutils


class NavNode(object):

    def __init__(self, position, off_road, impassable, infantry_only):
        self.position = position
        self.g = 0.0
        self.parent = None
        self.neighbors = []
        self.infantry_neighbors = []
        self.off_road = off_road
        self.impassable = impassable
        self.infantry_only = infantry_only
        self.occupied = False

    def clean_node(self, occupied):
        self.g = 0.0
        self.parent = None
        self.occupied = occupied
        self.neighbors = []
        self.infantry_neighbors = []

    def check_valid_target(self, infantry):
        if self.impassable:
            return False
        if self.occupied:
            return False
        if self.infantry_only and not infantry:
            return False
        if len(self.neighbors) == 0:
            return False

        return True


class Pathfinder(object):
    def __init__(self, environment):
        self.environment = environment
        self.graph = self.rebuild_map()
        self.update_map()
        self.flooded = False

        self.current_path = []
        self.start = None
        self.infantry = False
        self.on_road_cost = 1.0
        self.off_road_cost = 1.0

    def rebuild_map(self):
        level_map = self.environment.level_map
        graph = {}

        for map_key in level_map:
            position = bgeutils.get_loc(map_key)

            tile = level_map[map_key]
            impassable_types = ["water", "heights", "wall"]
            infantry_only_types = ["trees", "rocks"]

            off_road = True

            impassable = False
            infantry_only = False

            for terrain in impassable_types:
                if tile[terrain]:
                    impassable = True

            for infantry_terrain in infantry_only_types:
                if tile[infantry_terrain]:
                    infantry_only = True
                    off_road = True

            if tile["softness"] == 0:
                off_road = True

            if tile["softness"] == 4:
                infantry_only = True

            if tile["road"] or tile["bridge"]:
                off_road = False
                impassable = False
                infantry_only = False

            graph_key = tuple(position)
            graph[graph_key] = NavNode(graph_key, off_road, impassable, infantry_only)

        return graph

    def get_neighbors(self):
        for map_key in self.graph:

            node = self.graph[map_key]
            if not node.impassable:
                neighbors = []
                infantry_neighbors = []

                x, y = map_key
                search_array = [[-1, 0], [-1, 1], [1, 0], [1, 1], [0, -1], [1, -1], [0, 1], [-1, -1]]

                for n in search_array:
                    nx, ny = [x + n[0], y + n[1]]
                    if 0 <= nx < self.environment.max_x:
                        if 0 <= ny < self.environment.max_y:
                            neighbor_key = tuple([nx, ny])
                            neighbor_node = self.graph[neighbor_key]

                            if not neighbor_node.impassable:
                                if not neighbor_node.occupied:
                                    cost = 1.0
                                    if bgeutils.diagonal(n):
                                        cost = 1.4
                                    if not neighbor_node.infantry_only:
                                        neighbors.append([neighbor_key, cost])

                                    infantry_neighbors.append([neighbor_key, cost])

                self.graph[map_key].neighbors = neighbors
                self.graph[map_key].infantry_neighbors = infantry_neighbors

    def update_map(self):

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

    def generate_paths(self, start, on_road, off_road, infantry):

        self.start = tuple(start)
        self.on_road_cost = on_road
        self.off_road_cost = off_road
        self.infantry = infantry
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
            if self.infantry:
                neighbors = current_node.infantry_neighbors
            else:
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

                if neighbor_key in self.graph:

                    g_score = current_node.g + neighbor_cost

                    if neighbor_key in closed_set and g_score >= self.graph[neighbor_key].g:
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
        else:
            path = []

        if path:
            path.reverse()
            path.append(target)

        self.current_path = path


