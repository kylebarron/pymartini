import numpy as np
import pytest

from pymartini import Martini


def test_fuji_mesh(fuji):
    # Matches the benchmark output documented in the README, and Martini's
    martini = Martini(fuji.shape[0])
    vertices, triangles = martini.create_tile(fuji).get_mesh(30)
    assert len(vertices) / 2 == 9704
    assert len(triangles) / 3 == 19086


def test_output_types(fuji):
    vertices, triangles = Martini(fuji.shape[0]).create_tile(fuji).get_mesh(30)
    assert vertices.dtype == np.uint16
    assert triangles.dtype == np.uint32
    assert vertices.ndim == 1
    assert triangles.ndim == 1
    assert len(vertices) % 2 == 0
    assert len(triangles) % 3 == 0


def test_triangles_index_vertices(fuji):
    vertices, triangles = Martini(fuji.shape[0]).create_tile(fuji).get_mesh(30)
    num_vertices = len(vertices) // 2
    assert triangles.max() == num_vertices - 1
    # Every vertex is used by some triangle
    assert len(np.unique(triangles)) == num_vertices


def test_vertices_within_grid(fuji):
    vertices, _ = Martini(fuji.shape[0]).create_tile(fuji).get_mesh(30)
    assert vertices.min() == 0
    assert vertices.max() == fuji.shape[0] - 1


def test_lower_max_error_gives_more_triangles(fuji):
    tile = Martini(fuji.shape[0]).create_tile(fuji)
    _, coarse = tile.get_mesh(30)
    _, fine = tile.get_mesh(5)
    assert len(fine) > len(coarse)


def test_get_mesh_is_repeatable(fuji):
    # get_mesh resets its internal state, so a tile can be reused
    tile = Martini(fuji.shape[0]).create_tile(fuji)
    first = tile.get_mesh(10)
    tile.get_mesh(50)
    second = tile.get_mesh(10)
    np.testing.assert_array_equal(first[0], second[0])
    np.testing.assert_array_equal(first[1], second[1])


def test_martini_reused_across_tiles(fuji):
    martini = Martini(fuji.shape[0])
    expected = martini.create_tile(fuji).get_mesh(10)
    martini.create_tile(np.zeros_like(fuji)).get_mesh(10)
    result = martini.create_tile(fuji).get_mesh(10)
    np.testing.assert_array_equal(result[0], expected[0])
    np.testing.assert_array_equal(result[1], expected[1])


def test_flat_input_matches_2d(fuji):
    martini = Martini(fuji.shape[0])
    vertices_2d, triangles_2d = martini.create_tile(fuji).get_mesh(30)
    vertices_1d, triangles_1d = martini.create_tile(fuji.ravel()).get_mesh(30)
    np.testing.assert_array_equal(vertices_1d, vertices_2d)
    np.testing.assert_array_equal(triangles_1d, triangles_2d)


def test_flat_terrain():
    # A flat surface is approximated exactly by the two top-level triangles
    terrain = np.zeros((257, 257), dtype=np.float32)
    vertices, triangles = Martini(257).create_tile(terrain).get_mesh(0)
    assert len(vertices) / 2 == 4
    assert len(triangles) / 3 == 2
    corners = {tuple(v) for v in vertices.reshape(-1, 2)}
    assert corners == {(0, 0), (0, 256), (256, 0), (256, 256)}


def test_default_grid_size():
    assert Martini().grid_size == 257


@pytest.mark.parametrize("grid_size", [256, 258, 300])
def test_invalid_grid_size(grid_size):
    with pytest.raises(ValueError, match="Expected grid size to be 2\\^n\\+1"):
        Martini(grid_size)


def test_invalid_terrain_length():
    terrain = np.zeros((256, 256), dtype=np.float32)
    with pytest.raises(ValueError, match="Expected terrain data of length 66049"):
        Martini(257).create_tile(terrain)


def test_terrain_must_be_float32():
    terrain = np.zeros((257, 257), dtype=np.float64)
    with pytest.raises(ValueError, match="Buffer dtype mismatch"):
        Martini(257).create_tile(terrain)
