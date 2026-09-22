import pygame
import sys
import random

# Импортируем параметры и классы из созданных модулей
from config import *
from map_gen import generate_map
from entities import Unit, Player, TurnManager, City, Port, to_isometric

def from_isometric(screen_x, screen_y):
    """Преобразует экранные координаты мыши в координаты сетки (X, Y)"""
    cx = screen_x - (WIDTH // 2)
    cy = screen_y - (HEIGHT // 4)
    grid_x = int((cx / (TILE_WIDTH / 2) + cy / (TILE_HEIGHT / 2)) / 2)
    grid_y = int((cy / (TILE_HEIGHT / 2) - cx / (TILE_WIDTH / 2)) / 2)
    return grid_x, grid_y

# Инициализация графического движка Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Polytopia Naval & Cities Edition")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 16)
font_large = pygame.font.SysFont("Arial", 22, bold=True)

# Процедурная генерация игрового мира
map_data = generate_map(MAP_SIZE)
land_tiles = [(c, r) for r in range(MAP_SIZE) for c in range(MAP_SIZE) if map_data[r][c] == 1]

# Если суши слишком мало, подстраховываемся и создаем сухую карту
if len(land_tiles) < 5:
    map_data = [[1 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
    land_tiles = [(c, r) for r in range(MAP_SIZE) for c in range(MAP_SIZE)]

# Случайное распределение 4 городов на суше
random.shuffle(land_tiles)
cities_positions = land_tiles[:4]

all_cities = []
all_ports = []  # Хранилище для всех построенных пирсов

for pos in cities_positions:
    all_cities.append(City(pos[0], pos[1]))

# Стартовые координаты игроков привязываем к первым двум городам
p1_spawn = (all_cities[0].x, all_cities[0].y)
p2_spawn = (all_cities[1].x, all_cities[1].y)

# Создание объектов игроков
player1 = Player("Игрок 1 (Синий)", (50, 150, 255))
player2 = Player("Игрок 2 (Красный)", (255, 70, 70))

# Передаем стартовые города во владение фракциям
all_cities[0].owner = player1
player1.cities.append(all_cities[0])
all_cities[1].owner = player2
player2.cities.append(all_cities[1])

# Создаем по первому юниту в границах столиц
p1_unit = Unit(p1_spawn[0], p1_spawn[1], player1)
p2_unit = Unit(p2_spawn[0], p2_spawn[1], player2)

player1.units.append(p1_unit)
player2.units.append(p2_unit)

all_units = [p1_unit, p2_unit]
turn_manager = TurnManager([player1, player2])

# Первичное рассеивание тумана войны вокруг стартовых зон
player1.update_fog()
player2.update_fog()

# Элементы интерфейса
end_turn_btn = pygame.Rect(WIDTH - 180, HEIGHT - 70, 150, 45)
selected_unit = None
combat_log = "Зайдите на мелководье и кликните на юнита ещё раз, чтобы построить Порт (5 ⭐️)!"

def get_valid_moves(unit):
    """Рассчитывает доступные плитки для перемещения с учетом типа юнита (корабль/пехота)"""
    valid_moves = []
    if not unit or unit.movement_left <= 0:
        return valid_moves
    for r in range(MAP_SIZE):
        for c in range(MAP_SIZE):
            tile = map_data[r][c]
            distance = abs(unit.x - c) + abs(unit.y - r)
            if 0 < distance <= unit.movement_left:
                # На занятую клетку наступать нельзя
                if any(u.x == c and u.y == r for u in all_units):
                    continue
                
                if unit.is_ship:
                    # Морские корабли ходят только по океану (0), мелководью (2) или заплывают в порты
                    has_port = any(p.x == c and p.y == r for p in all_ports)
                    if tile in [0, 2] or has_port:
                        valid_moves.append((c, r))
                else:
                    # Сухопутные войска ходют по земле (1) или союзным портам на воде
                    if tile == 1:
                        valid_moves.append((c, r))
                    elif tile == 2:
                        is_my_port = any(p.x == c and p.y == r and p.owner == unit.owner for p in all_ports)
                        if is_my_port or (abs(unit.x - c) <= 1 and abs(unit.y - r) <= 1):
                            valid_moves.append((c, r))
    return valid_moves

def get_attackable_targets(unit):
    """Возвращает список целей. Корабли стреляют дальше (на 2 клетки)"""
    targets = []
    if not unit or unit.has_attacked:
        return targets
    for u in all_units:
        if u.owner != unit.owner and u.hp > 0:
            distance = abs(unit.x - u.x) + abs(unit.y - u.y)
            max_range = 2 if unit.is_ship else 1
            if distance <= max_range:
                targets.append(u)
    return targets

def check_city_capture(player):
    """Механика проверки и захвата чужих/нейтральных поселений пехотой"""
    global combat_log
    for unit in player.units:
        if unit.hp > 0 and not unit.is_ship:
            for city in all_cities:
                if city.x == unit.x and city.y == unit.y and city.owner != player:
                    if city.owner: 
                        city.owner.cities.remove(city)
                    city.owner = player
                    player.cities.append(city)
                    combat_log = f"{player.name} успешно захватил город на ({city.x}, {city.y})!"

# Главный цикл игры
running = True
while running:
    screen.fill(BG_COLOR)
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        # ОБРАБОТКА КЛАВИАТУРЫ: Смена хода по Пробелу
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                check_city_capture(turn_manager.current_player)
                turn_manager.next_turn()
                selected_unit = None
                combat_log = "Ход передан (Клавиша Пробел)."
                continue
        
        # ОБРАБОТКА МЫШИ
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Левый клик
                # Клик по кнопке окончания хода на экране
                if end_turn_btn.collidepoint(mouse_pos):
                    check_city_capture(turn_manager.current_player)
                    turn_manager.next_turn()
                    selected_unit = None
                    continue
                
                # Переводим курсор мыши в координаты игрового поля
                gx, gy = from_isometric(mouse_pos[0], mouse_pos[1])
                
                if 0 <= gy < MAP_SIZE and 0 <= gx < MAP_SIZE:
                    current_player = turn_manager.current_player
                    
                    # Проверяем наличие юнита на выбранной клетке
                    clicked_unit = None
                    for u in all_units:
                        if u.x == gx and u.y == gy and u.hp > 0:
                            clicked_unit = u
                    
                    # Проверяем наличие союзного города на клетке
                    clicked_my_city = None
                    for city in all_cities:
                        if city.is_clicked(gx, gy) and city.owner == current_player:
                            clicked_my_city = city

                    # МЕХАНИКА: Постройка морского端口 при повторном клике по своему юниту на мелководье
                    if selected_unit and clicked_unit == selected_unit and map_data[gy][gx] == 2:
                        has_port_here = any(p.x == gx and p.y == gy for p in all_ports)
                        if not has_port_here:
                            if current_player.stars >= PORT_COST:
                                current_player.stars -= PORT_COST
                                new_port = Port(gx, gy, current_player)
                                all_ports.append(new_port)
                                current_player.ports.append(new_port)
                                selected_unit.is_ship = True # Переводим в статус корабля
                                combat_log = "Порт возведен! Юнит спущен на воду в качестве Корабля! ⛵"
                                selected_unit = None
                                current_player.update_fog()
                                continue
                            else:
                                combat_log = f"Недостаточно средств. Нужно {PORT_COST} ⭐️ для порта!"
                    
                    # Выделение союзного бойца
                    if clicked_unit and clicked_unit.owner == current_player:
                        selected_unit = clicked_unit
                        combat_log = f"Выбран юнит {clicked_unit.owner.name}."
                    
                    # СРАЖЕНИЕ: Атака вражеской цели
                    elif selected_unit and clicked_unit and clicked_unit in get_attackable_targets(selected_unit):
                        attacker = selected_unit
                        defender = clicked_unit
                        
                        atk_force = attacker.atk * (attacker.hp / attacker.max_hp)
                        def_force = defender.def_power * (defender.hp / defender.max_hp)
                        total_force = atk_force + def_force if (atk_force + def_force) > 0 else 1
                        
                        damage_to_def = round((atk_force / total_force) * attacker.atk * 1.5)
                        defender.take_damage(damage_to_def)
                        log_msg = f"Атака! Нанесено {damage_to_def} урона. "
                        
                        # Контратака соперника, если он выжил в бою
                        if defender.hp > 0:
                            damage_to_atk = round((def_force / total_force) * defender.def_power * 1.5)
                            attacker.take_damage(damage_to_atk)
                            log_msg += f"Ответный удар: получено {damage_to_atk} урона."
                        else:
                            log_msg += "Враг полностью уничтожен!"
                            if defender in all_units: all_units.remove(defender)
                            if defender in defender.owner.units: defender.owner.units.remove(defender)
                        
                        attacker.has_attacked = True
                        attacker.movement_left = 0
                        selected_unit = None
                        combat_log = log_msg
                        
                    # ПЕРЕМЕЩЕНИЕ: Ход на пустую подсвеченную клетку
                    elif selected_unit and (gx, gy) in get_valid_moves(selected_unit):
                        move_cost = abs(selected_unit.x - gx) + abs(selected_unit.y - gy)
                        selected_unit.x = gx
                        selected_unit.y = gy
                        selected_unit.movement_left -= move_cost
                        
                        # Трансформация в корабль при заходе на клетку порта из тумана
                        is_at_port = any(p.x == gx and p.y == gy and p.owner == current_player for p in all_ports)
                        if is_at_port and not selected_unit.is_ship:
                            selected_unit.is_ship = True
                            combat_log = "Юнит успешно зашел в доки и принял форму Корабля!"
                        
                        # Обратная трансформация корабля в сухопутного пехотинца при высадке
                        if map_data[gy][gx] == 1 and selected_unit.is_ship:
                            selected_unit.is_ship = False
                            combat_log = "Корабль причалил. Армия высадилась на сушу!"

                        current_player.update_fog()
                        selected_unit = None
                        
                    # ЭКОНОМИКА: Наем (спавн) нового воина в пустом городе
                    elif clicked_my_city and not clicked_unit:
                        if current_player.stars >= UNIT_COST:
                            new_unit = Unit(clicked_my_city.x, clicked_my_city.y, current_player)
                            current_player.units.append(new_unit)
                            all_units.append(new_unit)
                            current_player.stars -= UNIT_COST
                            current_player.update_fog()
                            combat_log = f"Новый воин успешно нанят за {UNIT_COST} ⭐️!"
                        else:
                            combat_log = f"Не хватает звёзд для найма! Требуется {UNIT_COST} ⭐️."
                    else:
                        selected_unit = None

    # --- ОТРИСОВКА ИГРОВОГО МИРА ---
    valid_moves = get_valid_moves(selected_unit) if selected_unit else []
    attack_targets = get_attackable_targets(selected_unit) if selected_unit else []
    attack_coords = [(t.x, t.y) for t in attack_targets]
    
    current_fog = turn_manager.current_player.fog

    for row_idx, row in enumerate(map_data):
        for col_idx, tile_type in enumerate(row):
            iso_x, iso_y = to_isometric(col_idx, row_idx)
            
            # Маскировка неразведанных плиток черным цветом
            if current_fog[row_idx][col_idx] == 0:
                color = (20, 20, 25)
            else:
                if (col_idx, row_idx) in attack_coords:
                    color = (230, 80, 80) # Красный индикатор мишени
                elif (col_idx, row_idx) in valid_moves:
                    color = VALID_MOVE_COLOR # Зеленый индикатор хода
                else:
                    if tile_type == 1: color = LAND_COLOR
                    elif tile_type == 2: color = SHALLOW_COLOR
                    else: color = WATER_COLOR
                
            points = [
                (iso_x, iso_y), 
                (iso_x + TILE_WIDTH // 2, iso_y + TILE_HEIGHT // 2), 
                (iso_x, iso_y + TILE_HEIGHT), 
                (iso_x - TILE_WIDTH // 2, iso_y + TILE_HEIGHT // 2)
            ]
            pygame.draw.polygon(screen, color, points)
            if current_fog[row_idx][col_idx] == 1:
                pygame.draw.polygon(screen, GRID_COLOR, points, 1)

    # Отрисовка видимых объектов инфраструктуры и войск
    for port in all_ports:
        if current_fog[port.y][port.x] == 1: 
            port.draw(screen)
            
    for city in all_cities:
        if current_fog[city.y][city.x] == 1: 
            city.draw(screen)
            
    for unit in all_units:
        if unit.hp > 0 and current_fog[unit.y][unit.x] == 1: 
            unit.draw(screen)

    # --- ОТРЕНДЕРИВАНИЕ ИНТЕРФЕЙСА (UI) ---
    pygame.draw.rect(screen, UI_BG, (0, 0, WIDTH, 50))
    current_p = turn_manager.current_player
    
    text_turn = font_large.render(f"Ход: {current_p.name}", True, current_p.color)
    text_stars = font.render(f"Звёзды: ⭐️ {current_p.stars} (+{1 + sum(c.income for c in current_p.cities)})", True, TEXT_COLOR)
    screen.blit(text_turn, (20, 12))
    screen.blit(text_stars, (WIDTH - 180, 15))
    
    pygame.draw.rect(screen, UI_BG, (0, HEIGHT - 50, WIDTH - 200, 50))
    text_log = font.render(f"События: {combat_log}", True, TEXT_COLOR)
    screen.blit(text_log, (20, HEIGHT - 33))

    # Кнопка передачи управления
    btn_color = (80, 180, 80) if not end_turn_btn.collidepoint(mouse_pos) else (100, 210, 100)
    pygame.draw.rect(screen, btn_color, end_turn_btn, border_radius=5)
    text_btn = font_large.render("Конец хода", True, (255, 255, 255))
    screen.blit(text_btn, (WIDTH - 158, HEIGHT - 58))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()