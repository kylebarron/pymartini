"""Helpers for decoding elevation tiles and rescaling Martini output."""

from __future__ import annotations

import numpy as np

# Arrays with at most this many entries in the first axis are assumed to be
# band-first and are transposed to band-last
_MAX_BANDS = 4


def decode_ele(
    png: np.ndarray,
    encoding: str,
    backfill: bool = True,  # noqa: FBT001, FBT002 (positional for backwards compatibility)
) -> np.ndarray:
    """Decode an RGB-encoded elevation array to elevations.

    Args:
        png: Array of elevations encoded in three channels, representing red,
            green, and blue. Must be of shape (tile_size, tile_size, >=3) or
            (>=3, tile_size, tile_size), where `tile_size` is usually 256 or
            512.
        encoding: Either `"mapbox"` or `"terrarium"`, the two main RGB
            encodings for elevation values.
        backfill: Whether to create an array of size (tile_size + 1,
            tile_size + 1), backfilling the bottom and right edges. This is
            used because Martini needs a grid of size 2^n + 1.

    Returns:
        Array with decoded elevation values. If `backfill` is `True`, the
        shape is (tile_size + 1, tile_size + 1) and the dtype is `float32`,
        otherwise the shape is (tile_size, tile_size).

    """
    allowed_encodings = ["mapbox", "terrarium"]
    if encoding not in allowed_encodings:
        raise ValueError(f"encoding must be one of {allowed_encodings}")

    if png.shape[0] <= _MAX_BANDS:
        png = png.T

    # Promote to float so integer (e.g. uint8) inputs don't overflow, since
    # numpy 2 keeps the array's dtype when multiplying by a Python int
    png = png.astype(np.float64)

    # Get bands
    if encoding == "mapbox":
        red = png[:, :, 0] * (256 * 256)
        green = png[:, :, 1] * (256)
        blue = png[:, :, 2]

        # Compute float height
        terrain = (red + green + blue) / 10 - 10000
    elif encoding == "terrarium":
        red = png[:, :, 0] * (256)
        green = png[:, :, 1]
        blue = png[:, :, 2] / 256

        # Compute float height
        terrain = (red + green + blue) - 32768

    if backfill:
        terrain = compute_backfill(terrain)

    return terrain


def compute_backfill(arr: np.ndarray) -> np.ndarray:
    """Pad a square array by one row and column, copying the last row/column.

    Args:
        arr: Square array of shape (tile_size, tile_size).

    Returns:
        `float32` array of shape (tile_size + 1, tile_size + 1).

    """
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
    bounds: tuple[float, float, float, float] | None = None,
    flip_y: bool = False,  # noqa: FBT001, FBT002 (positional for backwards compatibility)
) -> np.ndarray:
    """Rescale positions and add height as third dimension.

    Args:
        vertices: Vertices output from Martini.
        terrain: 2D array of elevations as output by `decode_ele`. This must
            be the same array that was passed to `Martini.create_tile`.
        bounds: Linearly rescale position values to this extent, expected to
            be `[minx, miny, maxx, maxy]`. If not provided, no rescaling is
            done.
        flip_y: Flip y coordinates. Useful when the original data source is a
            PNG, since the origin of a PNG is the top left.

    Returns:
        `float32` array of shape (-1, 3) with positions rescaled and including
        elevations. Each row represents a single 3D point.

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
