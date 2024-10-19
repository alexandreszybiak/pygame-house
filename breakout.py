import os
import math
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
    def render(self, surface):
        pygame.draw.rect(surface, 'white', self.rect)

class Ball(Entity):
    def __init__(self,state,position,velocity):
        super().__init__(state,position)
        self.velocity = velocity

class Paddle(Entity):
    def __init__(self,state,position):
        super().__init__(state, position)
        self.move_speed = 2
        self.rect = Rect(position.x,position.y,80,4)

class GameState:
    def __init__(self):
        self.paddle = Paddle(self, Vector2(0,200))

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

###############################################################################
#                                Rendering                                    #
###############################################################################



###############################################################################
#                             User Interface                                  #
###############################################################################

class UserInterface:
    def __init__(self):
        pygame.init()

        # Game state
        self.gameState = GameState()

        # Rendering properties
        resolution = Vector2(160, 240)
        self.pixel_size = 3
        self.entities = [ self.gameState.paddle]
        self.viewport = Surface(resolution)

        # Window
        window_size = resolution.elementwise() * 3
        self.window = pygame.display.set_mode((int(window_size.x), int(window_size.y)))
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

        # Apply gravity

    def update(self):
        for command in self.commands:
            command.run()
        self.commands.clear()

    def render(self):
        self.viewport.fill((0, 0, 0))

        for entity in self.entities:
            entity.render(self.viewport)

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