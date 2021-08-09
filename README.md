# pymartini

A Cython port of [Martini][martini] for fast RTIN terrain mesh generation, 2-3x
faster than Martini in Node. The only dependency is Numpy.

[![][image_url]][example]

[image_url]: https://raw.githubusercontent.com/kylebarron/pymartini/master/assets/grca_wireframe.jpg
[example]: https://kylebarron.dev/quantized-mesh-encoder

A wireframe rendering of the Grand Canyon. The mesh is created using
`pymartini`, encoded using [`quantized-mesh-encoder`][quantized-mesh-encoder],
served on-demand using [`dem-tiler`][dem-tiler], and rendered with
[deck.gl](https://deck.gl).

[quantized-mesh-encoder]: https://github.com/kylebarron/quantized-mesh-encoder
[dem-tiler]: https://github.com/kylebarron/dem-tiler

## Install

With pip:

```
pip install pymartini
```

or with Conda:

```
conda install -c conda-forge pymartini
```

## Using

### Example

The API is modeled after Martini.

```py
from pymartini import Martini

# set up mesh generator for a certain 2^k+1 grid size
# Usually either 257 or 513
martini = Martini(257)

# generate RTIN hierarchy from terrain data (an array of size^2 length)
tile = martini.create_tile(terrain)

# get a mesh (vertices and triangles indices) for a 10m error
vertices, triangles = tile.get_mesh(10)
```

### API

The `Martini` class and `create_tile` and `get_mesh` methods are a direct port
from the JS Martini library.

Additionally I include two helper functions: `decode_ele` to decode a Mapbox
Terrain RGB or Terrarium PNG array to elevations; and `rescale_positions`, which
adds elevations to each vertex and optionally linearly rescales each vertex's XY
coordinates to a new bounding box.

#### `Martini`

A class to instantiate constants needed for the `create_tile` and `get_mesh`
steps. As noted in the benchmarks below, instantiating the `Martini` class is
the slowest of the three functions. If you're planning to create many meshes of
the same size, create one `Martini` class and create many tiles from it.

##### Arguments

- `grid_size` (`int`, default `257`): the grid size to use when generating the
  mesh. Must be 2^k+1. If your source heightmap is 256x256 pixels, use
  `grid_size=257` and backfill the border pixels.

##### Returns

Returns a `Martini` instance on which you can call `create_tile`.

#### `Martini.create_tile`

Generate RTIN hierarchy from terrain data. This is faster than creating the
`Martini` instance, but slower than creating a mesh for a given max error. If
you need to create many meshes with different errors for the same tile, you
should reuse a `Tile` instance.

##### Arguments

- `terrain` (numpy `ndarray`): an array of dtype `float32` representing the
  input heightmap. The array can either be flattened, of shape (2^k+1 \* 2^k+1)
  or a two-dimensional array of shape (2^k+1, 2^k+1). Note that for a 2D array
  pymartini expects indices in (columns, rows) order, so you might need to
  transpose your array first. Currently an error will be produced if the dtype
  of your input array is not `np.float32`.

##### Returns

Returns a `Tile` instance on which you can call `get_mesh`.

#### `Tile.get_mesh`

Get a mesh for a given max error.

##### Arguments

- `max_error` (`float`, default `0`): the maximum vertical error for each
  triangle in the output mesh. For example if the units of the input heightmap
  is meters, using `max_error=5` would mean that the mesh is continually refined
  until every triangle approximates the surface of the heightmap within 5
  meters.

##### Returns

Returns a tuple of (`vertices`, `triangles`).

Each is a flat numpy array. Vertices represents the interleaved **2D**
coordinates of each vertex, e.g. `[x0, y0, x1, y1, ...]`. If you need 3D
coordinates, you can use the `rescale_positions` helper function described
below.

`triangles` represents _indices_ within the `vertices` array. So `[0, 1, 3, ...]` would use the first, second, and fourth vertices within the `vertices`
array as a single triangle.

#### `decode_ele`

A helper function to decode a PNG terrain tile into elevations.

##### Arguments

- `png` (`np.ndarray`): Ndarray of elevations encoded in three channels,
  representing red, green, and blue. Must be of shape (`tile_size`, `tile_size`,
  `>=3`) or (`>=3`, `tile_size`, `tile_size`), where `tile_size` is usually 256
  or 512
- `encoding` (`str`): Either 'mapbox' or 'terrarium', the two main RGB
  encodings for elevation values
- `backfill` (`bool`, default `True`): Whether to create an array of size
  (`tile_size + 1`, `tile_size + 1`), backfilling the bottom and right edges. This is used
  because Martini needs a grid of size `2^n + 1`

##### Returns

- (`np.ndarray`) Array with decoded elevation values. If `backfill` is `True`,
  returned shape is (`tile_size + 1`, `tile_size + 1`), otherwise returned shape
  is (`tile_size`, `tile_size`), where `tile_size` is the shape of the input
  array.

##### Example

```py
from imageio import imread
from pymartini import decode_ele

path = './test/data/fuji.png'
fuji = imread(path)
terrain = decode_ele(fuji, 'mapbox')
```

#### `rescale_positions`

A helper function to rescale the `vertices` output and add elevations. The
output is a numpy ndarray of the form `[[x1, y1, z1], [x2, y2, z2], ...]`.

##### Arguments

- `vertices`: (`np.array`) vertices output from Martini
- `terrain`: (`np.ndarray`) 2d heightmap array of elevations as output by
  `decode_ele`. Expected to have shape (`grid_size`, `grid_size`). **`terrain`
  is expected to be the exact same array passed to `Martini.create_tile`.** If
  you use a different or transposed array, the mesh will look weird. See
  [#15](https://github.com/kylebarron/pymartini/issues/15). If you need to
  transpose your array, do it before passing to `Martini.create_tile`.
- `bounds`: (`List[float]`, default `None`) linearly rescale position values to
  this extent, expected to be [minx, miny, maxx, maxy]. If not provided, no
  rescaling is done
- `flip_y`: (`bool`, default `False`) Flip y coordinates. Can be useful when
  original data source is a PNG, since the origin of a PNG is the top left.

##### Example

```py
from imageio import imread
from pymartini import decode_ele, Martini, rescale_positions

path = './test/data/terrarium.png'
png = imread(path)
terrain = decode_ele(png, 'mapbox')
martini = Martini(png.shape[0] + 1)
tile = martini.create_tile(terrain)
vertices, triangles = tile.get_mesh(10)

# Use mercantile to find the bounds in WGS84 of this tile
import mercantile
bounds = mercantile.bounds(mercantile.Tile(385, 803, 11))

# Rescale positions to WGS84
rescaled = rescale_positions(
    vertices,
    terrain,
    bounds=bounds,
    flip_y=True
    column_row=True
)
```

## `Martini` or `Delatin`?

Two popular algorithms for terrain mesh generation are the **"Martini"**
algorithm, found in the JavaScript [`martini`][martini] library and this Python
`pymartini` library, and the **"Delatin"** algorithm, found in the
C++ [`hmm`][hmm] library, the Python [`pydelatin`][pydelatin] library, and the JavaScript
[`delatin`][delatin] library.

Which to use?

For most purposes, use `pydelatin` over `pymartini`. A good breakdown from [a
Martini issue][martini_desc_issue]:

> Martini:
>
> - Only works on square 2^n+1 x 2^n+1 grids.
> - Generates a hierarchy of meshes (pick arbitrary detail after a single run)
> - Optimized for meshing speed rather than quality.
>
> Delatin:
>
> - Works on arbitrary raster grids.
> - Generates a single mesh for a particular detail.
> - Optimized for quality (as few triangles as possible for a given error).

[hmm]: https://github.com/fogleman/hmm
[pydelatin]: https://github.com/kylebarron/pydelatin
[delatin]: https://github.com/mapbox/delatin
[martini_desc_issue]: https://github.com/mapbox/martini/issues/15#issuecomment-700475731

## Correctness

`pymartini` passes the (only) test case included in the original Martini JS
library. I also wrote a few extra conformance tests to compare output by
`pymartini` and Martini. I've found some small differences in float values at
the end of the second step.

This second step, `martini.create_tile(terrain)`, computes the maximum error of
every possible triangle and accumulates them. Thus, small float errors appear to
be magnified by the summation of errors into larger triangles. These errors
appear to be within `1e-5` of the JS output. I'm guessing that this variance is
greater than normal float rounding errors, due to this summation behavior.

These differences are larger when using 512px tiles compared to 256px tiles,
which reinforces my hypothesis that the differences have something to do with
small low-level float or bitwise operations differences between Python and
JavaScript.

If you'd like to explore this in more detail, look at the `Tile.update()` in
`martini.pyx` and the corresponding Martini code.

## Type Checking

As of `pymartini` 0.4.0, types are provided, which can be used with a checker
like [`mypy`](https://mypy.readthedocs.io/). If you wish to get the full
benefit, make sure to [enable Numpy's mypy
plugin](https://numpy.org/devdocs/reference/typing.html#examples).

## Benchmark

Preparation steps are about 3x faster in Python than in Node; generating the
mesh is about 2x faster in Python than in Node.

### Python

```bash
git clone https://github.com/kylebarron/pymartini
cd pymartini
pip install '.[test]'
python bench.py
```

```
init tileset: 14.860ms
create tile: 5.862ms
mesh (max_error=30): 1.010ms
vertices: 9700.0, triangles: 19078.0
mesh 0: 18.350ms
mesh 1: 17.581ms
mesh 2: 15.245ms
mesh 3: 13.853ms
mesh 4: 11.284ms
mesh 5: 12.360ms
mesh 6: 8.293ms
mesh 7: 8.342ms
mesh 8: 7.166ms
mesh 9: 5.678ms
mesh 10: 5.886ms
mesh 11: 5.092ms
mesh 12: 3.732ms
mesh 13: 3.420ms
mesh 14: 3.524ms
mesh 15: 3.101ms
mesh 16: 2.892ms
mesh 17: 2.358ms
mesh 18: 2.250ms
mesh 19: 2.293ms
mesh 20: 2.281ms
20 meshes total: 155.559ms
```

### JS (Node)

```bash
git clone https://github.com/mapbox/martini
cd martini
npm install
node -r esm bench.js
```

```
init tileset: 54.293ms
create tile: 17.307ms
mesh: 6.230ms
vertices: 9704, triangles: 19086
mesh 0: 43.181ms
mesh 1: 33.102ms
mesh 2: 30.735ms
mesh 3: 25.935ms
mesh 4: 20.643ms
mesh 5: 17.511ms
mesh 6: 15.066ms
mesh 7: 13.334ms
mesh 8: 11.180ms
mesh 9: 9.651ms
mesh 10: 9.240ms
mesh 11: 10.996ms
mesh 12: 7.520ms
mesh 13: 6.617ms
mesh 14: 5.860ms
mesh 15: 5.693ms
mesh 16: 4.907ms
mesh 17: 4.469ms
mesh 18: 4.267ms
mesh 19: 4.267ms
mesh 20: 3.619ms
20 meshes total: 290.256ms
```

## License

This library is ported from Mapbox's [Martini][martini], which is licensed under
the ISC License. My additions are licensed under the MIT license.

ISC License

Copyright (c) 2019, Mapbox

Permission to use, copy, modify, and/or distribute this software for any purpose
with or without fee is hereby granted, provided that the above copyright notice
and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF
THIS SOFTWARE.

[martini]: https://github.com/mapbox/martini
