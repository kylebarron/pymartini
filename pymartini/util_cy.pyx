import numpy as np
cimport numpy as np


def rescale_positions(
    vertices,
    terrain,
    unsigned short tile_size,
    bounds=None,
    flip_y=False):
    """Rescale positions and add height as third dimension

    Note this flips the y dimension, since the use

    Args:
        - vertices: vertices output from Martini
        - terrain: array of elevations
        - tile_size: Original array size. Used to select the right values from
          the terrain array.
        - bounds: linearly rescale position values to this extent, expected to
          be [minx, miny, maxx, maxy]
        - flip_y: (bool) Flip y coordinates. Useful when original data source is
          a PNG, since the origin of a PNG is the top left.

    Returns:
        (np.array): Array with positions rescaled and including elevations
    """

    cdef unsigned short grid_size
    cdef unsigned int n_vertices
    cdef np.uint16_t[:] vertices_view = vertices
    cdef np.float32_t[:] terrain_view = terrain

    grid_size = tile_size + 1
    n_vertices = int(len(vertices) / 2)
    # vec3. x, y in pixels, z in meters
    positions = np.zeros(n_vertices * 3, dtype=np.float32)

    cdef np.float32_t[:] positions_view = positions

    cdef float minx, miny, maxx, maxy
    cdef float x_scale, y_scale

    minx, miny, maxx, maxy = bounds or [0, 0, tile_size, tile_size]
    x_scale = (maxx - minx) / tile_size
    y_scale = (maxy - miny) / tile_size

    if flip_y:
        y_scale *= -1

    cdef Py_ssize_t i
    cdef unsigned short x, y
    cdef unsigned int pixel_idx

    for i in range(n_vertices):
        x = vertices_view[i * 2]
        y = vertices_view[i * 2 + 1]
        pixel_idx = y * grid_size + x

        positions_view[i * 3 + 0] = x * x_scale + minx
        positions_view[i * 3 + 1] = y * y_scale + maxy
        positions_view[i * 3 + 2] = terrain_view[pixel_idx]

    return positions
