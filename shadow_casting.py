
class ShadowCasting(object):
    mult = [
        [1, 0, 0, -1, -1, 0, 0, 1],
        [0, 1, -1, 0, 0, -1, 1, 0],
        [0, 1, 1, 0, 0, -1, -1, 0],
        [1, 0, 0, 1, -1, 0, 0, -1]
    ]

    def __init__(self, environment):
        self.environment = environment

        self.width = self.environment.max_x
        self.height = self.environment.max_y
        self.light = []
        for i in range(self.height):
            self.light.append([0] * self.width)
        self.flag = 0
        self.update()

    def blocked(self, x, y):

        tile = self.environment.pathfinder.graph.get((x, y))
        if tile:
            if not tile.blocks_vision:
                return False

        return True

    def lit(self, x, y):
        return self.light[y][x] == self.flag

    def was_lit(self, x, y):
        return self.light[y][x] > 0

    def set_lit(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.light[y][x] = self.flag

    def _cast_light(self, cx, cy, row, start, end, radius, xx, xy, yx, yy, sid):

        """Recursive lightcasting function"""

        if start < end:
            return
        radius_squared = radius * radius
        for j in range(row, radius + 1):
            dx, dy = -j - 1, -j
            blocked = False
            while dx <= 0:
                dx += 1
                # Translate the dx, dy coordinates into map coordinates:
                ix, iy = cx + dx * xx + dy * xy, cy + dx * yx + dy * yy
                # l_slope and r_slope store the slopes of the left and right
                # extremities of the square we're considering:
                l_slope, r_slope = (dx - 0.5) / (dy + 0.5), (dx + 0.5) / (dy - 0.5)
                if start < r_slope:
                    continue
                elif end > l_slope:
                    break
                else:
                    # Our light beam is touching this square; light it:
                    if dx * dx + dy * dy < radius_squared:
                        self.set_lit(ix, iy)
                    if blocked:
                        # we're scanning a row of blocked squares:
                        if self.blocked(ix, iy):
                            new_start = r_slope
                            continue
                        else:
                            blocked = False
                            start = new_start
                    else:
                        if self.blocked(ix, iy) and j < radius:
                            # This is a blocking square, start a child scan:
                            blocked = True
                            self._cast_light(cx, cy, j + 1, start, l_slope,
                                             radius, xx, xy, yx, yy, sid + 1)
                            new_start = r_slope
            # Row is scanned; do next row unless last square was blocked:
            if blocked:
                break

    def do_fov(self, x, y, radius):
        """Calculate lit squares from the given location and radius"""
        for octant in range(8):
            self._cast_light(x, y, 1, 1.0, 0.0, radius,
                             self.mult[0][octant], self.mult[1][octant],
                             self.mult[2][octant], self.mult[3][octant], 0)

    def update(self):

        self.flag += 1

        for agent_key in self.environment.agents:
            agent = self.environment.agents[agent_key]
            if agent.stats["team"] == 1:
                x, y = agent.stats["position"]
                self.set_lit(x, y)
                self.do_fov(x, y, 12)



