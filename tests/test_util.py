import numpy as np
import pytest

from pymartini import Martini, decode_ele, rescale_positions
from pymartini.util import compute_backfill


def _rgb_tile(rgb) -> np.ndarray:
    # Use a tile larger than 4px so decode_ele doesn't treat it as band-first
    return np.tile(np.array(rgb, dtype=np.uint8), (8, 8, 1))


def test_decode_ele_mapbox_uint8():
    # (3776 + 10000) * 10 = 137760 = 2 * 65536 + 26 * 256 + 32
    png = _rgb_tile([2, 26, 32])
    terrain = decode_ele(png, "mapbox", backfill=False)
    assert terrain.shape == (8, 8)
    np.testing.assert_allclose(terrain, 3776)


def test_decode_ele_terrarium_uint8():
    # 3776.5 + 32768 = 36544.5 = 142 * 256 + 192 + 128 / 256
    png = _rgb_tile([142, 192, 128])
    terrain = decode_ele(png, "terrarium", backfill=False)
    np.testing.assert_allclose(terrain, 3776.5)


def test_decode_ele_backfill_uint8():
    png = _rgb_tile([2, 26, 32])
    terrain = decode_ele(png, "mapbox")
    assert terrain.shape == (9, 9)
    assert terrain.dtype == np.float32
    np.testing.assert_allclose(terrain, 3776)


def test_decode_ele_band_first():
    png = np.moveaxis(_rgb_tile([2, 26, 32]), -1, 0)
    assert png.shape == (3, 8, 8)
    terrain = decode_ele(png, "mapbox")
    assert terrain.shape == (9, 9)
    np.testing.assert_allclose(terrain, 3776)


def test_decode_ele_ignores_alpha_band():
    png = _rgb_tile([2, 26, 32, 255])
    np.testing.assert_allclose(decode_ele(png, "mapbox"), 3776)


def test_decode_ele_invalid_encoding():
    with pytest.raises(ValueError, match="encoding must be one of"):
        decode_ele(_rgb_tile([0, 0, 0]), "unknown")


def test_compute_backfill():
    arr = np.arange(9, dtype=np.float64).reshape(3, 3)
    out = compute_backfill(arr)
    assert out.dtype == np.float32
    expected = np.array(
        [
            [0, 1, 2, 2],
            [3, 4, 5, 5],
            [6, 7, 8, 8],
            [6, 7, 8, 8],
        ]
    )
    np.testing.assert_array_equal(out, expected)


# A 3x3 terrain, indexed [y, x], and vertices given as interleaved x, y pairs
TERRAIN = np.arange(9, dtype=np.float32).reshape(3, 3)
VERTICES = np.array([0, 0, 2, 0, 0, 2, 2, 2, 1, 2], dtype=np.uint16)


def test_rescale_positions_no_bounds():
    out = rescale_positions(VERTICES, TERRAIN)
    expected = np.array(
        [[0, 0, 0], [2, 0, 2], [0, 2, 6], [2, 2, 8], [1, 2, 7]],
    )
    assert out.dtype == np.float32
    np.testing.assert_array_equal(out, expected)


def test_rescale_positions_bounds():
    out = rescale_positions(VERTICES, TERRAIN, bounds=(-10, 20, 0, 40))
    expected = np.array(
        [[-10, 20, 0], [0, 20, 2], [-10, 40, 6], [0, 40, 8], [-5, 40, 7]],
    )
    np.testing.assert_allclose(out, expected)


def test_rescale_positions_flip_y():
    out = rescale_positions(VERTICES, TERRAIN, bounds=(-10, 20, 0, 40), flip_y=True)
    expected = np.array(
        [[-10, 40, 0], [0, 40, 2], [-10, 20, 6], [0, 20, 8], [-5, 20, 7]],
    )
    np.testing.assert_allclose(out, expected)


def test_rescale_positions_positional_args():
    out = rescale_positions(VERTICES, TERRAIN, (-10, 20, 0, 40), True)  # noqa: FBT003
    expected = rescale_positions(
        VERTICES, TERRAIN, bounds=(-10, 20, 0, 40), flip_y=True
    )
    np.testing.assert_array_equal(out, expected)


def test_rescale_positions_2d_vertices():
    out = rescale_positions(VERTICES.reshape(-1, 2), TERRAIN)
    np.testing.assert_array_equal(out, rescale_positions(VERTICES, TERRAIN))


def test_rescale_positions_mesh_heights(fuji):
    vertices, _ = Martini(fuji.shape[0]).create_tile(fuji).get_mesh(30)
    out = rescale_positions(vertices, fuji)
    assert out.shape == (len(vertices) // 2, 3)
    xy = vertices.reshape(-1, 2)
    np.testing.assert_array_equal(out[:, 2], fuji[xy[:, 1], xy[:, 0]])
