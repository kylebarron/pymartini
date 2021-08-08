from typing import Tuple

import numpy as np


def decode_ele(png: np.ndarray, encoding: str, backfill: bool = True) -> np.ndarray:
    """Decode array to elevations

    Arguments:
        - png (np.ndarray). Ndarray of elevations encoded in three channels,
          representing red, green, and blue. Must be of shape (tile_size,
          tile_size, >=3), where `tile_size` is usually 256 or 512
        - encoding: (str): Either 'mapbox' or 'terrarium', the two main RGB
          encodings for elevation values.
        - backfill: (bool): Whether to create an array of size (tile_size +
          1)^2, backfilling the bottom and right edges. This is used because
          Martini needs a grid of size 2^n + 1

    Returns:
        (np.array) Array of shape (tile_size^2) with decoded elevation values
    """
    allowed_encodings = ['mapbox', 'terrarium']
    if encoding not in allowed_encodings:
        raise ValueError(f'encoding must be one of {allowed_encodings}')

    if png.shape[0] <= 4:
        png = png.T

    # Get bands
    if encoding == 'mapbox':
        red = png[:, :, 0] * (256 * 256)
        green = png[:, :, 1] * (256)
        blue = png[:, :, 2]

        # Compute float height
        terrain = (red + green + blue) / 10 - 10000
    elif encoding == 'terrarium':
        red = png[:, :, 0] * (256)
        green = png[:, :, 1]
        blue = png[:, :, 2] / 256

        # Compute float height
        terrain = (red + green + blue) - 32768

    if backfill:
        terrain = compute_backfill(terrain)

    return terrain


def compute_backfill(arr: np.ndarray) -> np.ndarray:
    grid_size = arr.shape[0] + 1

    terrain = np.zeros((grid_size, grid_size), dtype=np.float32)

    # Copy to larger array to allow backfilling
    np.copyto(terrain[: grid_size - 1, : grid_size - 1], arr)

    # backfill right and bottom borders
    terrain[grid_size - 1, :] = terrain[grid_size - 2, :]
    terrain[:, grid_size - 1] = terrain[:, grid_size - 2]
    return terrain


def rescale_positions(
    vertices: np.ndarray,
    terrain: np.ndarray,
    bounds: Tuple[float, float, float, float] = None,
    flip_y: bool = False,
) -> np.ndarray:
    """Rescale positions and add height as third dimension

    Args:
        - vertices: vertices output from Martini
        - terrain: 2d array of elevations as output by `decode_ele`
        - bounds: linearly rescale position values to this extent, expected to
          be [minx, miny, maxx, maxy]. If not provided, no rescaling is done
        - flip_y: (bool) Flip y coordinates. Useful when original data source is
          a PNG, since the origin of a PNG is the top left.

    Returns:
        (np.ndarray): ndarray of shape (-1, 3) with positions rescaled and
        including elevations. Each row represents a single 3D point.
    """
    vertices = vertices.reshape(-1, 2)

    # vec3. x, y in pixels/bounds' coordinates, z in meters
    positions = np.zeros((max(vertices.shape), 3), dtype=np.float32)

    if not bounds:
        positions[:, :2] = vertices
    else:
        tile_size = vertices.max()
        minx, miny, maxx, maxy = bounds or [0, 0, tile_size, tile_size]
        x_scale = (maxx - minx) / tile_size
        y_scale = (maxy - miny) / tile_size

        if flip_y:
            scalar = np.array([x_scale, -y_scale])
            offset = np.array([minx, maxy])
        else:
            scalar = np.array([x_scale, y_scale])
            offset = np.array([minx, miny])

        # Rescale x, y positions
        positions[:, :2] = vertices * scalar + offset

    positions[:, 2] = terrain[vertices[:, 1], vertices[:, 0]]

    return positions
