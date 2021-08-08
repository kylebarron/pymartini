from typing import Any, Tuple

import numpy as np
from numpy.typing import NDArray

class Martini:
    grid_size: int
    max_num_triangles: int
    num_parent_triangles: int

    indices_view: Any
    coords_view: Any
    def __init__(self, grid_size: int = ...) -> None: ...
    def create_tile(self, terrain: NDArray[np.number]) -> 'Tile': ...

class Tile:
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
    def __init__(self, terrain: NDArray[np.number], martini: 'Martini') -> None: ...
    def update(self) -> None: ...
    def get_mesh(
        self, max_error: float = ...
    ) -> Tuple[NDArray[np.uint16], NDArray[np.uint32]]: ...
