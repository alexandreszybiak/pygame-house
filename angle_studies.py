import pygame
from pygame import Rect, Vector2

# pygame setup
pygame.init()
screen = pygame.display.set_mode((400,400))

clock = pygame.time.Clock()

running = True



while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            pass
        if event.type == pygame.QUIT:
            running = False

    angle = 0
    origin = Vector2(0, 0)

    vector = Vector2(0.5, 0.5)

    r_angle = origin.angle_to(vector)

    #pygame.draw.line(screen, "white", point_a, point_b)

    # flip() the display to put your work on screen
    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()
