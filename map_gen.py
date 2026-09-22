import random
from config import MAP_SIZE

def generate_map(size=MAP_SIZE):
    """Генерирует случайную карту: острова (1) посреди океана (0)"""
    grid = [[1 if random.random() < 0.45 else 0 for _ in range(size)] for _ in range(size)]
    
    for _ in range(2):
        new_grid = [[0] * size for _ in range(size)]
        for r in range(size):
            for c in range(size):
                neighbors = 0
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if 0 <= r + dr < size and 0 <= c + dc < size:
                            neighbors += grid[r + dr][c + dc]
                
                if neighbors > 4:
                    new_grid[r][c] = 1
                else:
                    new_grid[r][c] = 0
        grid = new_grid
        
    for i in range(size):
        grid[i][0] = grid[size-1][i] = grid[i][0] = grid[i][size-1] = 0
        
    return grid
