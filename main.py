# Example file showing a basic pygame "game loop"
import random
import math
from math import copysign, floor
from operator import truediv
from random import randint
from tokenize import Intnumber

import pygame

# param
resolution = (160,240)
pixel_size = 3

# game param
gravity = 0.065
platform_timer = 1000
laser_position = 40
laser_height = 4
smallest_platform = 16
largest_platform = 48
platform_height = 4
player_spawn_position = 48
platform_timer_id = 999
score_position = (3,3)

class Laser:
    def __init__(self, y):
        self.rect = pygame.Rect(0, y, viewport.get_width(), laser_height)
    def draw(self):
        pygame.draw.rect(viewport, 'red', self.rect)
class Platform:
    def __init__(self):
        _width = random.randint(smallest_platform, largest_platform)
        _x = random.randint(0, viewport.get_width() - _width)
        _y = viewport.get_height()
        self.rect = pygame.Rect(_x, _y, _width, platform_height)
        self.rect.move_ip(0, randint(0, 32))
    def update(self):
        self.rect.move_ip(0, -1)
        #self.rect.update((self.rect.x, self.rect.y - 1), (self.rect.w, self.rect.h))
    def draw(self):
        pygame.draw.rect(viewport, 'blue', self.rect)

class Player:
    def __init__(self):
        self.alive = True
        self.is_falling = False
        self._width = 8
        self._height = 24
        self._velocity_y = 0
        self._y_remainder = 0
        self.rect = pygame.Rect(viewport.get_width()/2-5, player_spawn_position, self._width, self._height)
        self.bounce_amount = 3.2
        self.bounce_amount_modifier = 0.25
        self.score = 0
        self.flip = False
    def set_flip(self, value):
        self.flip = value
        x = self.rect.centerx
        y = self.rect.bottom
        size = (self._height, self._width)
        if not self.flip:
            size = (self._width, self._height)
        self.rect.update((0, 0), size)
        self.rect.centerx = x
        self.rect.bottom = y
    def respawn(self):
        self.set_flip(False)
        self.alive = True
        self.score = 0
        self.rect.y = player_spawn_position
        self.rect.centerx = viewport.get_rect().centerx
        self._velocity_y = 0
    def die(self):
        self.alive = False
        self.is_falling = False
        pygame.time.set_timer(platform_timer_id, 0, 0)
        platforms.clear()
    def update(self):
        if not self.alive:
            return
        move_dir = -keys[pygame.K_LEFT] + keys[pygame.K_RIGHT]
        if not self.is_falling:
            return
        # Check for death
        if self.rect.collidelist(lasers) != -1:
            self.die()
        self._velocity_y += gravity
        if self._velocity_y > 4:
            self._velocity_y = 4
        #self._velocity_y
        #self._y += self._velocity_y
        self.rect.move_ip(move_dir * 2, 0)
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > viewport.get_width():
            self.rect.right = viewport.get_width()
        self.move_y(self._velocity_y)
    def move_y(self, amount):
        self._y_remainder += amount
        _move = round(self._y_remainder)
        if _move == 0:
            return
        self._y_remainder -= _move
        _sign = copysign(1, _move)
        while _move != 0:
            p = self.rect.move(0,_sign).collidelist(platforms)
            if p == -1:
                self.rect.move_ip(0, _sign)
                _move -= _sign
            else:
                self._velocity_y = -self.bounce_amount * (1 - self.flip * self.bounce_amount_modifier)
                self.set_flip(not self.flip)
                platforms.pop(p)
                self.score += 1
                break
    def draw(self):
        if self.alive:
            pygame.draw.rect(viewport, 'yellow',self.rect)

# pygame setup
pygame.init()
screen = pygame.display.set_mode((resolution[0] * pixel_size, resolution[1] * pixel_size))
viewport = pygame.Surface(resolution)
clock = pygame.time.Clock()
pygame.time.set_timer(platform_timer_id, platform_timer, 0)
running = True
keys = pygame.key.get_pressed()
font = pygame.font.Font('freesansbold.ttf', 32)
game_over_text = font.render('Game Over', False, 'green', 'blue')
game_over_text_rect = game_over_text.get_rect()

#game variable
game_state = 0

#ingame variables
numbers_sprite = pygame.image.load('numbers.bmp')
numbers_sprite.set_colorkey((255,0,255))
platforms = []
lasers = [ Laser(laser_position), Laser(viewport.get_height() - laser_position - laser_height) ]
player = Player()

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if not player.alive:
                player.respawn()
                pygame.time.set_timer(platform_timer_id, platform_timer, 0)
            elif not player.is_falling:
                player.is_falling = True
        if event.type == pygame.QUIT:
            running = False
        if event.type == 999:
            p = Platform()
            platforms.append(p)
    keys = pygame.key.get_pressed()

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
    # Laser
    pygame.draw.rect(viewport, 'red', (0, laser_position, viewport.get_width(), laser_height))
    pygame.draw.rect(viewport, 'red', (0, viewport.get_height() - laser_position, viewport.get_width(), laser_height))

    if not player.alive:
        viewport.blit(game_over_text, game_over_text_rect)

    # Display score
    n = floor(player.score / 10)
    if n > 0:
        viewport.blit(numbers_sprite, (viewport.get_width() - 10,3,5,5),(n * 5,0,5,5))
    n = player.score % 10
    viewport.blit(numbers_sprite, (viewport.get_width() - 6,3,5,5),(n * 5,0,5,5))
    # flip() the display to put your work on screen
    screen.blit(pygame.transform.scale_by(viewport, 3), screen.get_rect())

    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()
