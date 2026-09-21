import pygame
import sys

# Настройки окна
WIDTH, HEIGHT = 900, 650
TILE_WIDTH = 64
TILE_HEIGHT = 32

# Цвета
BG_COLOR = (30, 30, 40)
GRID_COLOR = (70, 70, 80)
LAND_COLOR = (45, 140, 45)
WATER_COLOR = (40, 80, 200)
VALID_MOVE_COLOR = (100, 200, 100) # Подсветка доступных клеток
UI_BG = (50, 50, 60)
TEXT_COLOR = (255, 255, 255)

# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Polytopia Turn Engine")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18)
font_large = pygame.font.SysFont("Arial", 24, bold=True)

# Карта мира (0 - вода, 1 - суша)
# map_data = [,
#  ,
#  ,
#  ,
#  ,
#  ,
# ]
map_data = [
    [0, 0, 1, 1, 1, 0, 0],
    [0, 1, 1, 1, 1, 1, 0],
    [1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1],
    [0, 1, 1, 1, 1, 1, 0],
    [0, 0, 1, 1, 1, 0, 0],
]


def to_isometric(grid_x, grid_y):
    iso_x = (grid_x - grid_y) * (TILE_WIDTH // 2) + WIDTH // 2 - 50
    iso_y = (grid_x + grid_y) * (TILE_HEIGHT // 2) + HEIGHT // 4
    return iso_x, iso_y

def from_isometric(screen_x, screen_y):
    cx = screen_x - (WIDTH // 2 - 50)
    cy = screen_y - HEIGHT // 4
    grid_x = int((cx / (TILE_WIDTH / 2) + cy / (TILE_HEIGHT / 2)) / 2)
    grid_y = int((cy / (TILE_HEIGHT / 2) - cx / (TILE_WIDTH / 2)) / 2)
    return grid_x, grid_y

class Unit:
    def __init__(self, x, y, owner):
        self.x = x
        self.y = y
        self.owner = owner  # Ссылка на игрока-владельца
        self.max_movement = 2
        self.movement_left = self.max_movement
        self.hp = 10

    def reset_turn(self):
        """Сбрасывается в начале хода владельца"""
        self.movement_left = self.max_movement

    def draw(self, surface):
        iso_x, iso_y = to_isometric(self.x, self.y)
        # Рисуем круг цвета игрока
        pygame.draw.circle(surface, self.owner.color, (iso_x, iso_y + TILE_HEIGHT // 2), 12)
        # Полоска здоровья или индикатор того, что юнит находился
        if self.movement_left == 0:
            pygame.draw.circle(surface, (100, 100, 100), (iso_x, iso_y + TILE_HEIGHT // 2), 4)

class Player:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.stars = 5  # Стартовая валюта Polytopia
        self.units = []

    def collect_income(self):
        self.stars += 2 # Базовый доход за ход

class TurnManager:
    def __init__(self, players):
        self.players = players
        self.current_player_idx = 0

    @property
    def current_player(self):
        return self.players[self.current_player_idx]

    def next_turn(self):
        """Переключает ход на следующего игрока"""
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        # Активируем юнитов нового игрока и даем монеты
        self.current_player.collect_income()
        for unit in self.current_player.units:
            unit.reset_turn()

# Создаем игроков и их стартовых юнитов
player1 = Player("Игрок 1 (Синий)", (50, 150, 255))
player2 = Player("Игрок 2 (Красный)", (255, 70, 70))

p1_unit = Unit(2, 2, player1)
p2_unit = Unit(4, 3, player2)

player1.units.append(p1_unit)
player2.units.append(p2_unit)

all_units = [p1_unit, p2_unit]
turn_manager = TurnManager([player1, player2])

# Кнопка "Конец хода" (UI)
end_turn_btn = pygame.Rect(WIDTH - 180, HEIGHT - 70, 150, 45)

# Состояние выбора юнита
selected_unit = None

def get_valid_moves(unit):
    """Вычисляет доступные клетки для движения методом Манхэттенского расстояния"""
    valid_moves = []
    if unit.movement_left <= 0:
        return valid_moves
        
    for r in range(len(map_data)):
        for c in range(len(map_data[0])):
            if map_data[r][c] == 1: # Только суша
                distance = abs(unit.x - c) + abs(unit.y - r)
                if 0 < distance <= unit.movement_left:
                    # Проверяем, нет ли там чужого юнита
                    occupied = any(u.x == c and u.y == r for u in all_units)
                    if not occupied:
                        valid_moves.append((c, r))
    return valid_moves

# Главный цикл
running = True
while running:
    screen.fill(BG_COLOR)
    mouse_pos = pygame.mouse.get_pos()
    
    # Обработка ввода
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # ЛКМ
                # 1. Проверяем клик по кнопке "Конец хода"
                if end_turn_btn.collidepoint(mouse_pos):
                    turn_manager.next_turn()
                    selected_unit = None
                    continue
                
                # 2. Клик по карте
                gx, gy = from_isometric(mouse_pos[0], mouse_pos[1])
                
                if 0 <= gy < len(map_data) and 0 <= gx < len(map_data[0]):
                    # Пытаемся выбрать юнита текущего игрока
                    clicked_unit = None
                    for u in turn_manager.current_player.units:
                        if u.x == gx and u.y == gy:
                            clicked_unit = u
                    
                    if clicked_unit:
                        selected_unit = clicked_unit
                    elif selected_unit and (gx, gy) in get_valid_moves(selected_unit):
                        # Перемещаем выбранного юнита
                        move_cost = abs(selected_unit.x - gx) + abs(selected_unit.y - gy)
                        selected_unit.x = gx
                        selected_unit.y = gy
                        selected_unit.movement_left -= move_cost
                        selected_unit = None # Сбрасываем выбор после хода
                    else:
                        selected_unit = None # Кликнули в пустоту

    # --- ОТРИСОВКА ---
    
    # Отрендерим клетки для подсветки хода
    valid_moves = get_valid_moves(selected_unit) if selected_unit else []

    # Отрисовка карты
    for row_idx, row in enumerate(map_data):
        for col_idx, tile_type in enumerate(row):
            iso_x, iso_y = to_isometric(col_idx, row_idx)
            
            # Подсвечиваем клетку, если туда можно сходить
            if (col_idx, row_idx) in valid_moves:
                color = VALID_MOVE_COLOR
            else:
                color = LAND_COLOR if tile_type == 1 else WATER_COLOR
                
            # Рисуем ромб
            points = [(iso_x, iso_y), (iso_x + TILE_WIDTH // 2, iso_y + TILE_HEIGHT // 2), 
                      (iso_x, iso_y + TILE_HEIGHT), (iso_x - TILE_WIDTH // 2, iso_y + TILE_HEIGHT // 2)]
            pygame.draw.polygon(screen, color, points)
            pygame.draw.polygon(screen, GRID_COLOR, points, 1)

    # Отрисовка всех юнитов
    for unit in all_units:
        unit.draw(screen)

    # --- ИНТЕРФЕЙС (UI) ---
    # Панель сверху
    pygame.draw.rect(screen, UI_BG, (0, 0, WIDTH, 50))
    current_p = turn_manager.current_player
    
    text_turn = font_large.render(f"Ход: {current_p.name}", True, current_p.color)
    text_stars = font.render(f"Звёзды: ⭐️ {current_p.stars}", True, TEXT_COLOR)
    screen.blit(text_turn, (20, 10))
    screen.blit(text_stars, (WIDTH - 150, 15))
    
    if selected_unit:
        text_unit = font.render(f"Юнит: Очки движения [{selected_unit.movement_left}/{selected_unit.max_movement}]", True, TEXT_COLOR)
        screen.blit(text_unit, (350, 15))

    # Кнопка окончания хода
    btn_color = (80, 180, 80) if not end_turn_btn.collidepoint(mouse_pos) else (100, 210, 100)
    pygame.draw.rect(screen, btn_color, end_turn_btn, border_radius=5)
    text_btn = font.render("Конец хода", True, (255, 255, 255))
    screen.blit(text_btn, (WIDTH - 155, HEIGHT - 58))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
