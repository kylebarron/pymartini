import numpy as np
from ._martini_cy import martini


class Martini:
    def __init__(self, grid_size=257):
        resp = martini(grid_size)
        self.grid_size, self.num_triangles, self.num_parent_triangles, self.indices, self.coords = resp

    def create_tile(self, terrain):
        return Tile(terrain, self)


class Tile:
    def __init__(self, terrain, martini):
        size = martini.grid_size

        if len(terrain) != (size * size):
            raise ValueError(
                f'Expected terrain data of length {size * size} ({size} x {size}), got {len(terrain)}.'
            )

        self.terrain = terrain
        self.martini = martini
        self.errors = np.zeros(len(terrain), dtype=np.float32)
        self.update()

    def update(self):
        num_triangles = self.martini.num_triangles
        num_parent_triangles = self.martini.num_parent_triangles
        coords = self.martini.coords
        size = self.martini.grid_size

        terrain = self.terrain
        errors = self.errors

        # iterate over all possible triangles, starting from the smallest level
        # TODO: Make sure this range is correct
        for i in range(num_triangles - 1, -1, -1):
            k = i * 4
            ax = coords[k + 0]
            ay = coords[k + 1]
            bx = coords[k + 2]
            by = coords[k + 3]
            mx = (ax + bx) >> 1
            my = (ay + by) >> 1
            cx = mx + my - ay
            cy = my + ax - mx

            # calculate error in the middle of the long edge of the triangle
            interpolated_height = (
                terrain[ay * size + ax] + terrain[by * size + bx]) / 2
            middle_index = my * size + mx
            middle_error = abs(interpolated_height - terrain[middle_index])

            errors[middle_index] = max(errors[middle_index], middle_error)

            if i < num_parent_triangles:
                # bigger triangles; accumulate error with children
                left_child_index = ((ay + cy) >> 1) * size + ((ax + cx) >> 1)
                right_child_index = ((by + cy) >> 1) * size + ((bx + cx) >> 1)
                errors[middle_index] = max(
                    errors[middle_index], errors[left_child_index],
                    errors[right_child_index])

    def get_mesh(self, max_error=0):
        size = self.martini.grid_size
        indices = self.martini.indices
        errors = self.errors

        num_vertices = 0
        num_triangles = 0
        # max is a reserved keyword in Python
        _max = size - 1

        # use an index grid to keep track of vertices that were already used to
        # avoid duplication
        # I already initialized array with zeros
        # indices.fill(0)

        # retrieve mesh in two stages that both traverse the error map:
        # - countElements: find used vertices (and assign each an index), and count triangles (for minimum allocation)
        # - processTriangle: fill the allocated vertices & triangles typed arrays

        def countElements(ax, ay, bx, by, cx, cy, num_vertices, num_triangles):
            mx = (ax + bx) >> 1
            my = (ay + by) >> 1

            if (abs(ax - cx) + abs(ay - cy) > 1) and (errors[my * size + mx] >
                                                      max_error):
                num_vertices, num_triangles = countElements(
                    cx, cy, ax, ay, mx, my, num_vertices, num_triangles)
                num_vertices, num_triangles = countElements(
                    bx, by, cx, cy, mx, my, num_vertices, num_triangles)
            else:
                if not indices[ay * size + ax]:
                    num_vertices += 1
                    indices[ay * size + ax] = num_vertices
                if not indices[by * size + bx]:
                    num_vertices += 1
                    indices[by * size + bx] = num_vertices
                if not indices[cy * size + cx]:
                    num_vertices += 1
                    indices[cy * size + cx] = num_vertices

                num_triangles += 1

            return num_vertices, num_triangles

        num_vertices, num_triangles = countElements(
            0, 0, _max, _max, _max, 0, num_vertices, num_triangles)
        num_vertices, num_triangles = countElements(
            _max, _max, 0, 0, 0, _max, num_vertices, num_triangles)

        vertices = np.zeros(num_vertices * 2, dtype=np.uint16)
        triangles = np.zeros(num_triangles * 3, dtype=np.uint32)
        tri_index = 0

        def processTriangle(ax, ay, bx, by, cx, cy, tri_index):
            mx = (ax + bx) >> 1
            my = (ay + by) >> 1

            if (abs(ax - cx) + abs(ay - cy) > 1) and (errors[my * size + mx] >
                                                      max_error):
                # triangle doesn't approximate the surface well enough; drill down further
                tri_index = processTriangle(cx, cy, ax, ay, mx, my, tri_index)
                tri_index = processTriangle(bx, by, cx, cy, mx, my, tri_index)

            else:
                # add a triangle
                a = indices[ay * size + ax] - 1
                b = indices[by * size + bx] - 1
                c = indices[cy * size + cx] - 1

                vertices[2 * a] = ax
                vertices[2 * a + 1] = ay

                vertices[2 * b] = bx
                vertices[2 * b + 1] = by

                vertices[2 * c] = cx
                vertices[2 * c + 1] = cy

                triangles[tri_index] = a
                tri_index += 1
                triangles[tri_index] = b
                tri_index += 1
                triangles[tri_index] = c
                tri_index += 1

            return tri_index

        tri_index = processTriangle(0, 0, _max, _max, _max, 0, tri_index)
        tri_index = processTriangle(_max, _max, 0, 0, 0, _max, tri_index)

        return vertices, triangles
