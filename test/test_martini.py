import json
from pathlib import Path

import numpy as np
import pytest
from imageio import imread

from pymartini import Martini, decode_ele

TEST_CASES = []
# terrarium
# Add terrarium when you have a terrarium_terrain_to_grid
for png_fname, encoding in [('fuji', 'mapbox'), ('terrarium', 'terrarium')]:
    for max_error in [5, 20, 50, 100, 500]:
        TEST_CASES.append([png_fname, max_error, encoding])


@pytest.mark.parametrize("png_fname,max_error,encoding", TEST_CASES)
def test_terrain(png_fname, max_error, encoding):
    """Test output from decode_ele against JS output
    """
    # Generate terrain output
    path = Path(__file__).parents[0] / f'data/{png_fname}.png'
    # path = './data/fuji.png'
    # path = './data/terrarium.png'

    png = imread(path)
    terrain = decode_ele(png, encoding=encoding)

    # Load JS terrain output
    path = Path(__file__).parents[0] / f'data/{png_fname}_terrain'
    with open(path, 'rb') as f:
        exp_terrain = np.frombuffer(f.read(), dtype=np.float32)

    assert np.array_equal(terrain, exp_terrain), 'terrain not matching expected'


@pytest.mark.parametrize("png_fname,max_error,encoding", TEST_CASES)
def test_mesh(png_fname, max_error, encoding):
    path = Path(__file__).parents[0] / f'data/{png_fname}.png'

    png = imread(path)
    terrain = decode_ele(png, encoding=encoding)

    martini = Martini(png.shape[0] + 1)
    tile = martini.create_tile(terrain)
    vertices, triangles = tile.get_mesh(max_error)

    # Load JS data
    with open(Path(__file__).parents[0] /
              f'data/{png_fname}_{max_error}.json') as f:
        data = json.load(f)

    msg = '`vertices` length does not match'
    assert len(vertices) == len(data['vertices']), msg
    assert np.array_equal(
        vertices, np.asarray(data['vertices'],
                             dtype=np.uint16)), '`vertices` values do not match'

    msg = '`triangles` length does not match'
    assert len(triangles) == len(data['triangles']), msg
    assert np.array_equal(
        triangles,
        np.asarray(data['triangles'],
                   dtype=np.uint16)), '`triangles` values do not match'
