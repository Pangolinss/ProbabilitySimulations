import pygame
import numpy as np
import imageio

WIDTH, HEIGHT = 800, 200
BLOCK_WIDTH = 10
BLOCK_HEIGHT = 10
SPACING = 10
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ballistic Deposition")
clock = pygame.time.Clock()

BG_COLOR =  (25, 20,30)

class Block(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.v = 1
        self.color = (255,255,255)
        self.alive = True


def intersect(block1, block2):
    x1 = block1.x
    y1 = block1.y
    x2 = block2.x
    y2 = block2.y
    if (abs(x1 - x2) == BLOCK_WIDTH):
        return (y1 == y2)
    else:
        return((abs(y1 - y2) <= BLOCK_HEIGHT) and (abs(x1- x2) < BLOCK_WIDTH))
def brighten(color, factor):
    r, g, b = color
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return (r, g, b)

blocks = []
running = True
while running:
    delta_t = clock.tick(120)/1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill(BG_COLOR)

    n = np.random.poisson(0.2)
    for i in range(n):
        blocks.append(Block(np.random.randint(0, WIDTH/SPACING)*SPACING , 0))
    for block in blocks:
        if block.alive:
            block.y += block.v 
            if block.y >= HEIGHT - BLOCK_HEIGHT:
                block.y = HEIGHT - BLOCK_HEIGHT
                block.alive = False
            else:
                for other in blocks:
                    if other is not block and not other.alive and (intersect(block, other)):
                        if (abs(block.x - other.x) == BLOCK_WIDTH) and (block.y == other.y):
                            block.alive = False
                            break
                        block.y = other.y - BLOCK_HEIGHT
                        block.alive = False
                        break 

    for block in blocks:
        if (block.alive):
            pygame.draw.rect(screen, (255,255,255), (block.x, block.y, BLOCK_WIDTH, BLOCK_HEIGHT))
        else:
            pygame.draw.rect(screen, brighten((117,187,220), HEIGHT/block.y), (block.x, block.y, BLOCK_WIDTH, BLOCK_HEIGHT))

    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

