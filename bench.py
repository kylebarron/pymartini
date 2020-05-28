from time import time

from imageio import imread

from pymartini import Martini, mapbox_terrain_to_grid

path = './test/fuji.png'
fuji = imread(path)
terrain = mapbox_terrain_to_grid(fuji)

start = time()
martini = Martini(fuji.shape[0] + 1)
end = time()
print(f'init tileset: {(end - start) * 1000:.3f}ms')

start = time()
tile = martini.create_tile(terrain)
end = time()
print(f'create tile: {(end - start) * 1000:.3f}ms')

start = time()
vertices, triangles = tile.get_mesh(30)
end = time()
print(f'mesh (max_error=30): {(end - start) * 1000:.3f}ms')
print(f'vertices: {len(vertices) / 2}, triangles: {len(triangles) / 3}')
