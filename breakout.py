import os
from math import copysign

import pygame
from pygame import Rect
from pygame.math import Vector2
from pygame.surface import Surface

os.environ['SDL_VIDEO_CENTERED'] = '1'

###############################################################################
#                               Game State                                    #
###############################################################################

class GameState:
    def __init__(self):
        self.area = Rect(0,0,160,240)
        self.paddle = Paddle(self, Vector2(0,200))
        self.balls = [ Ball(self, Vector2(0,0), Vector2(1,1)) ]
        self.brickGrid = Grid(10,8,16,8)

    def is_leaving_the_area(self, rect):
        return False

class Entity:
    def __init__(self,state: GameState,position):
        self.state: GameState = state
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
    def __init__(self,state,position: Vector2):
        super().__init__(state, position)
        self.move_speed = 2
        self.rect = Rect(position.x,position.y,40,4)

class Grid:
    def __init__(self, width, height, cell_width, cell_height):
        self.width: int = width
        self.cells = [1 for i in range(width * height)]
        self.cell_width: int = cell_width
        self.cell_height: int = cell_height

    @property
    def height(self):
        return len(self.cells) // self.width

    def get_cell_coordinates(self, world_x, world_y):
        x = world_x // self.cell_width
        y = world_y // self.cell_height
        return x,y

    def get_cell(self, x, y):
        if 0 > x >= self.width:
            return 0
        if y >= self.height:
            return 0
        index: int = x * y
        value: int = self.cells[index]
        return value

    def get_values(self, point_a: tuple[int, int], point_b: tuple[int, int]):
        cells_value = []
        top_left = self.get_cell_coordinates(point_a[0], point_a[1])
        bottom_right = self.get_cell_coordinates(point_b[0], point_b[1])
        for x in range(top_left[0], bottom_right[0] + 1):
            for y in range(top_left[1], bottom_right[1] + 1):
                cells_value.append(self.get_cell(x, y))
        return cells_value

    def get_region(self, x1, y1, x2, y2):
        cells = []
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                cells.append(self.get_cell(x, y))
        return cells

    def set_cell(self, value, x, y):
        self.cells[x + y * self.width] = value

    def set_region(self, value, x1, y1, x2, y2):
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                self.set_cell(value, x, y)

    def on_ball_collide_grid(self, point_a, point_b):
        pass

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
            self.move_y(b)

    def collide_x(self, ball, x_direction):
        if ball.rect.move(x_direction, 0).right > self.state.area.right or ball.rect.move(x_direction, 0).left < self.state.area.left:
            return True
        elif ball.rect.move(x_direction, 0).colliderect(self.state.paddle):
            return True
        return False

    def collide_y(self, ball, y_direction):
        if y_direction < 0:
            cell_1 = self.state.brickGrid.get_cell_coordinates(ball.rect.left, ball.rect.top)
            cell_2 = self.state.brickGrid.get_cell_coordinates(ball.rect.right, ball.rect.top)
            if 1 in self.state.brickGrid.get_region(cell_1[0], cell_1[1], cell_2[0], cell_2[1]):
                self.state.brickGrid.set_region(0, cell_1[0], cell_1[1], cell_2[0], cell_2[1])
                return True
        if ball.rect.move(0, y_direction).bottom > self.state.area.bottom or ball.rect.move(0, y_direction).top < self.state.area.top:
            return True
        elif ball.rect.move(0, y_direction).colliderect(ball.state.paddle):
            return True
        return False

    def move_x(self, b):
        b.movement_remainder.x += b.velocity.x
        move: int = round(b.movement_remainder.x)
        if move == 0:
            return
        b.movement_remainder.x -= move
        sign: int = int(copysign(1, move))
        while move != 0:
            move -= sign
            if self.collide_x(b, sign):
                b.velocity.x *= -1
                break
            b.rect.move_ip(sign, 0)

    def move_y(self, b):
        b.movement_remainder.y += b.velocity.y
        move: int = round(b.movement_remainder.y)
        if move == 0:
            return
        b.movement_remainder.y -= move
        sign: int = int(copysign(1, move))
        while move != 0:
            move -= sign
            if self.collide_y(b, sign):
                b.velocity.y *= -1
                break
            b.rect.move_ip(0, sign)

###############################################################################
#                                Rendering                                    #
###############################################################################
class RenderingLayer:
    def render(self, surface):
        raise NotImplementedError()

class EntityLayer(RenderingLayer):
    def __init__(self):
        self.entities = []

    def render(self, surface):
        # Render entities
        for e in self.entities:
            pygame.draw.rect(surface, 'white', e.rect)

class TileLayer(RenderingLayer):
    def __init__(self, grid):
        self.grid: Grid = grid

    def render(self, surface):
        for count, cell in enumerate(self.grid.cells):
            if cell == 0:
                continue
            x = count % self.grid.width * self.grid.cell_width
            y = count // self.grid.width * self.grid.cell_height
            w = self.grid.cell_width - 1
            h = self.grid.cell_height - 1
            pygame.draw.rect(surface, 'white', Rect(x,y,w,h))



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

        entity_layer = EntityLayer()
        entity_layer.entities.append(self.gameState.paddle)
        for b in self.gameState.balls:
            entity_layer.entities.append(b)
        tile_layer = TileLayer(self.gameState.brickGrid)
        self.rendering_layers = [entity_layer, tile_layer]
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

        for l  in self.rendering_layers:
            l.render(self.viewport)

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