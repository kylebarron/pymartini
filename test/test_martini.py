from pathlib import Path

import numpy as np
import pytest
from imageio import imread

from pymartini import Martini, decode_ele

TEST_PNG_FILES = [
    ("fuji", "mapbox"),
    ("mapbox_st_helens", "mapbox"),
    ("terrarium", "terrarium"),
]
TEST_CASES = [
    (png_fname, max_error, encoding)
    for png_fname, encoding in TEST_PNG_FILES
    for max_error in [1, 5, 20, 50, 100, 500]
]

DATA_DIR = Path(__file__).parent / "data"


@pytest.mark.parametrize(("png_fname", "encoding"), TEST_PNG_FILES)
def test_terrain(png_fname, encoding):
    """Test output from decode_ele against JS output."""
    # Generate terrain output in Python
    png = imread(DATA_DIR / f"{png_fname}.png")
    terrain = decode_ele(png, encoding=encoding).flatten("C")

    # Load JS terrain output
    exp_terrain = np.fromfile(DATA_DIR / f"{png_fname}_terrain", dtype=np.float32)

    assert np.array_equal(terrain, exp_terrain), "terrain not matching expected"


@pytest.mark.parametrize("png_fname", [png_fname for png_fname, _ in TEST_PNG_FILES])
def test_martini(png_fname):
    """Test output from the Martini constructor against JS output."""
    # Generate Martini constructor output in Python
    png = imread(DATA_DIR / f"{png_fname}.png")
    martini = Martini(png.shape[0] + 1)
    indices = np.asarray(martini.indices_view, dtype=np.uint32)
    coords = np.asarray(martini.coords_view, dtype=np.uint16)

    # Load JS Martini output
    exp_indices = np.fromfile(
        DATA_DIR / f"{png_fname}_martini_indices", dtype=np.uint32
    )
    exp_coords = np.fromfile(DATA_DIR / f"{png_fname}_martini_coords", dtype=np.uint16)

    assert np.array_equal(indices, exp_indices), "indices not matching expected"
    assert np.array_equal(coords, exp_coords), "coords not matching expected"


@pytest.mark.parametrize(("png_fname", "encoding"), TEST_PNG_FILES)
def test_errors(png_fname, encoding):
    """Test errors output from martini.create_tile(terrain)."""
    # Generate errors output in Python
    png = imread(DATA_DIR / f"{png_fname}.png")
    terrain = decode_ele(png, encoding=encoding)
    martini = Martini(png.shape[0] + 1)
    tile = martini.create_tile(terrain)
    errors = np.asarray(tile.errors_view, dtype=np.float32)

    # Load JS errors output
    exp_errors = np.fromfile(DATA_DIR / f"{png_fname}_errors", dtype=np.float32)

    assert np.array_equal(errors, exp_errors), "errors not matching expected"


@pytest.mark.parametrize(("png_fname", "max_error", "encoding"), TEST_CASES)
def test_mesh(png_fname, max_error, encoding):
    # Generate mesh output in Python
    png = imread(DATA_DIR / f"{png_fname}.png")
    terrain = decode_ele(png, encoding=encoding)
    martini = Martini(png.shape[0] + 1)
    tile = martini.create_tile(terrain)
    vertices, triangles = tile.get_mesh(max_error)

    # Load JS mesh output
    exp_vertices = np.fromfile(
        DATA_DIR / f"{png_fname}_vertices_{max_error}", dtype=np.uint16
    )
    exp_triangles = np.fromfile(
        DATA_DIR / f"{png_fname}_triangles_{max_error}", dtype=np.uint32
    )

    assert np.array_equal(vertices, exp_vertices), "vertices not matching expected"
    assert np.array_equal(triangles, exp_triangles), "triangles not matching expected"
