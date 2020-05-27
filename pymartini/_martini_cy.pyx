import numpy as np
cimport numpy as np


def martini(int grid_size):
    tile_size = grid_size - 1
    if tile_size & (tile_size - 1):
        raise ValueError(
            f'Expected grid size to be 2^n+1, got {grid_size}.')

    num_triangles = tile_size * tile_size * 2 - 2
    num_parent_triangles = num_triangles - tile_size * tile_size

    cdef np.ndarray[np.uint32_t, ndim=1] indices = np.zeros(grid_size * grid_size, dtype=np.uint32)

    # coordinates for all possible triangles in an RTIN tile
    cdef np.ndarray[np.uint16_t, ndim=1] coords = np.zeros(num_triangles * 4, dtype=np.uint16)

    # Py_ssize_t is the proper C type for Python array indices.
    cdef Py_ssize_t i, _id
    cdef unsigned short [:] coords_view = coords
    cdef int k
    cdef unsigned short ax, ay, bx, by, mx, my, cx, cy

    # get triangle coordinates from its index in an implicit binary tree
    for i in range(num_triangles):
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
        coords_view[k + 0] = ax
        coords_view[k + 1] = ay
        coords_view[k + 2] = bx
        coords_view[k + 3] = by

    return grid_size, num_triangles, num_parent_triangles, indices, coords


def tile_update(
    int num_triangles,
    int num_parent_triangles,
    np.ndarray[np.uint16_t, ndim=1] coords,
    int size,
    np.ndarray[np.float32_t, ndim=1] terrain,
    np.ndarray[np.float32_t, ndim=1] errors):

    cdef unsigned short [:] coords_view = coords
    cdef float [:] terrain_view = terrain
    cdef float [:] errors_view = errors

    # Py_ssize_t is the proper C type for Python array indices.
    cdef Py_ssize_t i
    cdef int k
    cdef unsigned short ax, ay, bx, by, mx, my, cx, cy

    # iterate over all possible triangles, starting from the smallest level
    for i in range(num_triangles - 1, -1, -1):
        k = i * 4
        ax = coords_view[k + 0]
        ay = coords_view[k + 1]
        bx = coords_view[k + 2]
        by = coords_view[k + 3]
        mx = (ax + bx) >> 1
        my = (ay + by) >> 1
        cx = mx + my - ay
        cy = my + ax - mx

        # calculate error in the middle of the long edge of the triangle
        interpolated_height = (
            terrain_view[ay * size + ax] + terrain_view[by * size + bx]) / 2
        middle_index = my * size + mx
        middle_error = abs(interpolated_height - terrain_view[middle_index])

        errors_view[middle_index] = max(errors_view[middle_index], middle_error)

        if i < num_parent_triangles:
            # bigger triangles; accumulate error with children
            left_child_index = ((ay + cy) >> 1) * size + ((ax + cx) >> 1)
            right_child_index = ((by + cy) >> 1) * size + ((bx + cx) >> 1)
            errors_view[middle_index] = max(
                errors_view[middle_index], errors_view[left_child_index],
                errors_view[right_child_index])

    return errors


def get_mesh(
      np.ndarray[np.float32_t, ndim=1] errors,
      np.ndarray[np.uint32_t, ndim=1] indices,
      unsigned short size,
      float max_error,
    ):

    cdef unsigned int num_vertices = 0
    cdef unsigned int num_triangles = 0
    # max is a reserved keyword in Python
    cdef unsigned short _max = size - 1

    # use an index grid to keep track of vertices that were already used to
    # avoid duplication
    # I already initialized array with zeros
    # indices.fill(0)

    # retrieve mesh in two stages that both traverse the error map:
    # - countElements: find used vertices (and assign each an index), and count triangles (for minimum allocation)
    # - processTriangle: fill the allocated vertices & triangles typed arrays

    num_vertices, num_triangles, errors, indices = countElements(
        0, 0, _max, _max, _max, 0, num_vertices, num_triangles, errors, indices, max_error, size)
    num_vertices, num_triangles, errors, indices = countElements(
        _max, _max, 0, 0, 0, _max, num_vertices, num_triangles, errors, indices, max_error, size)

    cdef np.ndarray[np.uint16_t, ndim=1] vertices = np.zeros(num_vertices * 2, dtype=np.uint16)
    cdef np.ndarray[np.uint32_t, ndim=1] triangles = np.zeros(num_triangles * 3, dtype=np.uint32)
    cdef unsigned int tri_index = 0

    triangles, vertices, tri_index = processTriangle(0, 0, _max, _max, _max, 0, tri_index, errors, indices, triangles, vertices, max_error, size)
    triangles, vertices, tri_index = processTriangle(_max, _max, 0, 0, 0, _max, tri_index, errors, indices, triangles, vertices, max_error, size)

    return vertices, triangles

