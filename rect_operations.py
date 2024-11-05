import pygame
from pygame import Rect

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

    rect1 = Rect(0,0,200,200)
    rect1.center = screen.get_rect().center

    rect2 = Rect(0, 0, 120, 120)
    rect2.topleft = screen.get_rect().center

    rect3 = rect2.clamp(rect1)

    pygame.draw.rect(screen, "green", rect1, 1)
    pygame.draw.rect(screen, "blue", rect2, 1)
    pygame.draw.rect(screen, "yellow", rect3, 1)

    # flip() the display to put your work on screen
    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()
