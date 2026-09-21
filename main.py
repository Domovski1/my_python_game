import pygame
import sys

# Настройки окна
WIDTH, HEIGHT = 800, 600
TILE_WIDTH = 64
TILE_HEIGHT = 32

# Цвета (R, G, B)
BG_COLOR = (30, 30, 40)
GRID_COLOR = (100, 100, 100)
LAND_COLOR = (34, 139, 34)   # Зеленый для суши
WATER_COLOR = (65, 105, 225) # Синий для воды
UNIT_COLOR = (255, 69, 0)    # Оранжевый для юнита

# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Polytopia Clone Prototype")
clock = pygame.time.Clock()

# Карта мира (0 - вода, 1 - суша)
map_data = [
    [0, 0, 1, 1, 1, 0, 0],
    [0, 1, 1, 1, 1, 1, 0],
    [1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1],
    [0, 1, 1, 1, 1, 1, 0],
    [0, 0, 1, 1, 1, 0, 0],
]

# Координаты юнита на сетке (X, Y)
unit_pos = [3, 3]

def to_isometric(grid_x, grid_y):
    """Преобразует координаты сетки в экранные изометрические координаты."""
    iso_x = (grid_x - grid_y) * (TILE_WIDTH // 2) + WIDTH // 2
    iso_y = (grid_x + grid_y) * (TILE_HEIGHT // 2) + HEIGHT // 4
    return iso_x, iso_y

def from_isometric(screen_x, screen_y):
    """Преобразует экранные координаты мыши обратно в координаты сетки."""
    # Смещение относительно центра отрисовки
    cx = screen_x - WIDTH // 2
    cy = screen_y - HEIGHT // 4
    
    grid_x = int((cx / (TILE_WIDTH / 2) + cy / (TILE_HEIGHT / 2)) / 2)
    grid_y = int((cy / (TILE_HEIGHT / 2) - cx / (TILE_WIDTH / 2)) / 2)
    return grid_x, grid_y

def draw_tile(surface, color, iso_x, iso_y):
    """Рисует один изометрический ромб."""
    points = [
        (iso_x, iso_y),                          # Верхняя точка
        (iso_x + TILE_WIDTH // 2, iso_y + TILE_HEIGHT // 2),  # Правая
        (iso_x, iso_y + TILE_HEIGHT),            # Нижняя
        (iso_x - TILE_WIDTH // 2, iso_y + TILE_HEIGHT // 2)   # Левая
    ]
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, GRID_COLOR, points, 1) # Граница

# Главный цикл игры
running = True
while running:
    screen.fill(BG_COLOR)
    
    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Левый клик мыши
                mx, my = pygame.mouse.get_pos()
                gx, gy = from_isometric(mx, my)
                
                # Проверяем, попал ли клик в границы карты
                if 0 <= gy < len(map_data) and 0 <= gx < len(map_data[0]):
                    if map_data[gy][gx] == 1: # Перемещаемся только по суше
                        unit_pos = [gx, gy]

    # Отрисовка карты
    for row_idx, row in enumerate(map_data):
        for col_idx, tile_type in enumerate(row):
            iso_x, iso_y = to_isometric(col_idx, row_idx)
            color = LAND_COLOR if tile_type == 1 else WATER_COLOR
            draw_tile(screen, color, iso_x, iso_y)

    # Отрисовка юнита
    u_iso_x, u_iso_y = to_isometric(unit_pos[0], unit_pos[1])
    # Рисуем круг в центре тайла, слегка приподнятый вверх
    pygame.draw.circle(screen, UNIT_COLOR, (u_iso_x, u_iso_y + TILE_HEIGHT // 2), 12)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
