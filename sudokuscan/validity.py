import numpy as np


def check_validity(grid):
    grid = np.asarray(grid)
    if grid.shape != (9, 9) or not np.isin(grid, np.arange(10)).all():
        raise ValueError("Grid must be 9x9 with entries in 0..9")
    units = [[(row, col) for col in range(9)] for row in range(9)]
    units += [[(row, col) for row in range(9)] for col in range(9)]
    units += [[(row, col) for row in range(top, top + 3) for col in range(left, left + 3)]
              for top in (0, 3, 6) for left in (0, 3, 6)]
    conflicts = set()
    for unit in units:
        for digit in range(1, 10):
            positions = [(row, col) for row, col in unit if grid[row, col] == digit]
            if len(positions) > 1:
                conflicts.update(positions)
    return ("invalid" if conflicts else "valid"), [list(cell) for cell in sorted(conflicts)]
