var fs = require("fs");
var { PNG } = require("pngjs");
var Martini = require("@mapbox/martini");

function terrainToGrid(png, mapbox) {
  const gridSize = png.width + 1;
  const terrain = new Float32Array(gridSize * gridSize);

  const tileSize = png.width;

  // decode terrain values
  for (let y = 0; y < tileSize; y++) {
    for (let x = 0; x < tileSize; x++) {
      const k = (y * tileSize + x) * 4;
      const r = png.data[k + 0];
      const g = png.data[k + 1];
      const b = png.data[k + 2];
      if (mapbox) {
        // Mapbox encoding
        terrain[y * gridSize + x] =
          (r * 256 * 256 + g * 256.0 + b) / 10.0 - 10000.0;
      } else {
        // Terrarium encoding
        terrain[y * gridSize + x] = ((r * 256) + g + (b / 256)) - 32768;
      }
    }
  }
  // backfill right and bottom borders
  for (let x = 0; x < gridSize - 1; x++) {
    terrain[gridSize * (gridSize - 1) + x] =
      terrain[gridSize * (gridSize - 2) + x];
  }
  for (let y = 0; y < gridSize; y++) {
    terrain[gridSize * y + gridSize - 1] = terrain[gridSize * y + gridSize - 2];
  }

  return terrain;
}

function main() {
  // Fuji mapbox tile
  var fuji = PNG.sync.read(fs.readFileSync("./data/fuji.png"));
  var terrain = terrainToGrid(fuji, true);
  var martini = new Martini(fuji.width + 1);
  var tile = martini.createTile(terrain);

  for (var i of [5, 20, 50, 100, 500]) {
    var { vertices, triangles } = tile.getMesh(i);
    // Coerce to regular arrays so they can be json encoded
    var out = {
      vertices: Array.from(vertices),
      triangles: Array.from(triangles)
    };
    fs.writeFileSync(`./data/fuji_${i}.json`, JSON.stringify(out));
  }

  // Grand Canyon Terrarium tile
  var terrarium = PNG.sync.read(fs.readFileSync("./data/terrarium.png"));
  var terrain = terrainToGrid(terrarium, false);
  var martini = new Martini(terrarium.width + 1);
  var tile = martini.createTile(terrain);

  for (var i of [5, 20, 50, 100, 500]) {
    var { vertices, triangles } = tile.getMesh(i);
    // Coerce to regular arrays so they can be json encoded
    var out = {
      vertices: Array.from(vertices),
      triangles: Array.from(triangles)
    };
    fs.writeFileSync(`./data/terrarium_${i}.json`, JSON.stringify(out));
  }
}

main();
