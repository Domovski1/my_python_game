import pygame
import sys
import random

# Настройки окна
WIDTH, HEIGHT = 900, 650
TILE_WIDTH = 64
TILE_HEIGHT = 32
MAP_SIZE = 12

# Цвета
BG_COLOR = (30, 30, 40)
GRID_COLOR = (70, 70, 80)
LAND_COLOR = (45, 140, 45)
WATER_COLOR = (40, 80, 200)
VALID_MOVE_COLOR = (100, 200, 100)
UI_BG = (50, 50, 60)
TEXT_COLOR = (255, 255, 255)

# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Polytopia Combat Engine")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 16)
font_large = pygame.font.SysFont("Arial", 22, bold=True)


def generate_map(size):
    """Генерирует случайную карту: острова (1) посреди океана (0)"""
    # Шаг 1: Заполняем сетку случайным шумом (45% суши, 55% воды)
    grid = [[1 if random.random() < 0.45 else 0 for _ in range(size)] for _ in range(size)]
    
    # Шаг 2: Сглаживаем карту (Клеточный автомат), чтобы получились цельные острова
    for _ in range(2): # 2 прохода сглаживания
        new_grid = [[0] * size for _ in range(size)]  # <--- ИСПРАВЛЕНО ТУТ
        for r in range(size):
            for c in range(size):
                # Считаем живых соседей вокруг клетки
                neighbors = 0
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if 0 <= r + dr < size and 0 <= c + dc < size:
                            neighbors += grid[r + dr][c + dc]
                
                # Если рядом много суши — клетка становится сушей, иначе водой
                if neighbors > 4:
                    new_grid[r][c] = 1
                else:
                    new_grid[r][c] = 0
        grid = new_grid
        
    # Гарантируем, что края карты будут водой (эффект океана вокруг острова)
    for i in range(size):
        grid[0][i] = grid[size-1][i] = grid[i][0] = grid[i][size-1] = 0
        
    return grid





# Двумерный массив карты
map_data = generate_map(MAP_SIZE)
# map_data = [
#     [0, 0, 1, 1, 1, 0, 0],
#     [0, 1, 1, 1, 1, 1, 0],
#     [1, 1, 1, 1, 1, 1, 1],
#     [1, 1, 1, 1, 1, 1, 1],
#     [0, 1, 1, 1, 1, 1, 0],
#     [0, 0, 1, 1, 1, 0, 0],
# ]


# Автоматически находим безопасные места на суше для спавна юнитов
land_tiles = [(c, r) for r in range(MAP_SIZE) for c in range(MAP_SIZE) if map_data[r][c] == 1]

