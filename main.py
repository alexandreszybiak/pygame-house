# Example file showing a basic pygame "game loop"
import random
import math
from math import copysign

import pygame

# param
resolution = (160,240)
pixel_size = 3

# game param
laser_position = 220
laser_height = 4
smallest_platform = 16
largest_platform = 48
platform_height = 4

class Platform:
    def __init__(self):
        _width = random.randint(smallest_platform, largest_platform)
        _x = random.randint(0, viewport.get_width() - _width)
        _y = viewport.get_height()
        self.rect = pygame.Rect(_x, _y, _width, platform_height)
    def update(self):
        self.rect.update((self.rect.x, self.rect.y - 1), (self.rect.w, self.rect.h))
    def draw(self):
        pygame.draw.rect(viewport, 'blue', self.rect)

class Player:
    def __init__(self):
        self._x = viewport.get_width()/2-5
        self._y = 32
        self._width = 10
        self._height = 12
        self._velocity_y = 0
        self._y_remainder = 0
    def update(self):
        #self._velocity_y += 0.09
        #self._velocity_y
        self._y += self._velocity_y
        self.move_y(self._velocity_y)
    def move_y(self, amount):
        self._y_remainder += amount
        _move = round(self._y_remainder)
        if _move == 0:
            return
        self._y_remainder -= _move
        _sign = copysign(1, _move)
        while _move > 0:
            self._y += _sign
    def draw(self):
        pygame.draw.rect(viewport, 'yellow',(self._x, self._y, self._width, self._height))

# pygame setup
pygame.init()
screen = pygame.display.set_mode((resolution[0] * pixel_size, resolution[1] * pixel_size))
viewport = pygame.Surface(resolution)
clock = pygame.time.Clock()
pygame.time.set_timer(999, 1000, 0)
running = True

#game variables
wall = pygame.image.load('wall.png').convert()
platforms = []
player = Player()

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == 999:
            p = Platform()
            platforms.append(p)


    # fill the screen with a color to wipe away anything from last frame
    viewport.fill(0x656565)

    # UPDATE GAME
    player.update()
    for p in platforms:
        p.update()
        if p.rect[1] < 0 - platform_height:
            platforms.remove(p)

    # RENDER YOUR GAME HERE
    #viewport.blit(wall, wall.get_rect())
    player.draw()
    for p in platforms:
        p.draw()
    pygame.draw.rect(viewport, 'red', (0, laser_position, viewport.get_width(), laser_height))

    # flip() the display to put your work on screen
    screen.blit(pygame.transform.scale_by(viewport, 3), screen.get_rect())

    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()
