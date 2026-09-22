import pygame

# Настройки окна и сетки
WIDTH, HEIGHT = 900, 650
TILE_WIDTH = 64
TILE_HEIGHT = 32
MAP_SIZE = 12

# Цвета
BG_COLOR = (30, 30, 40)
GRID_COLOR = (70, 70, 80)
LAND_COLOR = (45, 140, 45)      # Зеленый — суша (1)
SHALLOW_COLOR = (70, 130, 180)  # Голубой — мелководье (2)
WATER_COLOR = (30, 50, 140)     # Темно-синий — глубокий океан (0)
VALID_MOVE_COLOR = (100, 200, 100)
UI_BG = (50, 50, 60)
TEXT_COLOR = (255, 255, 255)

# Стоимость построек и юнитов
PORT_COST = 5
UNIT_COST = 3
