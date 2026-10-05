import numpy as np

from pymartini import Martini

# A 3x3 grid (indexed [y, x]) whose center lies on the shared long edge of the
# two top-level triangles, from (0, 0) to (2, 2). In float32, 2**24 + 1 rounds
# to 2**24, so the interpolated height at the center is only exact if it's
# computed in double precision, as Martini (JS) does: (2**24 + 1) / 2 =
# 2**23 + 0.5, an error of 0.5 against the center height of 2**23. All other
# triangles interpolate their midpoints exactly, with zero error.
TERRAIN = np.array(
    [
        [2**24, 2**23, 0],
        [2**23, 2**23, 0.5],
        [0, 0.5, 1],
    ],
    dtype=np.float32,
)


def test_errors_computed_in_double_precision():
    tile = Martini(3).create_tile(TERRAIN)
    errors = np.asarray(tile.errors_view).reshape(3, 3)
    expected = np.zeros((3, 3), dtype=np.float32)
    expected[1, 1] = 0.5
    np.testing.assert_array_equal(errors, expected)


def test_mesh_refines_on_sub_float32_error():
    tile = Martini(3).create_tile(TERRAIN)
    # The center error of 0.5 exceeds max_error, so each of the two top-level
    # triangles is split in two
    _, triangles = tile.get_mesh(0.25)
    assert len(triangles) == 4 * 3
