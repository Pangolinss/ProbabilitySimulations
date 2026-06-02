import pygame
import numpy as np
import imageio
import bisect 

WIDTH, HEIGHT = 800, 400
BLOCK_WIDTH = 4
BLOCK_HEIGHT = 4
SPACING = 4
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
        self.gone = False


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

deadblocks = []
blocks = []
running = True

capture_frames = True
frames = []
MAX_VIDEO_FRAMES = 6000
VIDEO_FPS = 60
VIDEO_FILENAME = "animation.mp4"


while running:
    delta_t = clock.tick(120)/1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill(BG_COLOR)

    n = np.random.poisson(3)
    new_blocks = []
    gone_index = []
    for i in range(n):
        new_blocks = Block(np.random.randint(0, WIDTH/SPACING)*SPACING , 0)
        if gone_index != []:
            blocks[-gone_index[-1]] = new_blocks
            gone_index = gone_index[:-1]
        else:
            blocks.append(new_blocks)
    for j in range(5):
        k =0
        for block in blocks:
            if block.alive:
                block.y += block.v 
                if block.y >= HEIGHT - BLOCK_HEIGHT:
                    if (block.x <350) or (block.x > 450):
                        block.gone = True
                        bisect.insort(gone_index, -k)
                    else:
                        block.y = HEIGHT - BLOCK_HEIGHT
                        block.alive = False
                        deadblocks.append(block)
                        block.gone = True
                        bisect.insort(gone_index, -k)


                else:
                    for other in deadblocks:
                        if (intersect(block, other)):
                            if (abs(block.x - other.x) == BLOCK_WIDTH) and (block.y == other.y):
                                block.alive = False
                                deadblocks.append(block)
                                block.gone = True
                                bisect.insort(gone_index, -k)
                                break
                            block.y = other.y - BLOCK_HEIGHT
                            block.alive = False
                            deadblocks.append(block)
                            block.gone = True
                            bisect.insort(gone_index, -k)
                            break 
        k += 1

    for block in blocks:
        ratio = 0
        if (block.y != 0):
            ratio = HEIGHT/block.y
        else:
            ratio = HEIGHT/0.01
        if (block.gone is False):
            if (block.alive):
                pygame.draw.rect(screen, (150,150,150), (block.x, block.y, BLOCK_WIDTH, BLOCK_HEIGHT))
            else:
                pygame.draw.rect(screen, brighten((117,187,220), ratio), (block.x, block.y, BLOCK_WIDTH, BLOCK_HEIGHT))
    for block in deadblocks:
        if (block.y != 0):
            ratio = HEIGHT/block.y
        else:
            ratio = HEIGHT/0.01
        pygame.draw.rect(screen, brighten((117,187,220), ratio), (block.x, block.y, BLOCK_WIDTH, BLOCK_HEIGHT))

    # Update the display
    if capture_frames and len(frames) < MAX_VIDEO_FRAMES:
        frame = pygame.surfarray.array3d(screen)
        frame = np.transpose(frame, (1, 0, 2))
        frames.append(frame)
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

if capture_frames and frames:
    try:
        with imageio.get_writer(
            VIDEO_FILENAME,
            fps=VIDEO_FPS,
            codec="libx264",
            ffmpeg_params=["-pix_fmt", "yuv420p"],
        ) as writer:
            for frame in frames:
                writer.append_data(frame)
        print(f"Saved {len(frames)} frames to {VIDEO_FILENAME}")
    except Exception as e:
        print(f"Failed to save MP4: {e}")

