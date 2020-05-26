import numpy as np


class Martini:
    def __init__(self, grid_size=257):
        self.grid_size = grid_size

        tile_size = grid_size - 1
        if tile_size & (tile_size - 1):
            raise ValueError(
                f'Expected grid size to be 2^n+1, got {grid_size}.')

        self.num_triangles = tile_size * tile_size * 2 - 2
        self.num_parent_triangles = self.num_triangles - tile_size * tile_size

        self.indices = np.zeros(
            self.grid_size * self.grid_size, dtype=np.uint32)

        # coordinates for all possible triangles in an RTIN tile
        self.coords = np.zeros(self.num_triangles * 4, dtype=np.uint16)

        # get triangle coordinates from its index in an implicit binary tree
        for i in range(self.num_triangles):
            # id is a reserved name in Python
            _id = i + 2

            ax = ay = bx = by = cx = cy = 0
            if _id & 1:
                # bottom-left triangle
                bx = by = cx = tile_size
            else:
                # top-right triangle
                ax = ay = cy = tile_size

            while (_id >> 1) > 1:
                # Since Python doesn't have a >>= operator
                _id = _id >> 1

                mx = (ax + bx) >> 1
                my = (ay + by) >> 1

                if _id & 1:
                    # Left half
                    bx, by = ax, ay
                    ax, ay = cx, cy
                else:
                    # Right half
                    ax, ay = bx, by
                    bx, by = cx, cy

                cx, cy = mx, my

            k = i * 4
            self.coords[k + 0] = ax
            self.coords[k + 1] = ay
            self.coords[k + 2] = bx
            self.coords[k + 3] = by
