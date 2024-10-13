# Example file showing a basic pygame "game loop"
import pygame

# param
resolution = (160,160)
pixel_size = 3

# pygame setup
pygame.init()
screen = pygame.display.set_mode((resolution[0] * pixel_size, resolution[1] * pixel_size))
viewport = pygame.Surface(resolution)
clock = pygame.time.Clock()
running = True

wall = pygame.image.load('wall.png').convert()

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # fill the screen with a color to wipe away anything from last frame
    viewport.fill(0x656565)

    # RENDER YOUR GAME HERE
    viewport.blit(wall, wall.get_rect())

    # flip() the display to put your work on screen
    screen.blit(pygame.transform.scale_by(viewport, 3), screen.get_rect())

    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()