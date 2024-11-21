import os
import json
from math import copysign, floor, ceil

import pygame
from pygame import Rect, Color
from pygame.math import Vector2
from pygame.surface import Surface

os.environ['SDL_VIDEO_CENTERED'] = '1'


###############################################################################
#                                 Engine                                      #
###############################################################################

class Cell:
    def __init__(self, alive=True):
        self.alive = alive

    def __int__(self):
        return int(self.alive)

    def __bool__(self):
        return self.alive


class Brick(Cell):
    def __init__(self):
        super().__init__()


class Grid:
    error_cell: Cell = Cell(False)
    cell: Cell = Cell()

    def __init__(self, x: int, y: int, width: int, cell_width: int, cell_height: int):
        self.x = x
        self.y = y
        self.width: int = width
        self.cells: list[Cell] = []
        self.cell_width: int = cell_width
        self.cell_height: int = cell_height
        self._dirty = False

    def set_dirty(self):
        self._dirty = True

    def fill(self, value):
        pass

    def fill_with_data(self, data):
        self.cells = data

    @property
    def height(self):
        return len(self.cells) // self.width

    def get_rect(self) -> Rect:
        return Rect(self.x, self.y, self.width * self.cell_width, self.height * self.cell_height)

    # Cell-related Methods
    def get_cell_coordinates(self, world_x, world_y):
        x = (world_x - self.x) // self.cell_width
        y = (world_y - self.y) // self.cell_height
        return x, y

    def get_cell(self, x, y) -> Cell:
        if x >= self.width or x < 0:
            return Grid.error_cell
        if y >= self.height or y < 0:
            return Grid.error_cell
        index: int = x + y * self.width
        cell: Cell = self.cells[index]
        return cell

    def kill_cell(self, x: int, y: int):
        if x < 0 or x >= self.width: return
        if y < 0 or y >= self.height: return
        index = x + y * self.width
        if 0 <= index < len(self.cells):
            self.cells[index].alive = False
            self.set_dirty()

    def kill_cell_world(self, pos: Vector2):
        x = int(pos.x) - self.x
        y = int(pos.y) - self.y
        self.kill_cell(x // self.cell_width, y // self.cell_height)

    def is_cell_alive(self, x: int, y: int) -> bool:
        if x >= self.width or x < 0 or y >= self.height or y < 0:
            return False
        return self.cells[x + y * self.width].alive

    def is_cell_alive_world(self, pos: Vector2) -> bool:
        x = pos.x - self.x
        y = pos.y - self.y
        return self.is_cell_alive(int(x // self.cell_width), int(y // self.cell_height))

    # Region
    def get_region_coordinate_and_cells(self, x1, y1, x2, y2) -> list[tuple[int, int, Cell]]:
        cells: list[tuple[int, int, Cell]] = []
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                cells.append((x, y, self.get_cell(x, y)))
        return cells

    # Rows and Column
    def get_row(self, row) -> list[Cell]:
        return [c for c in self.cells[row * self.width: row * self.width + self.width] if not c.alive]

    def get_column(self, column) -> list[Cell]:
        return [c for c in self.cells[column::self.width] if not c.alive]


###############################################################################
#                               Game State                                    #
###############################################################################
class BrickGrid(Grid):
    environment_count = 3

    def __init__(self, x, y, width, cell_width, cell_height, environment):
        super().__init__(x, y, width, cell_width, cell_height)
        self.environment = environment

    def collide_point(self, point: Vector2) -> bool:
        return self.is_cell_alive_world(point)

    def trim(self):
        if not self._dirty:
            return

        pygame.image.save(pygame.display.get_surface(), "breakute.png")

        # Trim Grid from Top
        cells_to_delete = []
        for i in range(self.height):
            row = self.get_row(i)
            if len(row) < self.width:
                break
            cells_to_delete.extend(row)
            self.y += self.cell_height
        for c in cells_to_delete:
            self.cells.remove(c)

        # Trim Grid from Bottom
        cells_to_delete = []
        for i in reversed(range(self.height)):
            row = self.get_row(i)
            if len(row) < self.width:
                break
            cells_to_delete.extend(row)
        for c in cells_to_delete:
            self.cells.remove(c)

        # Trim Grid from Left
        cells_to_delete = []
        for i in range(self.width):
            col = self.get_column(i)
            if len(col) < self.height:
                break
            cells_to_delete.extend(col)
            self.x += self.cell_width
            self.width -= 1
        for c in cells_to_delete:
            self.cells.remove(c)

        # Trim Grid from Right
        cells_to_delete = []
        for i in reversed(range(self.width)):
            col = self.get_column(i)
            if len(col) < self.height:
                break
            cells_to_delete.extend(col)
            self.width -= 1
        for c in cells_to_delete:
            self.cells.remove(c)

        self._dirty = False


class GameStateObserver:
    def on_ball_created(self, ball):
        pass

    def on_ball_lost(self, ball):
        pass

    def on_balls_cleared(self):
        pass

    def on_last_ball_lost(self):
        pass

    def on_last_brick_destroyed(self):
        pass

    def on_brick_grid_destroyed(self, brick_grid: BrickGrid):
        pass


class GameState:
    def __init__(self):
        self.level_index = 0
        self.area = Rect(0, 0, 160, 240)
        self.paddle: Paddle = Paddle(Vector2(0, 200))
        self.paddle.rect.centerx = self.area.centerx
        self.balls: list[Ball] = []
        self.brick_grids: list[BrickGrid] = []
        self.collisions: list[Collision] = []
        self.powerups: list[PowerUp] = []
        self.brick_width = 16
        self.brick_height = 8
        self.observers: list[GameStateObserver] = []
        self._is_level_dirty = False

    def add_observer(self, observer: GameStateObserver):
        self.observers.append(observer)

    def notify_ball_created(self, ball):
        print("Ball Created")
        for observer in self.observers:
            observer.on_ball_created(ball)

    def notify_ball_lost(self, ball):
        print("Ball Lost")
        for observer in self.observers:
            observer.on_ball_lost(ball)

    def notify_balls_cleared(self):
        print("All Balls Destroyed")
        for observer in self.observers:
            observer.on_balls_cleared()

    def notify_last_ball_lost(self):
        for observer in self.observers:
            observer.on_last_ball_lost()

    def notify_last_brick_destroyed(self):
        print("Last Brick Destroyed")
        for observer in self.observers:
            observer.on_last_brick_destroyed()

    def notify_brick_grid_destroyed(self, brick_grid: BrickGrid):
        print("Brick Grid Destroyed")
        for observer in self.observers:
            observer.on_brick_grid_destroyed(brick_grid)


class Entity:
    def __init__(self, position):
        self.position = position
        self.velocity = Vector2(0, 0)
        self.rect: Rect = Rect(0, 0, 1, 1)
        self.movement_remainder = Vector2()
        self.alive = True

    def set_alive(self, value: bool):
        self.alive = value


class Ball(Entity):
    def __init__(self, position):
        super().__init__(position)
        self.rect = Rect(position.x, position.y, 4, 4)
        self.is_stuck_on_paddle = False


class Paddle(Entity):
    speed = 2

    def __init__(self, position: Vector2):
        super().__init__(position)
        self.rect = Rect(position.x, position.y, 40, 4)


class Effect:

    def activate(self, game_state: GameState):
        for b in game_state.balls[:]:
            pos = b.rect
            velocity = b.velocity

            new_ball = Ball(Vector2(pos.x, pos.y))
            new_ball.velocity = velocity.rotate(-10)
            game_state.balls.append(new_ball)
            game_state.notify_ball_created(new_ball)

            new_ball = Ball(Vector2(pos.x, pos.y))
            new_ball.velocity = velocity.rotate(10)
            game_state.balls.append(new_ball)
            game_state.notify_ball_created(new_ball)


class PowerUp(Entity):
    move_speed = 1

    def __init__(self, position: Vector2):
        super().__init__(position)
        self.rect = Rect(position.x, position.y, 10, 6)
        self.velocity = Vector2(0, PowerUp.move_speed)
        self.effect: Effect = Effect()


class Collision:
    def __init__(self, state: GameState, collider: Entity, axis: Vector2):
        self.state = state
        self.collider = collider
        self.axis = axis

    def process(self):
        raise NotImplementedError()


class GridCollision(Collision):
    def __init__(self, state: GameState, collider: Entity, axis: Vector2, brick_grid: BrickGrid, hit_cells):
        super().__init__(state, collider, axis)
        self.brick_grid = brick_grid
        self.hit_cells = hit_cells

    def process(self):
        for c in self.hit_cells:
            brick: Brick = c[2]
            self.brick_grid.kill_cell(c[0], c[1])

        # Create PowerUp
        if len(self.state.balls) == 1 and not self.state.powerups:
            self.state.powerups.append(
                PowerUp(Vector2(self.brick_grid.get_rect().centerx, self.brick_grid.get_rect().bottom)))

        self.brick_grid.set_dirty()
        self.state._is_level_dirty = True


class BallCollision(Collision):
    def __init__(self, state: GameState, collider: Entity, axis: Vector2):
        super().__init__(state, collider, axis)

    def process(self):
        self.collider.velocity.reflect_ip(self.axis)


class BallCollisionWithPaddle(Collision):
    def __init__(self, state: GameState, collider: Entity, axis: Vector2, paddle: Paddle):
        super().__init__(state, collider, axis)
        self.paddle = paddle

    def process(self):
        # Bounce
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


class CheckForPowerUpCommand(Command):
    def __init__(self, state: GameState):
        self.state = state

    def run(self):
        for p in self.state.powerups[:]:
            if self.state.paddle.rect.colliderect(p):
                p.effect.activate(self.state)
                self.state.powerups.remove(p)
            elif p.rect.top > self.state.area.bottom:
                self.state.powerups.remove(p)


class PaddleMoveCommand(Command):
    def __init__(self, state, paddle, move_amount):
        self.state: GameState = state
        self.paddle: Paddle = paddle
        self.move_amount = move_amount

    def run(self):
        self.paddle.rect.move_ip(self.move_amount, 0)
        self.paddle.rect.clamp_ip(self.state.area)
        for b in self.state.balls:
            if self.paddle.rect.colliderect(b):
                b.rect.bottom = self.paddle.rect.top


class MovePowerUpsCommand(Command):
    def __init__(self, state):
        self.state: GameState = state

    def run(self):
        for p in self.state.powerups:
            p.rect.move_ip(p.velocity)


class InitBallCommand(Command):
    def __init__(self, state: GameState):
        self.state = state

    def run(self):
        new_ball = Ball(Vector2(0, 0))
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
            if not self.state.area.colliderect(b.rect):
                self.state.notify_ball_lost(b)
                self.state.balls.remove(b)

    def collide_x(self, ball: Ball, x_direction):
        axis = Vector2(1, 0)
        next_rect = ball.rect.move(x_direction, 0)

        # Paddle
        if self.state.paddle is not None and next_rect.colliderect(self.state.paddle):
            self.state.collisions.append(BallCollision(self.state, ball, axis))
            return True

        # Area Boundaries
        if not self.state.area.contains(next_rect):
            self.state.collisions.append(BallCollision(self.state, ball, axis))
            return True

        # Grids
        collide = False
        x = next_rect.left if x_direction < 0 else next_rect.right
        grids: list[tuple[BrickGrid, tuple[int, int]]] = []
        for grid in self.state.brick_grids:
            cell_1 = grid.get_cell_coordinates(x, next_rect.top)
            cell_2 = grid.get_cell_coordinates(x, next_rect.bottom)
            cells = grid.get_region_coordinate_and_cells(cell_1[0], cell_1[1], cell_2[0], cell_2[1])

            hit_cells = [c for c in cells if c[2].alive]

            if hit_cells:
                self.state.collisions.append(GridCollision(self.state, ball, axis, grid, hit_cells))
                collide = True

        if collide:
            self.state.collisions.append(BallCollision(self.state, ball, axis))

        return collide

    def collide_y(self, ball, y_direction):
        axis = Vector2(0, 1)
        collide = False
        ball_rect = ball.rect.move(0, y_direction)

        # Paddle
        if self.state.paddle is not None and ball_rect.colliderect(self.state.paddle):
            self.state.collisions.append(BallCollisionWithPaddle(self.state, ball, axis, self.state.paddle))
            return True

        # Area Boundaries
        if ball_rect.top < self.state.area.top:
            self.state.collisions.append(BallCollision(self.state, ball, axis))
            return True

        # Grids
        y = ball_rect.top if y_direction < 0 else ball_rect.bottom
        for g in self.state.brick_grids:
            cell_1 = g.get_cell_coordinates(ball_rect.left, y)
            cell_2 = g.get_cell_coordinates(ball_rect.right, y)
            cells = g.get_region_coordinate_and_cells(cell_1[0], cell_1[1], cell_2[0], cell_2[1])

            hit_cells = [c for c in cells if c[2].alive]

            if hit_cells:
                self.state.collisions.append(GridCollision(self.state, ball, axis, g, hit_cells))
                collide = True

        if collide:
            self.state.collisions.append(BallCollision(self.state, ball, axis))

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


class DestroyBrickCommand(Command):
    def __init__(self, brick_grids: list[BrickGrid], position: Vector2):
        self.brick_grids = brick_grids
        self.position = position

    def run(self):
        for bg in self.brick_grids:
            bg.kill_cell_world(self.position)


class EditBrickGrid(Command):
    def __init__(self, state, value, rect):
        self.state: GameState = state
        self.value = value
        self.rect: Rect = rect

    def run(self):
        pass


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
        new_grid.cells = [Brick() for _ in range(w * h)]
        self.state.brick_grids.append(new_grid)


class DestroyBrickGridCommand(Command):
    def __init__(self, game_state: GameState, brick_grid: BrickGrid):
        self.game_state: GameState = game_state
        self.brick_grid = brick_grid

    def run(self):
        self.game_state.brick_grids.remove(self.brick_grid)


class BrickGridMaintenanceCommand(Command):
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def run(self):
        if not self.game_state._is_level_dirty:
            return
        for bg in self.game_state.brick_grids[:]:
            bg.trim()
            if not bg.cells:
                self.game_state.brick_grids.remove(bg)
                self.game_state.notify_brick_grid_destroyed(bg)

        self.game_state._is_level_dirty = False


class CheckForEndOfLevelCommand(Command):
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def run(self):
        # If no more brick grids, send a notification
        if not self.game_state.brick_grids:
            self.game_state.notify_last_brick_destroyed()


class ChangeLevelIndex(Command):
    def __init__(self, state: GameState, increment: int):
        self.state = state
        self.increment = increment

    def run(self):
        self.state.level_index += self.increment


class UnloadLevelCommand(Command):
    def __init__(self, state: GameState):
        self.state = state

    def run(self):
        self.state.brick_grids.clear()


class ClearBallsCommand(Command):
    def __init__(self, state: GameState):
        self.state = state

    def run(self):
        for b in self.state.balls:
            b.set_alive(False)
        self.state.balls.clear()
        self.state.notify_balls_cleared()


class LoadLevelCommand(Command):
    def __init__(self, state):
        self.state: GameState = state

    def run(self):
        level_name: str = "level_" + str(self.state.level_index).zfill(2) + ".json"
        try:
            file = open(level_name, mode="r", encoding="utf-8")
            level = json.load(file)
            for brick_grid in level:
                x = brick_grid["x"]
                y = brick_grid["y"]
                w = brick_grid["width"]
                env = brick_grid["env"]
                new_grid: BrickGrid = BrickGrid(x, y, w, self.state.brick_width, self.state.brick_height, env)
                for count, value in enumerate(brick_grid["cells"]):
                    new_grid.cells.append(Brick())
                self.state.brick_grids.append(new_grid)
        except OSError as error:
            print("OS error:", error)


class SaveLevelCommand(Command):
    def __init__(self, state):
        self.state: GameState = state

    def run(self):
        level_name: str = "level_" + str(self.state.level_index).zfill(2) + ".json"
        level = []
        for g in self.state.brick_grids:
            # Convert Cell into int
            cells: list[int] = [int(c) for c in g.cells]
            level.append({"x": g.x, "y": g.y, "width": g.width, "env": g.environment, "cells": cells})

        try:
            write_file = open(level_name, mode="w", encoding="utf-8")
            json.dump(level, write_file, indent=4)
        except OSError as error:
            print("OS error:", error)


class ChangeBrickGridEnvironmentCommand(Command):
    def __init__(self, brick_grid: list[BrickGrid], increment: int):
        self.brickGrid: list[BrickGrid] = brick_grid
        self.increment = increment

    def run(self):
        for bg in self.brickGrid:
            bg.environment = abs(bg.environment + self.increment) % bg.environment_count


###############################################################################
#                                Rendering                                    #
###############################################################################
class Viewport:
    def __init__(self, size, scale):
        self.surface: Surface = Surface(size)
        self.scale: int = scale

    def clear(self):
        self.surface.fill(0x326441)

    @property
    def display_size(self) -> tuple[int, int]:
        rect = self.surface.get_rect()
        return rect.width * self.scale, rect.height * self.scale

    @property
    def mouse_x(self) -> int:
        return pygame.mouse.get_pos()[0] // self.scale

    @property
    def mouse_y(self) -> int:
        return pygame.mouse.get_pos()[1] // self.scale

    @property
    def mouse(self) -> Vector2:
        return Vector2(self.mouse_x, self.mouse_y)

    def render(self, window: Surface):
        window.blit(pygame.transform.scale_by(self.surface, self.scale), window.get_rect())


class RenderingLayer(GameStateObserver):
    def render(self, viewport: Viewport):
        raise NotImplementedError()


class EntityLayer(RenderingLayer):
    def __init__(self):
        self.entities: list[Entity] = []

    def on_ball_created(self, ball):
        self.entities.append(ball)

    def on_ball_lost(self, ball):
        self.entities.remove(ball)

    def on_balls_cleared(self):
        self.entities = [e for e in self.entities if e.alive]

    def render(self, viewport: Viewport):
        # Render entities
        for e in self.entities:
            pygame.draw.rect(viewport.surface, 'white', e.rect)


class TileLayer(RenderingLayer):
    def __init__(self, grids):
        self.grids: list[BrickGrid] = grids  # This is a reference to the game state list of Brick Grids
        files = ["tiles_dual_16_8_forest.png"]
        self.tile_sets = []
        for f in files:
            i = pygame.image.load(f)
            i.set_colorkey((0, 0, 0))
            self.tile_sets.append(i)

    def render(self, viewport: Viewport):
        self.render_auto_tile(viewport)
        return

    def render_auto_tile(self, viewport: Viewport):
        for g in self.grids:
            for x in range(-1, g.width):
                for y in range(-1, g.height):
                    draw_x = x * g.cell_width + g.x + (g.cell_width / 2)
                    draw_y = y * g.cell_height + g.y + (g.cell_height / 2)
                    draw_w = g.cell_width
                    draw_h = g.cell_height

                    value = int(g.is_cell_alive(x, y))
                    value += int(g.is_cell_alive(x + 1, y)) * 2
                    value += int(g.is_cell_alive(x, y + 1)) * 4
                    value += int(g.is_cell_alive(x + 1, y + 1)) * 8

                    if value == 0:
                        continue

                    value -= 1

                    dest = Rect(draw_x, draw_y, draw_w, draw_h)
                    area = Rect(value * g.cell_width, g.environment * g.cell_height, g.cell_width, g.cell_height)

                    viewport.surface.blit(self.tile_sets[0], dest, area)


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


class PlayGameMode(GameMode, GameStateObserver):
    def __init__(self, observer):
        # Observer
        self.observer = observer

        # Game state
        self.game_state = GameState()
        self.game_state.add_observer(self)

        # Entity Layers
        paddle_layer = EntityLayer()
        paddle_layer.entities.append(self.game_state.paddle)

        ball_layer = EntityLayer()
        ball_layer.entities = self.game_state.balls

        powerups_layer = EntityLayer()
        powerups_layer.entities = self.game_state.powerups

        tile_layer = TileLayer(self.game_state.brick_grids)

        self.rendering_layers = [tile_layer, paddle_layer, ball_layer, powerups_layer]
        self.viewport: Viewport = Viewport(self.game_state.area.size, 3)

        # Controls
        self.paddle = self.game_state.paddle
        self.commands: list[Command] = []

        #
        self.level_clear = False

    def process_input(self):
        pressed_launch = False
        move_amount = 0

        # Pygame events (close & keyboard)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.observer.on_quit()
                break
            elif event.type == pygame.KEYDOWN:
                pygame.event.set_grab(False)
                if event.key == pygame.K_ESCAPE:
                    self.observer.on_quit()
                    break
                if event.key == pygame.K_p:
                    self.observer.on_edit()
                    break
                if event.key == pygame.K_UP:
                    pressed_launch = True
                    break
                if event.key == pygame.K_DOWN:
                    self.commands.append(ClearBallsCommand(self.game_state))
                    break
            elif event.type == pygame.MOUSEMOTION:
                pygame.event.set_grab(True)
            elif event.type == pygame.MOUSEBUTTONUP:
                pressed_launch = True

        keys = pygame.key.get_pressed()

        if not pygame.event.get_grab():
            move_amount = (-keys[pygame.K_LEFT] + keys[pygame.K_RIGHT]) * Paddle.speed
        else:
            move_amount = pygame.mouse.get_rel()[0] / 3

        if self.level_clear:
            self.level_clear = False
            self.commands.append(ClearBallsCommand(self.game_state))
            self.commands.append(ChangeLevelIndex(self.game_state, 1))
            self.commands.append(UnloadLevelCommand(self.game_state))
            self.commands.append(LoadLevelCommand(self.game_state))
            return

        # Init Ball
        if not self.game_state.balls:
            InitBallCommand(self.game_state).run()

        # Move the Paddle
        if move_amount != 0:
            command = PaddleMoveCommand(self.game_state, self.paddle, move_amount)
            self.commands.append(command)

        # Launch Ball
        if pressed_launch:
            self.commands.append(LaunchBallCommand(self.game_state))

        # Move balls
        self.commands.append(MoveBallsCommand(self.game_state))

        # Move PowerUps
        self.commands.append(MovePowerUpsCommand(self.game_state))

        # Process collisions
        self.commands.append(RunCollisionsCommand(self.game_state))

        # Check for PowerUp contact
        self.commands.append(CheckForPowerUpCommand(self.game_state))

        # Apply gravity

        # Maintenance
        self.commands.append(BrickGridMaintenanceCommand(self.game_state))

        # End Check
        self.commands.append(CheckForEndOfLevelCommand(self.game_state))

    def update(self):
        for command in self.commands:
            command.run()
        self.commands.clear()

    def render(self, window):
        self.viewport.clear()

        for l in self.rendering_layers:
            l.render(self.viewport)

    def on_last_ball_lost(self):
        pass

    def on_last_brick_destroyed(self):
        self.level_clear = True


class EditorMode(GameMode, GameStateObserver):
    def __init__(self, observer, game_state, play_game_mode: PlayGameMode):
        # Observer
        self.observer: UserInterface = observer

        # Game state
        self.game_state: GameState = game_state

        # Reference to the main game mode
        self.play_game_mode: PlayGameMode = play_game_mode

        # Observe the GameState
        self.game_state.add_observer(self)

        # Controls
        self.commands: list[Command] = []

        #
        self.hovered_brick_grid: list[BrickGrid] = []

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
                elif event.key == pygame.K_BACKSPACE:
                    self.commands.append(
                        DestroyBrickCommand(self.hovered_brick_grid, self.play_game_mode.viewport.mouse))
                elif event.key == pygame.K_DELETE:
                    bg = self.hovered_brick_grid.pop()
                    self.commands.append(DestroyBrickGridCommand(self.game_state, bg))
                elif event.key == pygame.K_LEFT:
                    self.commands.append(ChangeLevelIndex(self.game_state, -1))
                    self.commands.append(UnloadLevelCommand(self.game_state))
                    self.commands.append(LoadLevelCommand(self.game_state))
                elif event.key == pygame.K_RIGHT:
                    self.commands.append(ChangeLevelIndex(self.game_state, 1))
                    self.commands.append(UnloadLevelCommand(self.game_state))
                    self.commands.append(LoadLevelCommand(self.game_state))
                elif event.key == pygame.K_UP:
                    self.commands.append(ChangeBrickGridEnvironmentCommand(self.hovered_brick_grid, 1))
                elif event.key == pygame.K_DOWN:
                    self.commands.append(ChangeBrickGridEnvironmentCommand(self.hovered_brick_grid, -1))
                elif event.key == pygame.K_p:
                    self.observer.on_play()
                    break
                elif event.key == pygame.K_s:
                    if event.mod & pygame.KMOD_CTRL:
                        self.commands.append(SaveLevelCommand(self.game_state))
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
            elif event.type == pygame.MOUSEMOTION:
                self.hovered_brick_grid.clear()
                for bg in self.game_state.brick_grids:
                    if bg.collide_point(self.play_game_mode.viewport.mouse):
                        self.hovered_brick_grid.append(bg)
                        break

        # Selection Rectangle
        if self.is_selecting:
            x = min(self.selection_origin.x, pygame.mouse.get_pos()[0])
            y = min(self.selection_origin.y, pygame.mouse.get_pos()[1])
            w = abs(pygame.mouse.get_pos()[0] - self.selection_origin.x)
            h = abs(pygame.mouse.get_pos()[1] - self.selection_origin.y)
            self.selection_rect.update(x, y, w, h)

        # Trim
        self.commands.append(BrickGridMaintenanceCommand(self.game_state))

    def update(self):
        for command in self.commands:
            command.run()
        self.commands.clear()

    def on_brick_grid_destroyed(self, brick_grid: BrickGrid):
        self.hovered_brick_grid.clear()


###############################################################################
#                             User Interface                                  #
###############################################################################

class UserInterface:
    def __init__(self):
        pygame.init()

        # Rendering properties
        pixel_size = 3

        # Modes
        self.play_game_mode = PlayGameMode(self)
        self.editor_mode = EditorMode(self, self.play_game_mode.game_state, self.play_game_mode)
        LoadLevelCommand(self.play_game_mode.game_state).run()

        # Window
        self.window = pygame.display.set_mode(self.play_game_mode.viewport.display_size)
        pygame.display.set_caption("Alexandre Szybiak - Breakout")

        # GUI Surface
        self.gui_surface = Surface((self.window.get_width(), self.window.get_height()), pygame.SRCALPHA)

        # Loop properties
        self.clock = pygame.time.Clock()
        self.running = True

        # Start Mode
        self.paused = False

    def on_quit(self):
        self.running = False

    def on_edit(self):
        self.paused = True

    def on_play(self):
        self.paused = False

    def run(self):
        while self.running:
            if self.paused:
                self.editor_mode.process_input()
                self.editor_mode.update()
            else:
                self.play_game_mode.process_input()
                self.play_game_mode.update()

            self.play_game_mode.render(self.window)

            # Reset window
            self.window.fill((0, 0, 0))

            # Draw Game Viewport
            self.play_game_mode.viewport.render(self.window)

            # Draw Editor Graphical User Interface
            if self.paused:
                self.gui_surface.fill((0, 0, 0, 0))

                # Grid
                col_count = self.play_game_mode.game_state.area.width // self.play_game_mode.game_state.brick_width
                line_count = self.play_game_mode.game_state.area.height // self.play_game_mode.game_state.brick_height
                col_gap = self.window.get_rect().width / col_count
                line_gap = self.window.get_rect().height / line_count
                col = Color(0, 255, 0, 64)
                for x in range(col_count):
                    pygame.draw.line(self.gui_surface, col, (x * col_gap, 0),
                                     (x * col_gap, self.window.get_rect().height))
                for y in range(line_count):
                    pygame.draw.line(self.gui_surface, col, (0, y * line_gap),
                                     (self.window.get_rect().width, y * line_gap))
                # Selection Rectangle
                pygame.draw.rect(self.gui_surface, "green", self.editor_mode.selection_rect, 1)

                # Hovered Brick Grid
                for bg in self.editor_mode.hovered_brick_grid:
                    rect = bg.get_rect()
                    rect.x *= 3
                    rect.y *= 3
                    rect.w *= 3
                    rect.h *= 3
                    pygame.draw.rect(self.gui_surface, "green", rect, 2)

                self.window.blit(self.gui_surface, (0, 0))

            pygame.display.update()
            self.clock.tick(60)


userInterface = UserInterface()
userInterface.run()

pygame.quit()
