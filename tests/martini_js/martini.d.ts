// @mapbox/martini doesn't ship type declarations; these cover what
// create_test_data.ts uses
declare module "@mapbox/martini" {
  export default class Martini {
    constructor(gridSize?: number);
    gridSize: number;
    numTriangles: number;
    numParentTriangles: number;
    indices: Uint32Array;
    coords: Uint16Array;
    createTile(terrain: Float32Array): Tile;
  }

  export class Tile {
    terrain: Float32Array;
    martini: Martini;
    errors: Float32Array;
    update(): void;
    getMesh(maxError?: number): {
      vertices: Uint16Array;
      triangles: Uint32Array;
    };
  }
}
