# Tests

## JS Mesh Generation

To compare against Martini, I create JSON data files of meshes created with
Martini. To generate these tests, you need to have Node/NPM set up, then run

```bash
npm install
node create_test_data.js
```

This generates files in the `data/` folder to compare against Python output.

## Run Tests

In the root of the repository, run:

```
pip install '.[test]'
pytest
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
