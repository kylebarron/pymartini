"""Compare pymartini's output to Martini (JS) on the test tiles.

The expected output is stored as digests in `data/martini_js.json`. See
`martini_js/create_test_data.js` to regenerate it.
"""

import hashlib
from pathlib import Path

import imageio.v3 as iio
import numpy as np
import pytest

from pymartini import Martini, decode_ele

DATA_DIR = Path(__file__).parent / "data"

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


def assert_matches_js(arr, expected, name):
    arr = np.asarray(arr)
    assert arr.dtype == np.dtype(expected["dtype"]), f"{name} dtype"
    assert arr.size == expected["length"], f"{name} length"
    # Martini's typed arrays are little-endian
    data = arr.astype(arr.dtype.newbyteorder("<")).tobytes()
    sha256 = hashlib.sha256(data).hexdigest()
    assert sha256 == expected["sha256"], f"{name} not matching expected"


def read_png(png_fname):
    return iio.imread(DATA_DIR / f"{png_fname}.png")


@pytest.mark.parametrize(("png_fname", "encoding"), TEST_PNG_FILES)
def test_terrain(martini_js, png_fname, encoding):
    """Test output from decode_ele against JS output."""
    terrain = decode_ele(read_png(png_fname), encoding=encoding).flatten("C")
    assert_matches_js(terrain, martini_js[png_fname]["terrain"], "terrain")


@pytest.mark.parametrize("png_fname", [png_fname for png_fname, _ in TEST_PNG_FILES])
def test_martini(martini_js, png_fname):
    """Test output from the Martini constructor against JS output."""
    martini = Martini(read_png(png_fname).shape[0] + 1)
    expected = martini_js[png_fname]
    assert_matches_js(martini.indices_view, expected["martini_indices"], "indices")
    assert_matches_js(martini.coords_view, expected["martini_coords"], "coords")


@pytest.mark.parametrize(("png_fname", "encoding"), TEST_PNG_FILES)
def test_errors(martini_js, png_fname, encoding):
    """Test errors output from martini.create_tile(terrain) against JS output."""
    png = read_png(png_fname)
    terrain = decode_ele(png, encoding=encoding)
    tile = Martini(png.shape[0] + 1).create_tile(terrain)
    assert_matches_js(tile.errors_view, martini_js[png_fname]["errors"], "errors")


@pytest.mark.parametrize(("png_fname", "max_error", "encoding"), TEST_CASES)
def test_mesh(martini_js, png_fname, max_error, encoding):
    """Test output from tile.get_mesh(max_error) against JS output."""
    png = read_png(png_fname)
    terrain = decode_ele(png, encoding=encoding)
    tile = Martini(png.shape[0] + 1).create_tile(terrain)
    vertices, triangles = tile.get_mesh(max_error)

    expected = martini_js[png_fname]["meshes"][str(max_error)]
    assert_matches_js(vertices, expected["vertices"], "vertices")
    assert_matches_js(triangles, expected["triangles"], "triangles")
