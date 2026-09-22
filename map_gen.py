import random
from config import MAP_SIZE

def generate_map(size=MAP_SIZE):
    """Генерирует карту с островами (1), мелководьем (2) и глубоким океаном (0)"""
    # Шаг 1: Базовый шум
    grid = [[1 if random.random() < 0.42 else 0 for _ in range(size)] for _ in range(size)]
    
    # Шаг 2: Сглаживание клеточным автоматом
    for _ in range(2):
        new_grid = [[0] * size for _ in range(size)]
        for r in range(size):
            for c in range(size):
                neighbors = 0
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if 0 <= r + dr < size and 0 <= c + dc < size:
                            neighbors += 1 if grid[r + dr][c + dc] == 1 else 0
                if neighbors > 4:
                    new_grid[r][c] = 1
        grid = new_grid
        
    # Шаг 3: Генерируем мелководье (тип 2) вокруг всей суши
    final_grid = [[0] * size for _ in range(size)]
    for r in range(size):
        for c in range(size):
            if grid[r][c] == 1:
                final_grid[r][c] = 1 # Суша
            else:
                # Проверяем, есть ли рядом суша
                has_land_nearby = False
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if 0 <= r + dr < size and 0 <= c + dc < size:
                            if grid[r + dr][c + dc] == 1:
                                has_land_nearby = True
                if has_land_nearby:
                    final_grid[r][c] = 2 # Мелководье (берег)
                    
    # Океан по краям
    for i in range(size):
        final_grid[0][i] = final_grid[size-1][i] = final_grid[i][0] = final_grid[i][size-1] = 0
        
    return final_grid
