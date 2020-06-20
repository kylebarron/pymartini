import numpy as np
cimport numpy as np


cdef class Martini:
    # Define class attributes
    cdef readonly unsigned short grid_size
    cdef readonly unsigned int max_num_triangles
    cdef readonly unsigned int num_parent_triangles

    # Can't store Numpy arrays as class attributes, but you _can_ store the
    # associated memoryviews
    # https://stackoverflow.com/a/23840186
    cdef readonly np.uint32_t[:] indices_view
    cdef readonly np.uint16_t[:] coords_view

    def __init__(self, int grid_size=257):
        self.grid_size = grid_size
        tile_size = grid_size - 1
        if tile_size & (tile_size - 1):
            raise ValueError(
                f'Expected grid size to be 2^n+1, got {grid_size}.')

        self.max_num_triangles = tile_size * tile_size * 2 - 2
        self.num_parent_triangles = self.max_num_triangles - tile_size * tile_size

        self.indices_view = np.zeros(grid_size * grid_size, dtype=np.uint32)

        # coordinates for all possible triangles in an RTIN tile
        self.coords_view = np.zeros(self.max_num_triangles * 4, dtype=np.uint16)

        # Py_ssize_t is the proper C type for Python array indices.
        cdef Py_ssize_t i, _id
        cdef int k
        cdef unsigned short ax, ay, bx, by, mx, my, cx, cy

        # get triangle coordinates from its index in an implicit binary tree
        for i in range(self.max_num_triangles):
            # id is a reserved name in Python
            _id = i + 2

            ax = ay = bx = by = cx = cy = 0
            if _id & 1:
                # bottom-left triangle
                bx = by = cx = tile_size
            else:
                # top-right triangle
                ax = ay = cy = tile_size

            while (_id >> 1) > 1:
                # Since Python doesn't have a >>= operator
                _id = _id >> 1

                mx = (ax + bx) >> 1
                my = (ay + by) >> 1

                if _id & 1:
                    # Left half
                    bx, by = ax, ay
                    ax, ay = cx, cy
                else:
                    # Right half
                    ax, ay = bx, by
                    bx, by = cx, cy

                cx, cy = mx, my

            k = i * 4
            self.coords_view[k + 0] = ax
            self.coords_view[k + 1] = ay
            self.coords_view[k + 2] = bx
            self.coords_view[k + 3] = by

    def create_tile(self, terrain):
        return Tile(terrain, self)


