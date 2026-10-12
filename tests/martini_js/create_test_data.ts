// Run Martini (JS) on the test tiles and write a digest of each output array
// to ../data/martini_js.json. The Python tests compare pymartini's output to
// these digests. Storing digests instead of the raw arrays keeps about 23MB of
// binary fixtures out of the repository.
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import Martini from "@mapbox/martini";
import { PNG } from "pngjs";

const DATA_DIR = join(import.meta.dirname, "..", "data");

const MAX_ERRORS = [1, 5, 20, 50, 100, 500];

type Encoding = "mapbox" | "terrarium";

const TILES: Record<string, Encoding> = {
  fuji: "mapbox",
  mapbox_st_helens: "mapbox",
  terrarium: "terrarium",
};

type Decoder = (r: number, g: number, b: number) => number;

const DECODERS: Record<Encoding, Decoder> = {
  mapbox: (r, g, b) => (r * 256 * 256 + g * 256 + b) / 10 - 10000,
  terrarium: (r, g, b) => r * 256 + g + b / 256 - 32768,
};

type DigestArray = Float32Array | Uint16Array | Uint32Array;

interface Digest {
  dtype: "float32" | "uint16" | "uint32";
  length: number;
  sha256: string;
}

interface TileDigests {
  terrain: Digest;
  martini_indices: Digest;
  martini_coords: Digest;
  errors: Digest;
  meshes: Record<number, { vertices: Digest; triangles: Digest }>;
}

// Decode a PNG into a (tileSize + 1)^2 elevation grid, backfilling the extra
// right column and bottom row from their neighbors
function terrainToGrid(png: PNG, encoding: Encoding): Float32Array {
  const decode = DECODERS[encoding];
  const tileSize = png.width;
  const gridSize = tileSize + 1;
  const terrain = new Float32Array(gridSize * gridSize);

  for (let y = 0; y < tileSize; y++) {
    for (let x = 0; x < tileSize; x++) {
      const k = (y * tileSize + x) * 4;
      terrain[y * gridSize + x] = decode(
        png.data[k],
        png.data[k + 1],
        png.data[k + 2],
      );
    }
  }

  for (let x = 0; x < gridSize - 1; x++) {
    terrain[gridSize * (gridSize - 1) + x] =
      terrain[gridSize * (gridSize - 2) + x];
  }
  for (let y = 0; y < gridSize; y++) {
    terrain[gridSize * y + gridSize - 1] = terrain[gridSize * y + gridSize - 2];
  }

  return terrain;
}

function dtypeOf(arr: DigestArray): Digest["dtype"] {
  if (arr instanceof Float32Array) return "float32";
  if (arr instanceof Uint16Array) return "uint16";
  return "uint32";
}

// Summarize a typed array by its dtype, length, and the SHA-256 of its
// little-endian bytes
function digest(arr: DigestArray): Digest {
  const bytes = new Uint8Array(arr.buffer, arr.byteOffset, arr.byteLength);
  return {
    dtype: dtypeOf(arr),
    length: arr.length,
    sha256: createHash("sha256").update(bytes).digest("hex"),
  };
}

function createTestData(name: string, encoding: Encoding): TileDigests {
  const png = PNG.sync.read(readFileSync(join(DATA_DIR, `${name}.png`)));
  const terrain = terrainToGrid(png, encoding);

  // Digest the constructor output before getMesh, which writes to
  // martini.indices
  const martini = new Martini(png.width + 1);
  const martiniIndices = digest(martini.indices);
  const martiniCoords = digest(martini.coords);

  const tile = martini.createTile(terrain);
  const meshes = Object.fromEntries(
    MAX_ERRORS.map((maxError) => {
      const { vertices, triangles } = tile.getMesh(maxError);
      return [
        maxError,
        { vertices: digest(vertices), triangles: digest(triangles) },
      ];
    }),
  );

  return {
    terrain: digest(terrain),
    martini_indices: martiniIndices,
    martini_coords: martiniCoords,
    errors: digest(tile.errors),
    meshes,
  };
}

const output = Object.fromEntries(
  Object.entries(TILES).map(([name, encoding]) => [
    name,
    createTestData(name, encoding),
  ]),
);

writeFileSync(
  join(DATA_DIR, "martini_js.json"),
  `${JSON.stringify(output, null, 2)}\n`,
);
