import pygame
from config import WIDTH, HEIGHT, TILE_WIDTH, TILE_HEIGHT, MAP_SIZE

def to_isometric(grid_x, grid_y):
    iso_x = (grid_x - grid_y) * (TILE_WIDTH // 2) + (WIDTH // 2)
    iso_y = (grid_x + grid_y) * (TILE_HEIGHT // 2) + (HEIGHT // 4)
    return int(iso_x), int(iso_y)

class City:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.owner = None  
        self.income = 2    

    def is_clicked(self, mouse_grid_x, mouse_grid_y):
        return self.x == mouse_grid_x and self.y == mouse_grid_y

    def draw(self, surface):
        iso_x, iso_y = to_isometric(self.x, self.y)
        center_x = iso_x
        center_y = iso_y + TILE_HEIGHT // 2
        color = self.owner.color if self.owner else (200, 200, 200)
        pygame.draw.rect(surface, color, (center_x - 8, center_y - 12, 16, 16))
        pygame.draw.polygon(surface, (50, 50, 50), [(center_x - 10, center_y - 12), (center_x, center_y - 20), (center_x + 10, center_y - 12)])

class Port:
    def __init__(self, x, y, owner):
        self.x = x
        self.y = y
        self.owner = owner

    def draw(self, surface):
        iso_x, iso_y = to_isometric(self.x, self.y)
        center_x = iso_x
        center_y = iso_y + TILE_HEIGHT // 2
        # Деревянный пирс (коричневый прямоугольник)
        pygame.draw.rect(surface, (139, 69, 19), (center_x - 12, center_y - 4, 24, 8))
        # Маленький флажок цвета владельца
        pygame.draw.rect(surface, self.owner.color, (center_x + 4, center_y - 12, 6, 5))
        pygame.draw.line(surface, (200, 200, 200), (center_x + 4, center_y - 12), (center_x + 4, center_y - 2))

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
        self.is_ship = False # Новый статус: корабль ли мы?

    def reset_turn(self):
        self.movement_left = self.max_movement
        self.has_attacked = False

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp < 0: self.hp = 0

    def draw(self, surface):
        iso_x, iso_y = to_isometric(self.x, self.y)
        center_x = iso_x
        center_y = iso_y + TILE_HEIGHT // 2
        
        if self.is_ship:
            # Отрисовка корабля (треугольник в изометрии)
            points = [(center_x, center_y - 12), (center_x - 10, center_y + 4), (center_x + 10, center_y + 4)]
            pygame.draw.polygon(surface, self.owner.color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 1) # Белый парус
        else:
            # Обычный воин (круг)
            pygame.draw.circle(surface, self.owner.color, (center_x, center_y), 12)
        
        if self.movement_left == 0 and self.has_attacked:
            pygame.draw.circle(surface, (100, 100, 100), (center_x, center_y), 4)

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
        self.cities = [] 
        self.ports = [] # Список портов игрока
        self.fog = [[0 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]

    def collect_income(self):
        self.stars += 1 + sum(city.income for city in self.cities)

    def update_fog(self):
        for unit in self.units:
            if unit.hp > 0: self.reveal_area(unit.x, unit.y, 1)
        for city in self.cities:
            self.reveal_area(city.x, city.y, 1)
        for port in self.ports:
            self.reveal_area(port.x, port.y, 1)

    def reveal_area(self, cx, cy, radius):
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                r = cy + dr
                c = cx + dc
                if 0 <= r < MAP_SIZE and 0 <= c < MAP_SIZE:
                    self.fog[r][c] = 1

class TurnManager:
    def __init__(self, players):
        self.players = players
        self.current_player_idx = 0

    @property
    def current_player(self): return self.players[self.current_player_idx]

    def next_turn(self):
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        self.current_player.collect_income()
        for unit in self.current_player.units: unit.reset_turn()
        self.current_player.update_fog()
