import bge
import mathutils
import heapq
import bgeutils


class NavNode(object):

    def __init__(self, position, off_road, impassable, infantry_only):
        self.position = position
        self.g = 0.0
        self.f = 9000.0
        self.h = 9000.0
        self.parent = None
        self.neighbors = []
        self.infantry_neighbors = []
        self.off_road = off_road
        self.impassable = impassable
        self.infantry_only = infantry_only
        self.occupied = False

    def clean_node(self, occupied):
        self.g = 0.0
        self.f = 9000.0
        self.h = 9000.0
        self.parent = None
        self.occupied = occupied
        self.neighbors = []
        self.infantry_neighbors = []


class Pathfinder(object):
    def __init__(self, environment):
        self.environment = environment
        self.graph = self.rebuild_map()
        self.update_map()

        self.current_path = []
        self.start = None
        self.end = None
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

            off_road = False

            impassable = False
            infantry_only = False

            for terrain in impassable_types:
                if tile[terrain]:
                    impassable = True

            for infantry_terrain in infantry_only_types:
                if tile[infantry_terrain]:
                    infantry_only = True
                    off_road = True

            if tile["softness"] > 2:
                off_road = True

            if tile["softness"] > 3:
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

        for map_key in self.graph:
            tile = self.environment.get_tile(map_key)
            if tile:
                if tile["occupied"]:
                    occupied = True
                else:
                    occupied = False

                self.graph[map_key].clean_node(occupied)

        self.get_neighbors()

    def generate_path(self, start, end, on_road, off_road, infantry):

        self.end = tuple(end)
        self.start = tuple(start)
        self.on_road_cost = on_road
        self.off_road_cost = off_road
        self.infantry = infantry
        self.current_path = self.a_star()

    def a_star(self):

        current_key = self.start
        goal = mathutils.Vector(self.end)

        open_set = set()
        open_heap = []
        closed_set = set()

        path = []
        found = 0

        def path_gen(starting_key):

            current = self.graph[starting_key]
            new_path = []

            while current.parent:
                current = self.graph[current.parent]

                new_path.append(current.position)

            return new_path

        open_set.add(current_key)
        open_heap.append((0, current_key))

        while found == 0 and open_set:

            current_key = heapq.heappop(open_heap)[1]

            if current_key == self.end:
                path = path_gen(current_key)
                found = 1

            open_set.remove(current_key)
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
                if target.off_road:
                    neighbor_cost *= self.off_road_cost
                else:
                    neighbor_cost *= self.on_road_cost

                if neighbor_key in self.graph:

                    g_score = current_node.g + neighbor_cost
                    relation = (goal - mathutils.Vector(neighbor_key)).length

                    if neighbor_key in closed_set and g_score >= self.graph[neighbor_key].g:
                        continue

                    if neighbor_key not in open_set or g_score < self.graph[neighbor_key].g:
                        self.graph[neighbor_key].parent = current_key
                        self.graph[neighbor_key].g = g_score

                        h_score = relation
                        f_score = g_score + h_score
                        self.graph[neighbor_key].f = f_score

                        if self.graph[neighbor_key].h > h_score:
                            self.graph[neighbor_key].h = h_score

                        if neighbor_key not in open_set:
                            open_set.add(neighbor_key)
                            heapq.heappush(open_heap, (self.graph[neighbor_key].f, neighbor_key))

        if path:
            path.reverse()
            path.append(self.end)
            path.pop(0)

        return path

