from typing import Any

import numpy as np
from numpy.typing import NDArray

class Martini:
    """RTIN (right-triangulated irregular network) mesh generator.

    Precomputes the coordinates of every possible triangle in a grid of a given
    size. This is the slowest of the three steps, so if you're creating many
    meshes of the same size, create one `Martini` instance and create many
    tiles from it.
    """

    grid_size: int
    max_num_triangles: int
    num_parent_triangles: int

    indices_view: Any
    coords_view: Any
    def __init__(self, grid_size: int = 257) -> None:
        """Set up a mesh generator for a grid size.

        Args:
            grid_size: The grid size to use when generating the mesh. Must be
                2^k+1. If your source heightmap is 256x256 pixels, use
                `grid_size=257` and backfill the border pixels.

        Raises:
            ValueError: If `grid_size` is not 2^k+1.

        """

    def create_tile(self, terrain: NDArray[np.number]) -> Tile:
        """Generate the RTIN hierarchy from terrain data.

        This is faster than creating the `Martini` instance, but slower than
        creating a mesh for a given max error. If you need to create many
        meshes with different errors for the same terrain, reuse the
        returned `Tile`.

        Args:
            terrain: Heightmap of dtype `float32`. Either flattened, of shape
                (grid_size * grid_size), or two-dimensional, of shape
                (grid_size, grid_size), such as the output of
                [`decode_ele`][pymartini.decode_ele]. A 2D array is flattened
                in row-major (C) order, so vertex `(x, y)` of the output mesh
                is at `terrain[y, x]`.

        Returns:
            A tile on which you can call [`get_mesh`][pymartini.martini.Tile.get_mesh].

        Raises:
            ValueError: If `terrain` doesn't have grid_size * grid_size
                elements or isn't of dtype `float32`.

        """

class Tile:
    """The RTIN hierarchy of a heightmap, from which meshes are created.

    Create a tile with [`Martini.create_tile`][pymartini.Martini.create_tile].
    """

    grid_size: int
    max_num_triangles: int
    num_parent_triangles: int

    indices_view: Any
    coords_view: Any
    terrain_view: Any
    errors_view: Any

    num_vertices: int
    num_triangles: int
    max_error: float
    tri_index: int
    vertices_view: Any
    triangles_view: Any
    def __init__(self, terrain: NDArray[np.number], martini: Martini) -> None:
        """Generate the RTIN hierarchy from terrain data.

        Prefer [`Martini.create_tile`][pymartini.Martini.create_tile], which
        takes the same `terrain` argument.

        Args:
            terrain: Heightmap of dtype `float32`, of shape
                (grid_size * grid_size) or (grid_size, grid_size).
            martini: The mesh generator for this grid size.

        """

    def update(self) -> None:
        """Compute the error of every triangle in the hierarchy.

        This is called when the tile is created.
        """

    def get_mesh(
        self, max_error: float = 0
    ) -> tuple[NDArray[np.uint16], NDArray[np.uint32]]:
        """Get a mesh for a given max error.

        Args:
            max_error: The maximum vertical error for each triangle in the
                output mesh. For example if the units of the input heightmap
                are meters, using `max_error=5` means that the mesh is refined
                until every triangle approximates the surface of the heightmap
                within 5 meters.

        Returns:
            A tuple of `(vertices, triangles)`, each a flat array.
                `vertices` holds the interleaved 2D coordinates of each vertex,
                e.g. `[x0, y0, x1, y1, ...]`. To get 3D coordinates, use
                [`rescale_positions`][pymartini.rescale_positions].
                `triangles` holds indices of vertices, three per triangle. So
                `[0, 1, 3, ...]` uses the first, second, and fourth vertices
                as a single triangle.

        """
