import numpy as np


def decode_ele(png, encoding, backfill=True):
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

    return terrain.flatten('C')


def compute_backfill(arr):
    grid_size = arr.shape[0] + 1

    terrain = np.zeros((grid_size, grid_size), dtype=np.float32)

    # Copy to larger array to allow backfilling
    np.copyto(terrain[:grid_size - 1, :grid_size - 1], arr)

    # backfill right and bottom borders
    terrain[grid_size - 1, :] = terrain[grid_size - 2, :]
    terrain[:, grid_size - 1] = terrain[:, grid_size - 2]
    return terrain