cdef class Tile:
    # Define class attributes
    cdef readonly unsigned short grid_size
    cdef readonly unsigned int max_num_triangles
    cdef readonly unsigned int num_parent_triangles

    # Can't store Numpy arrays as class attributes, but you _can_ store the
    # associated memoryviews
    # https://stackoverflow.com/a/23840186
    cdef readonly np.uint32_t[:] indices_view
    cdef readonly np.uint16_t[:] coords_view

    cdef readonly np.float32_t[:] terrain_view
    cdef readonly np.float32_t[:] errors_view

    # "globals" Used in getMesh
    cdef readonly unsigned int num_vertices
    cdef readonly unsigned int num_triangles
    cdef readonly float max_error
    cdef readonly unsigned int tri_index
    cdef readonly np.uint16_t[:] vertices_view
    cdef readonly np.uint32_t[:] triangles_view

    def __init__(self, terrain, martini):
        size = martini.grid_size

        # Allow ndarray as input
        if len(terrain.shape) > 1:
            terrain = terrain.flatten('C')

        if len(terrain) != (size * size):
            raise ValueError(
                f'Expected terrain data of length {size * size} ({size} x {size}), got {len(terrain)}.'
            )

        self.terrain_view = terrain
        self.errors_view = np.zeros(len(terrain), dtype=np.float32)

        # Expand Martini instance, since I can't cdef a class
        self.grid_size = martini.grid_size
        self.max_num_triangles = martini.max_num_triangles
        self.num_parent_triangles = martini.num_parent_triangles
        self.indices_view = martini.indices_view
        self.coords_view = martini.coords_view

        self.update()

    def update(self):
        cdef unsigned short size
        size = self.grid_size

        # Py_ssize_t is the proper C type for Python array indices.
        cdef Py_ssize_t i
        cdef unsigned short ax, ay, bx, by, mx, my, cx, cy
        cdef unsigned int k
        cdef float interpolated_height, middle_error
        cdef unsigned int middle_index, left_child_index, right_child_index

        # iterate over all possible triangles, starting from the smallest level
        for i in range(self.max_num_triangles - 1, -1, -1):
            k = i * 4
            ax = self.coords_view[k + 0]
            ay = self.coords_view[k + 1]
            bx = self.coords_view[k + 2]
            by = self.coords_view[k + 3]
            mx = (ax + bx) >> 1
            my = (ay + by) >> 1
            cx = mx + my - ay
            cy = my + ax - mx

            # calculate error in the middle of the long edge of the triangle
            interpolated_height = (
                self.terrain_view[ay * size + ax] + self.terrain_view[by * size + bx]) / 2
            middle_index = my * size + mx
            middle_error = abs(interpolated_height - self.terrain_view[middle_index])

            self.errors_view[middle_index] = max(self.errors_view[middle_index], middle_error)

            if i < self.num_parent_triangles:
                # bigger triangles; accumulate error with children
                left_child_index = ((ay + cy) >> 1) * size + ((ax + cx) >> 1)
                right_child_index = ((by + cy) >> 1) * size + ((bx + cx) >> 1)
                self.errors_view[middle_index] = max(
                    self.errors_view[middle_index], self.errors_view[left_child_index],
                    self.errors_view[right_child_index])

    def get_mesh(self, float max_error=0):
        cdef unsigned short size
        size = self.grid_size

        # Initialize to zero on each iteration
        self.num_vertices = 0
        self.num_triangles = 0
        self.max_error = max_error

        # max is a reserved keyword in Python
        cdef unsigned short _max = size - 1

        # use an index grid to keep track of vertices that were already used to
        # avoid duplication
        # While indices was initialized with zeros, filling with 0 again
        # essentially removes any state from the previous time get_mesh was run,
        # so it can be run many times from the class
        indices = np.asarray(self.indices_view, dtype=np.uint32)
        indices.fill(0)
        self.indices_view = indices

        # retrieve mesh in two stages that both traverse the error map:
        # - countElements: find used vertices (and assign each an index), and count triangles (for minimum allocation)
        # - processTriangle: fill the allocated vertices & triangles typed arrays

        self.countElements(0, 0, _max, _max, _max, 0)
        self.countElements(_max, _max, 0, 0, 0, _max)

        self.vertices_view = np.zeros(self.num_vertices * 2, dtype=np.uint16)
        self.triangles_view = np.zeros(self.num_triangles * 3, dtype=np.uint32)
        self.tri_index = 0

        self.processTriangle(0, 0, _max, _max, _max, 0)
        self.processTriangle(_max, _max, 0, 0, 0, _max)

        vertices = np.asarray(self.vertices_view, dtype=np.uint16)
        triangles = np.asarray(self.triangles_view, dtype=np.uint32)

        return vertices, triangles

    cdef countElements(
        self,
        unsigned short ax,
        unsigned short ay,
        unsigned short bx,
        unsigned short by,
        unsigned short cx,
        unsigned short cy):

        cdef unsigned short size
        size = self.grid_size

        cdef unsigned short mx, my

        mx = (ax + bx) >> 1
        my = (ay + by) >> 1

        if (abs(ax - cx) + abs(ay - cy) > 1) and (self.errors_view[my * size + mx] > self.max_error):
            self.countElements(cx, cy, ax, ay, mx, my)
            self.countElements(bx, by, cx, cy, mx, my)
        else:
            if not self.indices_view[ay * size + ax]:
                self.num_vertices += 1
                self.indices_view[ay * size + ax] = self.num_vertices
            if not self.indices_view[by * size + bx]:
                self.num_vertices += 1
                self.indices_view[by * size + bx] = self.num_vertices
            if not self.indices_view[cy * size + cx]:
                self.num_vertices += 1
                self.indices_view[cy * size + cx] = self.num_vertices

            self.num_triangles += 1

    cdef processTriangle(
        self,
        unsigned short ax,
        unsigned short ay,
        unsigned short bx,
        unsigned short by,
        unsigned short cx,
        unsigned short cy,
        ):

        cdef unsigned short size
        size = self.grid_size

        cdef unsigned short mx, my
        cdef unsigned int a, b, c

        mx = (ax + bx) >> 1
        my = (ay + by) >> 1

        if (abs(ax - cx) + abs(ay - cy) > 1) and (self.errors_view[my * size + mx] > self.max_error):
            # triangle doesn't approximate the surface well enough; drill down further
            self.processTriangle(cx, cy, ax, ay, mx, my)
            self.processTriangle(bx, by, cx, cy, mx, my)

        else:
            # add a triangle
            a = self.indices_view[ay * size + ax] - 1
            b = self.indices_view[by * size + bx] - 1
            c = self.indices_view[cy * size + cx] - 1

            self.vertices_view[2 * a] = ax
            self.vertices_view[2 * a + 1] = ay

            self.vertices_view[2 * b] = bx
            self.vertices_view[2 * b + 1] = by

            self.vertices_view[2 * c] = cx
            self.vertices_view[2 * c + 1] = cy

            self.triangles_view[self.tri_index] = a
            self.tri_index += 1
            self.triangles_view[self.tri_index] = b
            self.tri_index += 1
            self.triangles_view[self.tri_index] = c
            self.tri_index += 1
