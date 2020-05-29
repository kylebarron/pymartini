from time import time

from imageio import imread

from pymartini import Martini, decode_ele

path = './test/data/fuji.png'
fuji = imread(path)
terrain = decode_ele(fuji, 'mapbox')

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

all_meshes_start = time()
for i in range(21):
    start = time()
    tile.get_mesh(i)
    end = time()
    print(f'mesh {i}: {(end - start) * 1000:.3f}ms')

all_meshes_end = time()
print(f'20 meshes total: {(all_meshes_end - all_meshes_start) * 1000:.3f}ms')
