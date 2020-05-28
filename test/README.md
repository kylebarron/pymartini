# Tests

## JS Mesh Generation

To compare against Martini, I create JSON data files of meshes created with
Martini. To generate these tests, you need to have Node/NPM set up, then run

```bash
npm install
node create_test_data.js
```

This generates `./data/{fuji,terrarium}_{5,20,50,100,500}.json`, a set of JSON
files holding the `vertices` and `triangles` output from `getMesh`.

## Data Sources

```
11_386_803.png
```

is a file from AWS' Open Terrain Tiles dataset, encoded with the Terrarium
encoding. It's selected from `x=385, y=803, z=11` (Grand Canyon, U.S.). It's
256x256 pixels.

```
fuji.png
```

is the test file from the Martini JS library, and comes from the Mapbox Terrain
RGB data source. It's 512x512 pixels.
