import json
from pathlib import Path

import imageio.v3 as iio
import numpy as np
import pytest

from pymartini import decode_ele

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def martini_js() -> dict:
    """Digests of Martini (JS) output, from `martini_js/create_test_data.js`."""
    with (DATA_DIR / "martini_js.json").open() as f:
        return json.load(f)


@pytest.fixture(scope="session")
def fuji() -> np.ndarray:
    """513x513 backfilled Mapbox Terrain-RGB heightmap of Mt. Fuji, in meters."""
    png = iio.imread(DATA_DIR / "fuji.png")
    return decode_ele(png, "mapbox")
