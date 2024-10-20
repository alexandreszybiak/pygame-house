import os
import math
from math import copysign

import pygame
from pygame import Rect
from pygame.math import Vector2
from pygame.surface import Surface

from main import viewport

os.environ['SDL_VIDEO_CENTERED'] = '1'

###############################################################################
#                               Game State                                    #
###############################################################################

class Entity:
    def __init__(self,state,position):
        self.state = state
        self.position = position
        self.rect = None
        self.movement_remainder = Vector2()

class Ball(Entity):
    def __init__(self,state,position,velocity):
        super().__init__(state,position)
        self.velocity = velocity
        self.rect = Rect(position.x, position.y, 4, 4)
        self.rect.center = self.state.area.center

class Paddle(Entity):
    def __init__(self,state,position):
        super().__init__(state, position)
        self.move_speed = 2
        self.rect = Rect(position.x,position.y,40,4)

class GameState:
    def __init__(self):
        self.area = Rect(0,0,160,240)
        self.paddle = Paddle(self, Vector2(0,200))
        self.balls = [ Ball(self, Vector2(0,0), Vector2(0.5,0)) ]

    def is_leaving_the_area(self, rect):
        return False

###############################################################################
#                                Commands                                     #
###############################################################################

class Command:
    def run(self):
        raise NotImplementedError()


class PaddleMoveCommand(Command):
    def __init__(self, state, paddle, move_direction):
        self.state = state
        self.paddle = paddle
        self.move_direction = move_direction

    def run(self):
        self.paddle.rect.move_ip(self.paddle.move_speed * self.move_direction, 0)

class MoveBallsCommand(Command):
    def __init__(self, state):
        self.state: GameState = state

    def run(self):
        for b in self.state.balls:
            self.move_x(b)

    def move_x(self, b: Ball):
        b.movement_remainder.x += b.velocity.x
        move: int = round(b.movement_remainder.x)
        if move == 0:
            return
        b.movement_remainder.x -= move
        sign: int = int(copysign(1, move))
        while move != 0:
            move -= sign
            if b.rect.move(sign, 0).right >= self.state.area.right or b.rect.move(sign, 0).left <= self.state.area.left:
                b.velocity.x *= -1
                break
            b.rect.move_ip(sign, 0)


###############################################################################
#                                Rendering                                    #
###############################################################################

class Layer:
    def __init__(self):
        self.entities = []

    def render(self, surface):
        for e in self.entities:
            pygame.draw.rect(surface, 'white', e.rect)

###############################################################################
#                             User Interface                                  #
###############################################################################

class UserInterface:
    def __init__(self):
        pygame.init()

        # Game state
        self.gameState = GameState()

        # Rendering properties
        self.pixel_size = 3
        self.rendering_layer = Layer()
        self.rendering_layer.entities.append(self.gameState.paddle)
        for b in self.gameState.balls:
            self.rendering_layer.entities.append(b)
        self.viewport = Surface(self.gameState.area.size)

        # Window
        self.window = pygame.display.set_mode(self.viewport.get_rect().scale_by(3,3).size)
        pygame.display.set_caption("Alexandre Szybiak - Breakout")

        # Controls
        self.paddle = self.gameState.paddle
        self.commands = []

        # Loop properties
        self.clock = pygame.time.Clock()
        self.running = True

    def process_input(self):
        # Pygame events (close & keyboard)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    break
        keys = pygame.key.get_pressed()
        move_direction = -keys[pygame.K_LEFT] + keys[pygame.K_RIGHT]

        # Keyboard controls the moves of the player's unit
        if move_direction != 0:
            command = PaddleMoveCommand(self.gameState, self.paddle, move_direction)
            self.commands.append(command)

        # Move balls
        self.commands.append(MoveBallsCommand(self.gameState))

        # Apply gravity

    def update(self):
        for command in self.commands:
            command.run()
        self.commands.clear()

    def render(self):
        self.viewport.fill((0, 0, 0))

        self.rendering_layer.render(self.viewport)

        self.window.blit(pygame.transform.scale_by(self.viewport, self.pixel_size), self.window.get_rect())

        pygame.display.update()

    def run(self):
        while self.running:
            self.process_input()
            self.update()
            self.render()
            self.clock.tick(60)

userInterface = UserInterface()
userInterface.run()

pygame.quit()