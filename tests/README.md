# Tests

## Run Tests

In the root of the repository, run:

```
uv run pytest
```

## Comparing against Martini

`test_martini.py` checks that `pymartini` produces the same output as
[Martini](https://github.com/mapbox/martini) (JS) on the test tiles below: the
decoded terrain, the `Martini` constructor's arrays, the error map from
`create_tile`, and the meshes for several max errors.

Rather than storing Martini's output arrays (about 23MB), `data/martini_js.json`
stores the dtype, length and SHA-256 digest of each one. To regenerate it, you
need Node/NPM set up, then run:

```bash
cd tests/martini_js
npm install
node create_test_data.js
```

## Data Sources

### AWS Open Data Terrain Tiles

```
terrarium.png
```

is a file from AWS' Open Terrain Tiles dataset, encoded with the Terrarium
encoding. It's selected from `x=385, y=803, z=11` (Grand Canyon, U.S.). It's
256x256 pixels.

### Mapbox Terrain-RGB 512px

```
fuji.png
```

is the test file from the Martini JS library, and comes from the Mapbox Terrain
RGB data source. It's 512x512 pixels.

### Mapbox Terrain-RGB 256px

```
mapbox_st_helens.png
```

is `x=2630`, `y=5812`, `z=14`, i.e.

```
https://api.mapbox.com/v4/mapbox.terrain-rgb/14/2630/5812.png?access_token=...
```
