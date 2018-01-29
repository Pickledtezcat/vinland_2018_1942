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
        self.neighbors = {}
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


class Pathfinder(object):

    def __init__(self, environment):
        self.environment = environment
        self.graph = self.rebuild_map()
        self.update_map()

        self.start = None
        self.end = None
        self.infantry = False
        self.on_road_cost = 1.0
        self.off_road_cost = 1.0

    def rebuild_map(self):
        level_map = self.environment.level_map
        graph = {}

        for map_key in level_map:

            tile = level_map[map_key]
            impassable_types = ["rocks", "water", "heights", "wall"]
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

            if tile["firmness"] > 2:
                off_road = True

            if tile["road"] or tile["bridge"]:
                off_road = False
                impassable = False
                infantry_only = False

            graph[map_key] = NavNode(bgeutils.get_loc(map_key), off_road, impassable, infantry_only)

        return graph

    def get_neighbors(self):
        for map_key in self.graph:
            node = self.graph[map_key]
            neighbors = []

            x, y = node.position

            search_array = [[-1, 0], [-1, 1], [0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1]]
            for n in search_array:
                nx, ny = [x + n[0], y + n[1]]
                if 0 <= nx < self.environment.max_x:
                    if 0 <= ny < self.environment.max_y:
                        neighbor_key = bgeutils.get_key([nx, ny])
                        neighbor_node = self.graph[neighbor_key]

                        if not neighbor_node.impassable:
                            if not neighbor_node.occupied:
                                neighbors.append(neighbor_key)

            self.graph[map_key].neighbors = neighbors

    def update_map(self):

        for map_key in self.graph:
            tile = self.environment.get_tile(bgeutils.get_loc(map_key))
            if tile:
                if tile["occupied"]:
                    occupied = True
                else:
                    occupied = False

                self.graph[map_key].clean_node(occupied)

        self.get_neighbors()

    def heuristic(self, node):

        D = 1.0
        D2 = 1.4

        node_x, node_y = node
        goal_x, goal_y = self.end

        dx = abs(node_x - goal_x)
        dy = abs(node_y - goal_y)
        return D * (dx + dy) + (D2 - 2 * D) * min(dx, dy)

    def generate_path(self, start, end, on_road, off_road, infantry):

        self.end = end
        self.start = start
        self.on_road_cost = on_road
        self.off_road_cost = off_road
        self.infantry = infantry




    def a_star(self):

        current_key = self.start
        goal = mathutils.Vector(self.end)

        open_set = set()
        open_heap = []
        closed_set = set()

        path = []
        found = 0

        def path_gen(current_key, path):

            current = self.graph[current_key]
            path = []

            while current.parent != None:
                current = self.graph[current.parent]

                path.append(current.location)

            return path

        open_set.add(current_key)
        open_heap.append((0, current_key))

        while found == 0 and open_set:

            current_key = heapq.heappop(open_heap)[1]

            if current_key == self.end:
                path = path_gen(current_key, path)
                found = 1

            open_set.remove(current_key)
            closed_set.add(current_key)

            current_node = self.graph[current_key]

            for neighbor_key in current_node.neighbors:

                if neighbor_key in self.graph:

                    g_score = current_node.g + current_node.neighbors[neighbor_key]
                    # relation = (goal - mathutils.Vector(neighbor_key)).length
                    relation = self.heuristic(neighbor_key)

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

        return path



