import numpy as np


def mapbox_terrain_to_grid(png):
    tile_size = png.shape[0]
    grid_size = tile_size + 1
    terrain = np.zeros(grid_size * grid_size, dtype=np.float32)

    # decode terrain values
    for y in range(tile_size):
        for x in range(tile_size):
            r = png[y, x, 0]
            g = png[y, x, 1]
            b = png[y, x, 2]
            terrain[y * tile_size +
                    x] = (r * 256 * 256 + g * 256.0 + b) / 10.0 - 10000.0

    # backfill right and bottom borders
    for x in range(grid_size - 1):
        terrain[grid_size * (grid_size - 1) + x] = terrain[grid_size *
                                                           (grid_size - 2) + x]

    for y in range(grid_size):
        terrain[grid_size * y + grid_size - 1] = terrain[grid_size * y +
                                                         grid_size - 2]

    return terrain
