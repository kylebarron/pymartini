# Changelog

## [0.3.2] - 2020-09-25

- Include *pyx files in package manifest

## [0.3.1] - 2020-06-20

- Remove `column_row` option of `rescale_positions`; when `False` it created
  incorrect meshes by using a transposed mesh for the mesh creation and height
  lookup steps. See #15.

## [0.3.0] - 2020-06-13

- Add `column_row` argument to `rescale_positions`, to use the right axes when
  looking up terrain values.
- Convert `rescale_positions` to python/numpy instead of cython, for ease of
  maintainability. This does make `rescale_positions` a tiny bit slower, but
  it's not a perceptible difference. Rescaling 7,000 vertices was 40 μs with the
  cython code and 190 μs with the python/numpy code.

## [0.2.3] - 2020-06-01

- Allow ndarray as input to `Martini.create_tile`

## [0.2.2] - 2020-06-01

- Allow `decode_ele` to take arrays of transposed shapes, and add an option to
  turn off backfilling

## [0.2.1] - 2020-06-01

- Test building wheels with Github actions

## [0.2.0] - 2020-05-28

- Convert Python code to Cython
- Add utilities to extract terrain from images and to rescale positions
- Add benchmarks
- Add tests, explain rounding errors between `pymartini` and Martini in README.

## [0.1.0] - 2020-05-26

- Initial release
