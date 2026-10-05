// Run Martini (JS) on the test tiles and write a digest of each output array
// to ../data/martini_js.json. The Python tests compare pymartini's output to
// these digests. Storing digests instead of the raw arrays keeps about 23MB of
// binary fixtures out of the repository.
var crypto = require("crypto");
var fs = require("fs");
var path = require("path");
var { PNG } = require("pngjs");
var Martini = require("@mapbox/martini");

var DATA_DIR = path.join(__dirname, "..", "data");

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

// Summarize a typed array by its dtype, length, and the SHA-256 of its
// little-endian bytes
function digest(arr) {
  var dtypes = {
    Float32Array: "float32",
    Uint16Array: "uint16",
    Uint32Array: "uint32",
  };
  var bytes = Buffer.from(arr.buffer, arr.byteOffset, arr.byteLength);
  return {
    dtype: dtypes[arr.constructor.name],
    length: arr.length,
    sha256: crypto.createHash("sha256").update(bytes).digest("hex"),
  };
}

function createTestData(name, mapboxEncoding, maxErrors = []) {
  // Load png
  var png = PNG.sync.read(fs.readFileSync(path.join(DATA_DIR, `${name}.png`)));
  var terrain = terrainToGrid(png, mapboxEncoding);

  var output = { terrain: digest(terrain) };

  // Digest the constructor output before getMesh, which writes to
  // martini.indices
  var martini = new Martini(png.width + 1);
  output.martini_indices = digest(martini.indices);
  output.martini_coords = digest(martini.coords);

  var tile = martini.createTile(terrain);
  output.errors = digest(tile.errors);

  var meshes = {};
  for (var maxError of maxErrors) {
    var { vertices, triangles } = tile.getMesh(maxError);
    meshes[maxError] = {
      vertices: digest(vertices),
      triangles: digest(triangles),
    };
  }

  output.meshes = meshes;
  return output;
}

function main() {
  var maxErrors = [1, 5, 20, 50, 100, 500];
  var output = {
    fuji: createTestData("fuji", true, maxErrors),
    mapbox_st_helens: createTestData("mapbox_st_helens", true, maxErrors),
    terrarium: createTestData("terrarium", false, maxErrors),
  };
  fs.writeFileSync(
    path.join(DATA_DIR, "martini_js.json"),
    JSON.stringify(output, null, 2) + "\n"
  );
}

main();
