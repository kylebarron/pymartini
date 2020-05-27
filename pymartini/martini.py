import numpy as np

from ._martini_cy import martini as _martini
from ._martini_cy import get_mesh as _get_mesh
from ._martini_cy import tile_update, countElements, processTriangle


class Martini:
    def __init__(self, grid_size=257):
        resp = _martini(grid_size)
        self.grid_size, self.num_triangles, self.num_parent_triangles, self.indices, self.coords = resp

    def create_tile(self, terrain):
        return Tile(terrain, self)


class Tile:
    def __init__(self, terrain, martini):
        size = martini.grid_size

        if len(terrain) != (size * size):
            raise ValueError(
                f'Expected terrain data of length {size * size} ({size} x {size}), got {len(terrain)}.'
            )

        self.terrain = terrain
        self.martini = martini
        self.errors = np.zeros(len(terrain), dtype=np.float32)
        self.update()

    def update(self):
        self.errors = tile_update(
            num_triangles=self.martini.num_triangles,
            num_parent_triangles=self.martini.num_parent_triangles,
            coords=self.martini.coords,
            size=self.martini.grid_size,
            terrain=self.terrain,
            errors=self.errors)

    def get_mesh(self, max_error=0):
        return _get_mesh(
          errors=self.errors,
          indices=self.martini.indices,
          size=self.martini.grid_size,
          max_error=max_error
        )
