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
        terrain[y * gridSize + x] = r * 256 + g + b / 256 - 32768;
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

function createTestData(name, mapboxEncoding, maxErrors = []) {
  // Load png
  var png = PNG.sync.read(fs.readFileSync(`./data/${name}.png`));
  var terrain = terrainToGrid(png, mapboxEncoding);

  // Write terrain data output
  fs.writeFileSync(`./data/${name}_terrain`, terrain, "binary");

  var martini = new Martini(png.width + 1);
  var tile = martini.createTile(terrain);

  // Write errors output
  fs.writeFileSync(`./data/${name}_errors`, tile.errors, "binary");

  for (var maxError of maxErrors) {
    var { vertices, triangles } = tile.getMesh(maxError);
    fs.writeFileSync(`./data/${name}_vertices_${maxError}`, vertices, "binary");
    fs.writeFileSync(
      `./data/${name}_triangles_${maxError}`,
      triangles,
      "binary"
    );
  }
}

function main() {
  createTestData("fuji", true, [5, 20, 50, 100, 500]);
  createTestData("terrarium", false, [5, 20, 50, 100, 500]);
}

main();
