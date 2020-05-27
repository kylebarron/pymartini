import numpy as np


def mapbox_terrain_to_grid(png):
    grid_size = png.shape[0] + 1
    terrain = np.zeros((grid_size, grid_size), dtype=np.float32)

    # Get bands
    red = png[:, :, 0] * (256 * 256)
    green = png[:, :, 1] * (256)
    blue = png[:, :, 2]

    # Compute float height
    heights = (red + green + blue) / 10 - 10000

    # Copy to larger array to allow backfilling
    np.copyto(terrain[:512, :512], heights)

    # backfill right and bottom borders
    terrain[grid_size - 1, :] = terrain[grid_size - 2, :]
    terrain[:, grid_size - 1] = terrain[:, grid_size - 2]

    return terrain.flatten('C')
