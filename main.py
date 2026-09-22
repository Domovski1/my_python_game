import pygame
import sys
import random

# Импортируем наши модули
from config import *
from map_gen import generate_map
from entities import Unit, Player, TurnManager, City, to_isometric

def from_isometric(screen_x, screen_y):
    cx = screen_x - (WIDTH // 2)
    cy = screen_y - (HEIGHT // 4)
    grid_x = int((cx / (TILE_WIDTH / 2) + cy / (TILE_HEIGHT / 2)) / 2)
    grid_y = int((cy / (TILE_HEIGHT / 2) - cx / (TILE_WIDTH / 2)) / 2)
    return grid_x, grid_y

# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Polytopia Modular Cities Edition")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 16)
font_large = pygame.font.SysFont("Arial", 22, bold=True)

# Генерация мира
map_data = generate_map(MAP_SIZE)
land_tiles = [(c, r) for r in range(MAP_SIZE) for c in range(MAP_SIZE) if map_data[r][c] == 1]
if len(land_tiles) < 5: # Подстраховка
    map_data = [[1 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
    land_tiles = [(c, r) for r in range(MAP_SIZE) for c in range(MAP_SIZE)]

# Случайный выбор мест под города (выберем, например, 4 города)
random.shuffle(land_tiles)
cities_positions = land_tiles[:4]

all_cities = []
for pos in cities_positions:
    all_cities.append(City(pos[0], pos[1]))

# Стартовые спавны игроков делаем прямо в первых двух городах
p1_spawn = (all_cities[0].x, all_cities[0].y)
p2_spawn = (all_cities[1].x, all_cities[1].y)

# Создание игроков
player1 = Player("Игрок 1 (Синий)", (50, 150, 255))
player2 = Player("Игрок 2 (Красный)", (255, 70, 70))

# Привязываем стартовые города к игрокам
all_cities[0].owner = player1
player1.cities.append(all_cities[0])

all_cities[1].owner = player2
player2.cities.append(all_cities[1])

# Создаем стартовых юнитов в их городах
p1_unit = Unit(p1_spawn[0], p1_spawn[1], player1)
p2_unit = Unit(p2_spawn[0], p2_spawn[1], player2)

player1.units.append(p1_unit)
player2.units.append(p2_unit)

all_units = [p1_unit, p2_unit]
turn_manager = TurnManager([player1, player2])

player1.update_fog()
player2.update_fog()

end_turn_btn = pygame.Rect(WIDTH - 180, HEIGHT - 70, 150, 45)
selected_unit = None
combat_log = "Захватывайте нейтральные серые города, чтобы увеличить доход!"

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

def check_city_capture(player):
    """Проверяет, стоят ли юниты игрока на чужих/нейтральных городах для их захвата"""
    global combat_log
    for unit in player.units:
        if unit.hp > 0:
            for city in all_cities:
                if city.x == unit.x and city.y == unit.y and city.owner != player:
                    # Убираем город у старого владельца, если он был
                    if city.owner:
                        city.owner.cities.remove(city)
                    # Отдаем новому
                    city.owner = player
                    player.cities.append(city)
                    combat_log = f"{player.name} захватил город на ({city.x}, {city.y})!"

# Главный цикл
running = True
while running:
    screen.fill(BG_COLOR)
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

         # --- ДОБАВЛЯЕМ ОБРАБОТКУ НАЖАТИЯ КЛАВИШ ---
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE: # Если нажат Пробел
                # Выполняем те же действия, что и при клике на кнопку конца хода
                check_city_capture(turn_manager.current_player)
                turn_manager.next_turn()
                selected_unit = None
                combat_log = "Ход передан (Пробел)."
                continue

            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if end_turn_btn.collidepoint(mouse_pos):
                    check_city_capture(turn_manager.current_player)
                    turn_manager.next_turn()
                    selected_unit = None
                    continue
                
                gx, gy = from_isometric(mouse_pos[0], mouse_pos[1])
                
                if 0 <= gy < MAP_SIZE and 0 <= gx < MAP_SIZE:
                    current_player = turn_manager.current_player
                    
                    # 1. Проверяем, кликнули ли по живому юниту
                    clicked_unit = None
                    for u in all_units:
                        if u.x == gx and u.y == gy and u.hp > 0:
                            clicked_unit = u
                    
                    # 2. Проверяем, кликнули ли по городу текущего игрока
                    clicked_my_city = None
                    for city in all_cities:
                        if city.is_clicked(gx, gy) and city.owner == current_player:
                            clicked_my_city = city

                    # --- ЛОГИКА ДЕЙСТВИЙ ---
                    
                    # Выбор своего юнита
                    if clicked_unit and clicked_unit.owner == current_player:
                        selected_unit = clicked_unit
                        combat_log = f"Выбран юнит {clicked_unit.owner.name}."
                    
                    # АТАКА врага выбранным юнитом
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
                            if defender in all_units: all_units.remove(defender)
                            if defender in defender.owner.units: defender.owner.units.remove(defender)
                        
                        attacker.has_attacked = True
                        attacker.movement_left = 0
                        selected_unit = None
                        combat_log = log_msg
                        
                    # ДВИЖЕНИЕ на пустую клетку
                    elif selected_unit and (gx, gy) in get_valid_moves(selected_unit):
                        move_cost = abs(selected_unit.x - gx) + abs(selected_unit.y - gy)
                        selected_unit.x = gx
                        selected_unit.y = gy
                        selected_unit.movement_left -= move_cost
                        current_player.update_fog()
                        selected_unit = None
                        combat_log = "Юнит переместился."
                        
                    # НАЙМ ЮНИТА: если кликнули по своему городу, не выбрали юнита и клетка пуста
                    elif clicked_my_city and not clicked_unit:
                        UNIT_COST = 3
                        if current_player.stars >= UNIT_COST:
                            # Создаем нового юнита прямо в городе
                            new_unit = Unit(clicked_my_city.x, clicked_my_city.y, current_player)
                            current_player.units.append(new_unit)
                            all_units.append(new_unit)
                            
                            # Списываем звёзды
                            current_player.stars -= UNIT_COST
                            current_player.update_fog()
                            combat_log = f"Нанят новый юнит в городе за {UNIT_COST} ⭐️!"
                        else:
                            combat_log = f"Недостаточно звёзд для найма воина! Нужно {UNIT_COST} ⭐️."
                            
                    else:
                        selected_unit = None


    # --- ОТРИСОВКА ---
    valid_moves = get_valid_moves(selected_unit) if selected_unit else []
    attack_targets = get_attackable_targets(selected_unit) if selected_unit else []
    attack_coords = [(t.x, t.y) for t in attack_targets]
    
    current_fog = turn_manager.current_player.fog

    for row_idx, row in enumerate(map_data):
        for col_idx, tile_type in enumerate(row):
            iso_x, iso_y = to_isometric(col_idx, row_idx)
            
            if current_fog[row_idx][col_idx] == 0:
                color = (20, 20, 25)
            else:
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
            if current_fog[row_idx][col_idx] == 1:
                pygame.draw.polygon(screen, GRID_COLOR, points, 1)

    # Отрисовка городов (только если они видны в тумане)
    for city in all_cities:
        if current_fog[city.y][city.x] == 1:
            city.draw(screen)

    # Отрисовка юнитов
    for unit in all_units:
        if unit.hp > 0 and current_fog[unit.y][unit.x] == 1:
            unit.draw(screen)

    # --- UI ---
    pygame.draw.rect(screen, UI_BG, (0, 0, WIDTH, 50))
    current_p = turn_manager.current_player
    
    text_turn = font_large.render(f"Ход: {current_p.name}", True, current_p.color)
    text_stars = font.render(f"Звёзды: ⭐️ {current_p.stars} (+{1 + sum(c.income for c in current_p.cities)})", True, TEXT_COLOR)
    screen.blit(text_turn, (20, 12))
    screen.blit(text_stars, (WIDTH - 180, 15))
    
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