class PathfinderX(object):

    def __init__(self, tiles, owner, move_type, size, start, end, border):

        self.owner = owner
        self.tiles = tiles
        self.ignore = [owner, owner.manager.player]
        self.move_type = move_type
        self.size = size
        self.start = start
        self.end = end
        self.border = border
        self.graph = self.build_graph(tiles)

        if self.start in self.graph and self.end in self.graph:
            self.route = self.a_star()
            if not self.route:

                graph_list = [self.graph[key] for key in self.graph]
                nearest = sorted(graph_list, key=lambda tile: tile.h)
                if nearest:
                    new_goal = nearest[0].location
                    self.end = new_goal
                    if new_goal != self.start:
                        self.graph = self.build_graph(tiles)
                        self.route = self.a_star()
                    else:
                        self.route = None

        else:
            self.route = None

        if self.route:
            self.route.pop(0)

        if self.owner.manager.debug:
            for tile_key in self.graph:
                tile = self.graph[tile_key]
                if tile.f < 1000:
                    color = [1.0, 0.0, 0.0, 1.0]
                else:
                    color = [0.0, 1.0, 0.0, 1.0]

                marker = self.owner.manager.scene.addObject("marker", self.owner.manager.own, 120)
                marker.worldPosition = [tile_key[0], tile_key[1], 0.1]
                marker.color = color
                if self.route:
                    if tile_key in self.route:
                        marker.color = [1.0, 0.0, 0.0, 1.0]

    def build_graph(self, tiles):

        graph = {}

        error = self.border

        x_min = min(self.start[0], self.end[0])
        x_max = max(self.start[0], self.end[0])
        y_min = min(self.start[1], self.end[1])
        y_max = max(self.start[1], self.end[1])

        for x in range(x_min - error, x_max + error):
            for y in range(y_min - error, y_max + error):
                tile = tiles.get((x, y))
                if tile:
                    open = True
                    if tile['type'] > self.move_type:
                        open = False

                    if tile["occupied"]:
                        if tile["occupied"] not in self.ignore:
                            open = False

                    if open:
                        if not self.check_blocked_tile((x, y)):
                            graph[(x, y)] = NavNode((x, y), tile['type'])

        directions = [[-1, 0], [-1, 1], [1, 0], [1, 1], [0, -1], [1, -1], [0, 1], [-1, -1]]

        for node_key in graph:
            for d in directions:
                if abs(d[0]) - abs(d[1]) == 0:
                    cost = 1.4
                else:
                    cost = 1.0

                neighbor_key = (node_key[0] + d[0], node_key[1] + d[1])

                if graph.get(neighbor_key):
                    graph[node_key].neighbors[neighbor_key] = cost

        return graph

    def update(self):

        pass

    def check_blocked_tile(self, origin_tile):

        ox, oy = origin_tile

        for cx in range(self.size):
            for cy in range(self.size):
                check_key = (ox + cx, oy + cy)

                check_tile = self.tiles.get(check_key)

                if not check_tile:
                    return True

                else:
                    if check_tile['type'] > self.move_type:
                        return True

                    if check_tile['occupied']:
                        if check_tile['occupied'] not in self.ignore:
                            return True

        return False

    def heuristic(self, node):

        D = 1.0
        D2 = 1.4

        node_x, node_y = node
        goal_x, goal_y = self.end

        dx = abs(node_x - goal_x)
        dy = abs(node_y - goal_y)
        return D * (dx + dy) + (D2 - 2 * D) * min(dx, dy)

    def a_star(self):

        current_key = self.start
        goal = mathutils.Vector(self.end)

        open_set = set()
        open_heap = []
        closed_set = set()

        path = []
        found = 0

        def path_gen(current_key, path):

            current = self.graph[current_key]
            path = []

            while current.parent != None:
                current = self.graph[current.parent]

                path.append(current.location)

            return path

        open_set.add(current_key)
        open_heap.append((0, current_key))

        while found == 0 and open_set:

            current_key = heapq.heappop(open_heap)[1]

            if current_key == self.end:
                path = path_gen(current_key, path)
                found = 1

            open_set.remove(current_key)
            closed_set.add(current_key)

            current_node = self.graph[current_key]

            for neighbor_key in current_node.neighbors:

                if neighbor_key in self.graph:

                    g_score = current_node.g + current_node.neighbors[neighbor_key]
                    # relation = (goal - mathutils.Vector(neighbor_key)).length
                    relation = self.heuristic(neighbor_key)

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

        return path