def countElements(
    unsigned short ax,
    unsigned short ay,
    unsigned short bx,
    unsigned short by,
    unsigned short cx,
    unsigned short cy,
    unsigned int num_vertices,
    unsigned int num_triangles,
    np.ndarray[np.float32_t, ndim=1] errors,
    np.ndarray[np.uint32_t, ndim=1] indices,
    float max_error,
    unsigned int size):

    cdef unsigned short mx, my
    cdef float [:] errors_view = errors
    cdef unsigned int [:] indices_view = indices

    mx = (ax + bx) >> 1
    my = (ay + by) >> 1

    if (abs(ax - cx) + abs(ay - cy) > 1) and (errors_view[my * size + mx] >
                                              max_error):
        num_vertices, num_triangles, errors, indices = countElements(
            cx, cy, ax, ay, mx, my, num_vertices, num_triangles, errors, indices, max_error, size)
        num_vertices, num_triangles, errors, indices = countElements(
            bx, by, cx, cy, mx, my, num_vertices, num_triangles, errors, indices, max_error, size)
    else:
        if not indices_view[ay * size + ax]:
            num_vertices += 1
            indices_view[ay * size + ax] = num_vertices
        if not indices_view[by * size + bx]:
            num_vertices += 1
            indices_view[by * size + bx] = num_vertices
        if not indices_view[cy * size + cx]:
            num_vertices += 1
            indices_view[cy * size + cx] = num_vertices

        num_triangles += 1

    return num_vertices, num_triangles, errors, indices


def processTriangle(
    unsigned short ax,
    unsigned short ay,
    unsigned short bx,
    unsigned short by,
    unsigned short cx,
    unsigned short cy,
    unsigned int tri_index,
    np.ndarray[np.float32_t, ndim=1] errors,
    np.ndarray[np.uint32_t, ndim=1] indices,
    np.ndarray[np.uint32_t, ndim=1] triangles,
    np.ndarray[np.uint16_t, ndim=1] vertices,
    float max_error,
    unsigned int size
    ):

    cdef unsigned short mx, my
    cdef float [:] errors_view = errors
    cdef unsigned int [:] indices_view = indices
    cdef unsigned int [:] triangles_view = triangles
    cdef unsigned short [:] vertices_view = vertices

    mx = (ax + bx) >> 1
    my = (ay + by) >> 1

    if (abs(ax - cx) + abs(ay - cy) > 1) and (errors_view[my * size + mx] >
                                              max_error):
        # triangle doesn't approximate the surface well enough; drill down further
        triangles, vertices, tri_index = processTriangle(cx, cy, ax, ay, mx, my, tri_index, errors, indices, triangles, vertices, max_error, size)
        triangles, vertices, tri_index = processTriangle(bx, by, cx, cy, mx, my, tri_index, errors, indices, triangles, vertices, max_error, size)

    else:
        # add a triangle
        a = indices_view[ay * size + ax] - 1
        b = indices_view[by * size + bx] - 1
        c = indices_view[cy * size + cx] - 1

        vertices_view[2 * a] = ax
        vertices_view[2 * a + 1] = ay

        vertices_view[2 * b] = bx
        vertices_view[2 * b + 1] = by

        vertices_view[2 * c] = cx
        vertices_view[2 * c + 1] = cy

        triangles_view[tri_index] = a
        tri_index += 1
        triangles_view[tri_index] = b
        tri_index += 1
        triangles_view[tri_index] = c
        tri_index += 1

    return triangles, vertices, tri_index
