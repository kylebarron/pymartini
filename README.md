# pymartini

A Cython port of [Martini][martini] for fast RTIN terrain mesh generation, 2-3x
faster than Martini in Node. The only dependency is Numpy.

## Install

Currently only source builds are provided, so you'll need to have Cython and a C
compiler available during installation. Pull requests are welcome to package as
platform-specific wheels.

```
pip install pymartini
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

### Utilities

A few utilities are included.

#### `decode_ele`

A helper function to decode a PNG terrain tile into elevations.

##### Arguments

- `png` (np.ndarray): Ndarray of elevations encoded in three channels,
  representing red, green, and blue. Must be of shape (`tile_size`,
  `tile_size`, >=3), where `tile_size` is usually 256 or 512
- `encoding` (str): Either 'mapbox' or 'terrarium', the two main RGB
  encodings for elevation values

##### Returns

- (np.array) Array of shape (tile_size^2) with decoded elevation values

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
output is of the form `[x1, y1, z1, x2, y2, z2, ...]`.

##### Arguments

- `vertices`: (`np.array`) vertices output from Martini
- `terrain`: (`np.array`) array of elevations
- `tile_size`: (`int`) Original array size. Used to select the right values from
  the terrain array.
- `bounds`: (`List[float]`, default `None`) linearly rescale position values to
  this extent, expected to be [minx, miny, maxx, maxy]. If not provided,
  rescales to `[0, 0, tile_size, tile_size]`.
- flip_y: (`bool`, default `False`) Flip y coordinates. Can be useful when
  original data source is a PNG, since the origin of a PNG is the top left.

##### Returns

- (`np.array`): Array with positions rescaled and including elevations

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
    tile_size=png.shape[0],
    bounds=bounds,
    flip_y=True
)
```

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

## Benchmark

Preparation steps are about 3x faster in Python than in Node; generating the
mesh is about 2x faster in Python than in Node.

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

### Python

```bash
git clone https://github.com/kylebarron/pymartini
cd pymartini
pip install .
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