# Если суши сгенерировалось слишком мало, подстрахуемся
if len(land_tiles) < 2:
    map_data = [[1 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
    land_tiles = [(c, r) for r in range(MAP_SIZE) for c in range(MAP_SIZE)]

p1_spawn = random.choice(land_tiles)
p2_spawn = random.choice(land_tiles)
while p1_spawn == p2_spawn: # Чтобы не спавнились в одной клетке
    p2_spawn = random.choice(land_tiles)


def to_isometric(grid_x, grid_y):
    """Преобразует координаты сетки в ЦЕЛЫЕ экранные координаты пикселей"""
    iso_x = (grid_x - grid_y) * (TILE_WIDTH // 2) + (WIDTH // 2)
    iso_y = (grid_x + grid_y) * (TILE_HEIGHT // 2) + (HEIGHT // 4)
    return int(iso_x), int(iso_y)

def from_isometric(screen_x, screen_y):
    """Преобразует координаты мыши обратно в сетку"""
    cx = screen_x - (WIDTH // 2)
    cy = screen_y - (HEIGHT // 4)
    grid_x = int((cx / (TILE_WIDTH / 2) + cy / (TILE_HEIGHT / 2)) / 2)
    grid_y = int((cy / (TILE_HEIGHT / 2) - cx / (TILE_WIDTH / 2)) / 2)
    return grid_x, grid_y

class Unit:
    def __init__(self, x, y, owner):
        self.x = x
        self.y = y
        self.owner = owner
        self.max_movement = 2
        self.movement_left = self.max_movement
        
        self.max_hp = 10
        self.hp = 10
        self.atk = 3
        self.def_power = 2
        self.has_attacked = False

    def reset_turn(self):
        self.movement_left = self.max_movement
        self.has_attacked = False

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp < 0:
            self.hp = 0

    def draw(self, surface):
        iso_x, iso_y = to_isometric(self.x, self.y)
        center_x = iso_x
        center_y = iso_y + TILE_HEIGHT // 2
        
        # Тело юнита
        pygame.draw.circle(surface, self.owner.color, (center_x, center_y), 12)
        
        # Индикатор конца действий
        if self.movement_left == 0 and self.has_attacked:
            pygame.draw.circle(surface, (100, 100, 100), (center_x, center_y), 4)

        # Здоровье
        if self.hp < self.max_hp:
            bar_width = 24
            bar_height = 4
            bx = center_x - bar_width // 2
            by = center_y - 22
            pygame.draw.rect(surface, (200, 50, 50), (bx, by, bar_width, bar_height))
            current_bar_width = int(bar_width * (self.hp / self.max_hp))
            pygame.draw.rect(surface, (50, 200, 50), (bx, by, current_bar_width, bar_height))


class Player:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.stars = 5
        self.units = []
        # Сетка тумана войны: 0 - скрыто, 1 - видно. Изначально всё скрыто (0)
        self.fog = [[0 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]

    def collect_income(self):
        self.stars += 2

    def update_fog(self):
        """Открывает клетки вокруг юнитов игрока (радиус 1 клетка)"""
        # Сначала делаем видимыми клетки, где стоят наши юниты и их соседей
        for unit in self.units:
            if unit.hp > 0:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        r = unit.y + dr
                        c = unit.x + dc
                        if 0 <= r < MAP_SIZE and 0 <= c < MAP_SIZE:
                            self.fog[r][c] = 1


class TurnManager:
    def __init__(self, players):
        self.players = players
        self.current_player_idx = 0

    @property
    def current_player(self):
        return self.players[self.current_player_idx]

    def next_turn(self):
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        self.current_player.collect_income()
        for unit in self.current_player.units:
            unit.reset_turn()
        self.current_player.update_fog() # <--- ДОБАВИТЬ ЭТУ СТРОКУ

# Инициализация игроков и их юнитов на случайной суше
player1 = Player("Игрок 1 (Синий)", (50, 150, 255))
player2 = Player("Игрок 2 (Красный)", (255, 70, 70))

p1_unit = Unit(p1_spawn[0], p1_spawn[1], player1)
p2_unit = Unit(p2_spawn[0], p2_spawn[1], player2)

player1.units.append(p1_unit)
player2.units.append(p2_unit)

all_units = [p1_unit, p2_unit]
turn_manager = TurnManager([player1, player2])


end_turn_btn = pygame.Rect(WIDTH - 180, HEIGHT - 70, 150, 45)
selected_unit = None
combat_log = "Нажмите на юнита, чтобы выбрать его."

def get_valid_moves(unit):
    valid_moves = []
    if not unit or unit.movement_left <= 0:
        return valid_moves
    for r in range(len(map_data)):
        for c in range(len(map_data)):
            if map_data[r][c] == 1:
                distance = abs(unit.x - c) + abs(unit.y - r)
                if 0 < distance <= unit.movement_left:
                    if not any(u.x == c and u.y == r for u in all_units):
                        valid_moves.append((c, r))
    return valid_moves

def get_attackable_targets(unit):
    targets = []
    if not unit or unit.has_attacked:
        return targets
    for u in all_units:
        if u.owner != unit.owner and u.hp > 0:
            distance = abs(unit.x - u.x) + abs(unit.y - u.y)
            if distance == 1:
                targets.append(u)
    return targets

player1.update_fog()
player2.update_fog()


# Главный цикл
running = True
while running:
    screen.fill(BG_COLOR)
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get(): # <--- Здесь исправлено pygame.event.get()
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if end_turn_btn.collidepoint(mouse_pos):
                    turn_manager.next_turn()
                    selected_unit = None
                    combat_log = "Ход передан."
                    continue
                
                # ИСПРАВЛЕНО: Передаем координаты мыши раздельно (X и Y)
                gx, gy = from_isometric(mouse_pos[0], mouse_pos[1])
                
                if 0 <= gy < len(map_data) and 0 <= gx < len(map_data):
                    clicked_unit = None
                    for u in all_units:
                        if u.x == gx and u.y == gy and u.hp > 0:
                            clicked_unit = u
                    
                    if clicked_unit and clicked_unit.owner == turn_manager.current_player:
                        selected_unit = clicked_unit
                        combat_log = f"Выбран юнит {clicked_unit.owner.name}."
                    
                    elif selected_unit and clicked_unit and clicked_unit in get_attackable_targets(selected_unit):
                        attacker = selected_unit
                        defender = clicked_unit
                        
                        atk_force = attacker.atk * (attacker.hp / attacker.max_hp)
                        def_force = defender.def_power * (defender.hp / defender.max_hp)
                        total_force = atk_force + def_force if (atk_force + def_force) > 0 else 1
                        
                        damage_to_def = round((atk_force / total_force) * attacker.atk * 1.5)
                        defender.take_damage(damage_to_def)
                        log_msg = f"Атака! Нанесено {damage_to_def} урона. "
                        
                        if defender.hp > 0:
                            damage_to_atk = round((def_force / total_force) * defender.def_power * 1.5)
                            attacker.take_damage(damage_to_atk)
                            log_msg += f"Ответный удар: получено {damage_to_atk} урона."
                        else:
                            log_msg += "Враг уничтожен!"
                            if defender in all_units:
                                all_units.remove(defender)
                            if defender in defender.owner.units:
                                defender.owner.units.remove(defender)
                        
                        attacker.has_attacked = True
                        attacker.movement_left = 0
                        selected_unit = None
                        turn_manager.current_player.update_fog() # <--- ДОБАВИТЬ СЮДА, чтобы туман открывался на ходу
                        combat_log = log_msg
                        
                    elif selected_unit and (gx, gy) in get_valid_moves(selected_unit):
                        move_cost = abs(selected_unit.x - gx) + abs(selected_unit.y - gy)
                        selected_unit.x = gx
                        selected_unit.y = gy
                        selected_unit.movement_left -= move_cost
                        combat_log = "Юнит переместился."
                        selected_unit = None
                    else:
                        selected_unit = None

    # --- ОТРИСОВКА КАРТЫ С ТУМАНОМ ---
    valid_moves = get_valid_moves(selected_unit) if selected_unit else []
    attack_targets = get_attackable_targets(selected_unit) if selected_unit else []
    attack_coords = [(t.x, t.y) for t in attack_targets]
    
    current_fog = turn_manager.current_player.fog

    for row_idx, row in enumerate(map_data):
        for col_idx, tile_type in enumerate(row):
            iso_x, iso_y = to_isometric(col_idx, row_idx)
            
            # Если клетка скрыта туманом войны для текущего игрока
            if current_fog[row_idx][col_idx] == 0:
                color = (20, 20, 25) # Почти черный цвет тумана
            else:
                # Если клетка видна, красим её как обычно
                if (col_idx, row_idx) in attack_coords:
                    color = (230, 80, 80)
                elif (col_idx, row_idx) in valid_moves:
                    color = VALID_MOVE_COLOR
                else:
                    color = LAND_COLOR if tile_type == 1 else WATER_COLOR
                
            points = [
                (iso_x, iso_y), 
                (iso_x + TILE_WIDTH // 2, iso_y + TILE_HEIGHT // 2), 
                (iso_x, iso_y + TILE_HEIGHT), 
                (iso_x - TILE_WIDTH // 2, iso_y + TILE_HEIGHT // 2)
            ]
            pygame.draw.polygon(screen, color, points)
            # Рисуем сетку только для видимых клеток
            if current_fog[row_idx][col_idx] == 1:
                pygame.draw.polygon(screen, GRID_COLOR, points, 1)

    # Отрисовка юнитов (рисуем только тех, кто стоит на видимых клетках)
    for unit in all_units:
        if unit.hp > 0 and current_fog[unit.y][unit.x] == 1:
            unit.draw(screen)


    # --- ИНТЕРФЕЙС (UI) ---
    pygame.draw.rect(screen, UI_BG, (0, 0, WIDTH, 50))
    current_p = turn_manager.current_player
    
    text_turn = font_large.render(f"Ход: {current_p.name}", True, current_p.color)
    screen.blit(text_turn, (20, 12))
    
    pygame.draw.rect(screen, UI_BG, (0, HEIGHT - 50, WIDTH - 200, 50))
    text_log = font.render(f"События: {combat_log}", True, TEXT_COLOR)
    screen.blit(text_log, (20, HEIGHT - 33))

    btn_color = (80, 180, 80) if not end_turn_btn.collidepoint(mouse_pos) else (100, 210, 100)
    pygame.draw.rect(screen, btn_color, end_turn_btn, border_radius=5)
    text_btn = font_large.render("Конец хода", True, (255, 255, 255))
    screen.blit(text_btn, (WIDTH - 158, HEIGHT - 58))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
