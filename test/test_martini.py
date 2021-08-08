from pathlib import Path

import numpy as np
import pytest
from imageio import imread

from pymartini import Martini, decode_ele

TEST_PNG_FILES = [
    ('fuji', 'mapbox'),
    ('mapbox_st_helens', 'mapbox'),
    ('terrarium', 'terrarium'),
]
TEST_CASES = []
for _png_fname, _encoding in TEST_PNG_FILES:
    for _max_error in [1, 5, 20, 50, 100, 500]:
        TEST_CASES.append([_png_fname, _max_error, _encoding])


def this_dir():
    try:
        return Path(__file__).resolve().parents[0]
    except NameError:
        return Path('.').resolve()


@pytest.mark.parametrize("png_fname,encoding", TEST_PNG_FILES)
def test_terrain(png_fname, encoding):
    """Test output from decode_ele against JS output"""
    # Generate terrain output in Python
    path = this_dir() / f'data/{png_fname}.png'
    png = imread(path)
    terrain = decode_ele(png, encoding=encoding).flatten('C')

    # Load JS terrain output
    path = this_dir() / f'data/{png_fname}_terrain'
    with open(path, 'rb') as f:
        exp_terrain = np.frombuffer(f.read(), dtype=np.float32)

    assert np.array_equal(terrain, exp_terrain), 'terrain not matching expected'


@pytest.mark.parametrize("png_fname,encoding", TEST_PNG_FILES)
def test_martini(png_fname, encoding):
    """Test output from decode_ele against JS output"""
    # pylint: disable=unused-argument

    # Generate Martini constructor output in Python
    path = this_dir() / f'data/{png_fname}.png'
    png = imread(path)
    martini = Martini(png.shape[0] + 1)
    indices = np.asarray(martini.indices_view, dtype=np.uint32)
    coords = np.asarray(martini.coords_view, dtype=np.uint16)

    # Load JS terrain output
    path = this_dir() / f'data/{png_fname}_martini_indices'
    with open(path, 'rb') as f:
        exp_indices = np.frombuffer(f.read(), dtype=np.uint32)

    path = this_dir() / f'data/{png_fname}_martini_coords'
    with open(path, 'rb') as f:
        exp_coords = np.frombuffer(f.read(), dtype=np.uint16)

    assert np.array_equal(indices, exp_indices), 'indices not matching expected'
    assert np.array_equal(coords, exp_coords), 'coords not matching expected'


@pytest.mark.parametrize("png_fname,encoding", TEST_PNG_FILES)
def test_errors(png_fname, encoding):
    """Test errors output from martini.create_tile(terrain)"""
    # Generate errors output in Python
    path = this_dir() / f'data/{png_fname}.png'
    png = imread(path)
    terrain = decode_ele(png, encoding=encoding)
    martini = Martini(png.shape[0] + 1)
    tile = martini.create_tile(terrain)
    errors = np.asarray(tile.errors_view, dtype=np.float32)

    # Load JS errors output
    path = this_dir() / f'data/{png_fname}_errors'
    with open(path, 'rb') as f:
        exp_errors = np.frombuffer(f.read(), dtype=np.float32)

    assert np.array_equal(errors, exp_errors), 'errors not matching expected'


@pytest.mark.parametrize("png_fname,max_error,encoding", TEST_CASES)
def test_mesh(png_fname, max_error, encoding):
    # Generate mesh output in Python
    path = this_dir() / f'data/{png_fname}.png'
    png = imread(path)
    terrain = decode_ele(png, encoding=encoding)
    martini = Martini(png.shape[0] + 1)
    tile = martini.create_tile(terrain)
    vertices, triangles = tile.get_mesh(max_error)

    # Load JS mesh output
    path = this_dir() / f'data/{png_fname}_vertices_{max_error}'
    with open(path, 'rb') as f:
        exp_vertices = np.frombuffer(f.read(), dtype=np.uint16)

    path = this_dir() / f'data/{png_fname}_triangles_{max_error}'
    with open(path, 'rb') as f:
        exp_triangles = np.frombuffer(f.read(), dtype=np.uint32)

    assert np.array_equal(vertices, exp_vertices), 'vertices not matching expected'
    assert np.array_equal(triangles, exp_triangles), 'triangles not matching expected'
