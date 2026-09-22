import pygame
from main import to_isometric

TILE_HEIGHT = 32

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