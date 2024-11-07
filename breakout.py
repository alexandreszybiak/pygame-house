import os
import json
from math import copysign, floor, ceil
from turtledemo.penrose import start

import pygame
from pygame import Rect
from pygame.math import Vector2
from pygame.surface import Surface

os.environ['SDL_VIDEO_CENTERED'] = '1'


###############################################################################
#                                 Engine                                      #
###############################################################################

class Grid:
    def __init__(self, x, y, width, cell_width, cell_height):
        self.x = x
        self.y = y
        self.width: int = width
        self.cells = []
        self.cell_width: int = cell_width
        self.cell_height: int = cell_height

    def fill(self, value):
        pass

    def fill_with_data(self, data):
        self.cells = data

    @property
    def height(self):
        return len(self.cells) // self.width

    def get_cell_coordinates(self, world_x, world_y):
        x = (world_x - self.x) // self.cell_width
        y = (world_y - self.y) // self.cell_height
        return x, y

    def get_cell(self, x, y):
        if x >= self.width or x < 0:
            return 0
        if y >= self.height or y < 0:
            return 0
        index: int = x + y * self.width
        value: int = self.cells[index]
        return value

    def set_cell(self, value, x: int, y: int):
        if x < 0 or x >= self.width: return
        if y < 0 or y >= self.height: return
        index = x + y * self.width
        if 0 <= index < len(self.cells):
            self.cells[index] = value

    def get_cell_world(self, pos: Vector2):
        return self.get_cell(int(pos.x // self.cell_width), int(pos.y // self.cell_height))

    def set_cell_world(self, value, pos: Vector2):
        self.set_cell(value, int(pos.x // self.cell_width), int(pos.y // self.cell_height))

    def get_region(self, x1, y1, x2, y2):
        cells = []
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                cells.append(self.get_cell(x, y))
        return cells

    def get_region_coordinate_and_value(self, x1, y1, x2, y2) -> list[tuple[int, int, int]]:
        cells: list[tuple[int, int, int]] = []
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                cells.append((x, y, self.get_cell(x, y)))
        return cells

    def set_region(self, value, x1: int, y1: int, x2: int, y2: int):
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                self.set_cell(value, x, y)

    def set_region_world(self, value, rect):
        x1: int = int(rect.left / self.cell_width)
        y1: int = int(rect.top / self.cell_height)
        x2: int = int(rect.right / self.cell_width)
        y2: int = int(rect.bottom / self.cell_height)
        self.set_region(value, x1, y1, x2, y2)


###############################################################################
#                               Game State                                    #
###############################################################################

class GameState:
    def __init__(self):
        self.area = Rect(0, 0, 160, 240)
        self.paddle: Paddle = Paddle(self, Vector2(0, 200))
        self.paddle.rect.centerx = self.area.centerx
        self.balls: list[Ball] = []
        self.brick_grid = None
        self.brick_grids: list[BrickGrid] = []
        self.collisions: list[Collision] = []
        self.brick_width = 16
        self.brick_height = 8
        self.observers: list[GameStateObserver] = []

    def add_observer(self, observer):
        self.observers.append(observer)

    def notify_ball_created(self, ball):
        for observer in self.observers:
            observer.on_ball_created(ball)


class Entity:
    def __init__(self, state: GameState, position):
        self.state: GameState = state
        self.position = position
        self.velocity = Vector2(0, 0)
        self.rect: Rect = Rect(0, 0, 1, 1)
        self.movement_remainder = Vector2()


class Ball(Entity):
    def __init__(self, state, position):
        super().__init__(state, position)
        self.rect = Rect(position.x, position.y, 4, 4)
        self.rect.center = self.state.area.center
        self.is_stuck_on_paddle = False


class Paddle(Entity):
    def __init__(self, state, position: Vector2):
        super().__init__(state, position)
        self.move_speed = 2
        self.rect = Rect(position.x, position.y, 40, 4)


class BrickGrid(Grid):
    def __init__(self, x, y, width, cell_width, cell_height, environment):
        super().__init__(x, y, width, cell_width, cell_height)
        self.environment = environment


class Collision:
    def __init__(self, collider: Entity, axis: Vector2):
        self.collider = collider
        self.axis = axis

    def process(self):
        pass


class GridCollision(Collision):
    def __init__(self, collider: Entity, axis: Vector2, brick_grid: BrickGrid, hit_cells):
        super().__init__(collider, axis)
        self.brick_grid = brick_grid
        self.hit_cells = hit_cells

    def process(self):
        for c in self.hit_cells:
            self.brick_grid.set_cell(0, c[0], c[1])


class BallCollision(Collision):
    def __init__(self, collider: Entity, axis: Vector2):
        super().__init__(collider, axis)

    def process(self):
        self.collider.velocity.reflect_ip(self.axis)


class BallCollisionWithPaddle(Collision):
    def __init__(self, collider: Entity, axis: Vector2, paddle: Paddle):
        super().__init__(collider, axis)
        self.paddle = paddle

    def process(self):
        if self.axis.x == 0:
            offset = (self.collider.rect.centerx - self.paddle.rect.centerx) / (self.paddle.rect.w / 2)
            ball_orientation = self.collider.velocity.angle_to(Vector2(0, 0))
            angle = offset * 20
            rounded_normal = Vector2(0, 1).rotate(angle)
            flat_normal = Vector2(0, 1)
            new_velocity = self.collider.velocity.reflect(rounded_normal)
            new_angle = new_velocity.angle_to(Vector2(0, 0))

            if new_angle < 20 or new_angle > 160:
                new_velocity = self.collider.velocity.reflect(flat_normal)

            self.collider.velocity.update(new_velocity)

            self.collider.velocity *= 1.25
            self.collider.velocity.clamp_magnitude_ip(3)
        else:
            self.collider.velocity.reflect_ip(self.axis)


###############################################################################
#                                Commands                                     #
###############################################################################

class Command:
    def run(self):
        raise NotImplementedError()


class LaunchBallCommand(Command):
    def __init__(self, state: GameState):
        self.state = state

    def run(self):
        b = self.state.balls[0]
        b.is_stuck_on_paddle = False
        b.velocity = Vector2(1, -1)


class PaddleMoveCommand(Command):
    def __init__(self, state, paddle, move_direction):
        self.state: GameState = state
        self.paddle = paddle
        self.move_direction = move_direction

    def run(self):
        self.paddle.rect.move_ip(self.paddle.move_speed * self.move_direction, 0)


class InitBallCommand(Command):
    def __init__(self, state: GameState):
        self.state = state

    def run(self):
        new_ball = Ball(self.state, Vector2(0, 0))
        new_ball.is_stuck_on_paddle = True
        new_ball.rect.midbottom = self.state.paddle.rect.midtop
        self.state.balls.append(new_ball)
        self.state.notify_ball_created(new_ball)


class MoveBallsCommand(Command):
    def __init__(self, state):
        self.state: GameState = state

    def run(self):
        for b in self.state.balls:
            if b.is_stuck_on_paddle:
                b.rect.midbottom = self.state.paddle.rect.midtop
                continue
            self.move_y(b)
            self.move_x(b)

    def collide_x(self, ball: Ball, x_direction):
        axis = Vector2(1, 0)
        collide = False
        ball_rect = ball.rect.move(x_direction, 0)

        # Paddle
        if self.state.paddle is not None and ball_rect.colliderect(self.state.paddle):
            collide = True

        # Area Boundaries
        if ball_rect.right > self.state.area.right:
            collide = True
        elif ball_rect.left < self.state.area.left:
            collide = True

        # Grids
        x = ball_rect.left if x_direction < 0 else ball_rect.right
        grids: list[tuple[BrickGrid, tuple[int, int]]] = []
        for g in self.state.brick_grids:
            cell_1 = g.get_cell_coordinates(x, ball_rect.top)
            cell_2 = g.get_cell_coordinates(x, ball_rect.bottom)
            cells = g.get_region_coordinate_and_value(cell_1[0], cell_1[1], cell_2[0], cell_2[1])

            hit_cells = [c for c in cells if c[2]]

            if hit_cells:
                self.state.collisions.append(GridCollision(ball, axis, g, hit_cells))
                collide = True

        if collide:
            self.state.collisions.append(BallCollision(ball, axis))

        return collide

    def collide_y(self, ball, y_direction):
        axis = Vector2(0, 1)
        collide = False
        ball_rect = ball.rect.move(0, y_direction)

        # Paddle
        if self.state.paddle is not None and ball_rect.colliderect(self.state.paddle):
            self.state.collisions.append(BallCollisionWithPaddle(ball, axis, self.state.paddle))
            return True

        # Area Boundaries
        if ball_rect.top < self.state.area.top:
            self.state.collisions.append(BallCollision(ball, axis))
            return True
        elif ball_rect.bottom > self.state.area.bottom:
            self.state.collisions.append(BallCollision(ball, axis))
            return True

        # Grids
        y = ball_rect.top if y_direction < 0 else ball_rect.bottom
        for g in self.state.brick_grids:
            cell_1 = g.get_cell_coordinates(ball_rect.left, y)
            cell_2 = g.get_cell_coordinates(ball_rect.right, y)
            cells = g.get_region_coordinate_and_value(cell_1[0], cell_1[1], cell_2[0], cell_2[1])

            hit_cells = [c for c in cells if c[2]]

            if hit_cells:
                self.state.collisions.append(GridCollision(ball, axis, g, hit_cells))
                collide = True

        if collide:
            self.state.collisions.append(BallCollision(ball, axis))

        return collide

    def move_x(self, ball):
        ball.movement_remainder.x += ball.velocity.x
        move: int = round(ball.movement_remainder.x)
        if move == 0:
            return
        ball.movement_remainder.x -= move
        sign: int = int(copysign(1, move))
        while move != 0:
            move -= sign
            if self.collide_x(ball, sign):
                break
            ball.rect.move_ip(sign, 0)

    def move_y(self, ball):
        ball.movement_remainder.y += ball.velocity.y
        move: int = round(ball.movement_remainder.y)
        if move == 0:
            return
        ball.movement_remainder.y -= move
        sign: int = int(copysign(1, move))
        while move != 0:
            move -= sign
            if self.collide_y(ball, sign):
                break
            ball.rect.move_ip(0, sign)


class RunCollisionsCommand(Command):
    def __init__(self, state):
        self.state: GameState = state

    def run(self):
        for c in self.state.collisions:
            c.process()
        self.state.collisions.clear()


class EditBrickGrid(Command):
    def __init__(self, state, value, rect):
        self.state: GameState = state
        self.value = value
        self.rect: Rect = rect

    def run(self):
        self.state.brick_grid.set_region_world(self.value, self.rect)


class CreateBrickGrid(Command):
    def __init__(self, state, rect):
        self.state: GameState = state
        self.rect: Rect = rect

    def run(self):
        x = self.rect.left // self.state.brick_width
        y = self.rect.top // self.state.brick_height
        w = int(ceil(self.rect.right / self.state.brick_width)) - x
        h = int(ceil(self.rect.bottom / self.state.brick_height)) - y

        new_grid = BrickGrid(x * self.state.brick_width, y * self.state.brick_height, w, self.state.brick_width,
                             self.state.brick_height, 1)
        new_grid.cells = [1 for i in range(w * h)]
        self.state.brick_grids.append(new_grid)


class LoadLevel(Command):
    def __init__(self, state):
        self.state: GameState = state

    def run(self):
        with (open("level.json", mode="r", encoding="utf-8") as read_file):
            data = json.load(read_file)
            for grid_data in data:
                x = grid_data["x"]
                y = grid_data["y"]
                w = grid_data["width"]
                env = grid_data["env"]
                new_grid: BrickGrid = BrickGrid(x, y, w, self.state.brick_width, self.state.brick_height, env)
                new_grid.fill_with_data(grid_data["cells"])
                self.state.brick_grids.append(new_grid)


class SaveLevel(Command):
    def __init__(self, state):
        self.state: GameState = state

    def run(self):
        level = []
        for g in self.state.brick_grids:
            level.append({"x": g.x, "y": g.y, "width": g.width, "env": g.environment, "cells": g.cells})

        with open("level.json", mode="w", encoding="utf-8") as write_file:
            json.dump(level, write_file)


###############################################################################
#                                Rendering                                    #
###############################################################################
class GameStateObserver:
    def on_ball_created(self, ball):
        pass


class RenderingLayer(GameStateObserver):
    def render(self, surface):
        raise NotImplementedError()


class EntityLayer(RenderingLayer):
    def __init__(self):
        self.entities = []

    def on_ball_created(self, ball):
        self.entities.append(ball)

    def render(self, surface):
        # Render entities
        for e in self.entities:
            pygame.draw.rect(surface, 'white', e.rect)


class TileLayer(RenderingLayer):
    def __init__(self, grids):
        self.grids: list[BrickGrid] = grids
        files = ["tiles_dual_16_8_garden.png", "tiles_dual_16_8_bathroom.png"]
        self.tile_sets = []
        for f in files:
            i = pygame.image.load(f)
            i.set_colorkey((0, 0, 0))
            self.tile_sets.append(i)

    def render(self, surface):
        self.render_auto_tile(surface)
        return

    def render_auto_tile(self, surface: Surface):
        for g in self.grids:
            for x in range(-1, g.width):
                for y in range(-1, g.height):
                    draw_x = x * g.cell_width + g.x + (g.cell_width / 2)
                    draw_y = y * g.cell_height + g.y + (g.cell_height / 2)
                    draw_w = g.cell_width
                    draw_h = g.cell_height

                    value = g.get_cell(x, y)
                    value += g.get_cell(x + 1, y) * 2
                    value += g.get_cell(x, y + 1) * 4
                    value += g.get_cell(x + 1, y + 1) * 8

                    dest = Rect(draw_x, draw_y, draw_w, draw_h)
                    area = Rect(value * g.cell_width, 0, g.cell_width, g.cell_height)

                    surface.blit(self.tile_sets[g.environment], dest, area)


###############################################################################
#                                Game Modes                                   #
###############################################################################

class GameMode:
    def process_input(self):
        raise NotImplementedError()

    def update(self):
        raise NotImplementedError()

    def render(self, window):
        pass


class PlayGameMode(GameMode):
    def __init__(self, observer):
        # Observer
        self.observer = observer

        # Game state
        self.game_state = GameState()

        # Layers
        entity_layer = EntityLayer()
        self.game_state.add_observer(entity_layer)
        entity_layer.entities.append(self.game_state.paddle)

        tile_layer = TileLayer(self.game_state.brick_grids)

        self.rendering_layers = [tile_layer, entity_layer]
        self.viewport = Surface(self.game_state.area.size)

        # Controls
        self.paddle = self.game_state.paddle
        self.commands: list[Command] = []

    def process_input(self):
        # Pygame events (close & keyboard)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.observer.on_quit()
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.observer.on_quit()
                    break
                if event.key == pygame.K_p:
                    self.observer.on_edit()
                    break
                if event.key == pygame.K_UP:
                    self.commands.append(LaunchBallCommand(self.game_state))
                    break
        keys = pygame.key.get_pressed()
        move_direction = -keys[pygame.K_LEFT] + keys[pygame.K_RIGHT]

        # Keyboard controls the moves of the player's unit
        if move_direction != 0:
            command = PaddleMoveCommand(self.game_state, self.paddle, move_direction)
            self.commands.append(command)

        # Move balls
        self.commands.append(MoveBallsCommand(self.game_state))

        # Run Collisions
        self.commands.append(RunCollisionsCommand(self.game_state))

        # Apply gravity

    def update(self):
        for command in self.commands:
            command.run()
        self.commands.clear()

    def render(self, window):
        self.viewport.fill((0, 0, 0))

        for l in self.rendering_layers:
            l.render(self.viewport)


class EditorMode(GameMode):
    def __init__(self, observer, game_state):
        # Observer
        self.observer: UserInterface = observer

        # Game state
        self.game_state = game_state

        # Controls
        self.commands: list[Command] = []

        # Graphical User Interface
        self.selection_rect = Rect(0, 0, 0, 0)
        self.is_selecting = False
        self.selection_origin = Vector2(0, 0)

    def process_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.observer.on_quit()
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.observer.on_quit()
                    break
                elif event.key == pygame.K_p:
                    self.observer.on_play()
                    break
                elif event.key == pygame.K_s:
                    if event.mod & pygame.KMOD_CTRL:
                        self.commands.append(SaveLevel(self.game_state))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.is_selecting = True
                self.selection_origin = Vector2(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])
            elif event.type == pygame.MOUSEBUTTONUP:
                new_rect = self.selection_rect.copy()
                new_rect.x /= 3
                new_rect.y /= 3
                new_rect.w /= 3
                new_rect.h /= 3
                # value = self.game_state.brick_grid.get_cell_world(self.selection_origin / 3)
                self.commands.append(CreateBrickGrid(self.game_state, new_rect))
                self.selection_rect.update(0, 0, 0, 0)
                self.is_selecting = False

        # Selection Rectangle
        if self.is_selecting:
            x = min(self.selection_origin.x, pygame.mouse.get_pos()[0])
            y = min(self.selection_origin.y, pygame.mouse.get_pos()[1])
            w = abs(pygame.mouse.get_pos()[0] - self.selection_origin.x)
            h = abs(pygame.mouse.get_pos()[1] - self.selection_origin.y)
            self.selection_rect.update(x, y, w, h)

    def update(self):
        for command in self.commands:
            command.run()
        self.commands.clear()


###############################################################################
#                             User Interface                                  #
###############################################################################

class UserInterface:
    def __init__(self):
        pygame.init()

        # Rendering properties
        self.pixel_size = 3

        # Modes
        self.play_game_mode = PlayGameMode(self)
        self.editor_game_mode = EditorMode(self, self.play_game_mode.game_state)
        LoadLevel(self.play_game_mode.game_state).run()

        # Window
        self.window = pygame.display.set_mode(self.play_game_mode.viewport.get_rect().scale_by(3, 3).size)
        pygame.display.set_caption("Alexandre Szybiak - Breakout")

        # Loop properties
        self.clock = pygame.time.Clock()
        self.running = True

        # Start Mode
        self.paused = False

        # Init Ball
        InitBallCommand(self.play_game_mode.game_state).run()

    def on_quit(self):
        self.running = False

    def on_edit(self):
        self.paused = True

    def on_play(self):
        self.paused = False

    def run(self):
        while self.running:
            if self.paused:
                self.editor_game_mode.process_input()
                self.editor_game_mode.update()
            else:
                self.play_game_mode.process_input()
                self.play_game_mode.update()

            self.play_game_mode.render(self.window)

            # Draw Viewport
            self.window.blit(pygame.transform.scale_by(self.play_game_mode.viewport, self.pixel_size),
                             self.window.get_rect())

            # Draw Graphical User Interface
            pygame.draw.rect(self.window, "green", self.editor_game_mode.selection_rect, 1)
            pygame.display.update()
            self.clock.tick(60)


userInterface = UserInterface()
userInterface.run()

pygame.quit()
