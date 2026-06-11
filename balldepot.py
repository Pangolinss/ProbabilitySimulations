import pygame
import numpy as np
import imageio
import bisect 

#WIDTH, HEIGHT = 1750, 1000
WIDTH, HEIGHT = 1000, 800
BLOCK_WIDTH = 50
BLOCK_HEIGHT = 50
SPACING = 50
V_MIN = 5
V_MAX = 6
RATE = 0.05
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ballistic Deposition")
clock = pygame.time.Clock()

#BG_COLOR = (57,42,57)
BG_COLOR = (25, 20,30)
ENABLE_BM = False
ENABLE_RANDOMSPEED = False
HAS_INITIAL = False
#initial types: circle image
INITIAL_TYPE = "image"
CIRCLE_CENTRE = (500,600)
CIRCLE_RADIUS = 150

class Block(object):
    def __init__(self, x, y, v):
        self.x = x
        self.y = y
        self.v = v
        self.color = (255,255,255)
        self.alive = True
        self.gone = False
        self.type = np.random.randint(3,6)


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

def interval(box1, box2):
    return (box2[0] <= box1[1] <= box2[1]) or (box2[0] <= box2[1] <= box2[1])
def isOverLapBox(box1, box2):
    return interval( (box1[0], box1[2]), (box2[0], box2[2]) ) and interval((box1[1], box1[3]),(box2[1], box2[3]))

def expand_box(x,y, bounding_box):
    if isOverLapBox( (x, y, x+BLOCK_WIDTH, y+BLOCK_HEIGHT), bounding_box ):
        if (x <= bounding_box[0]):
            bounding_box[0] = x
        if (x + BLOCK_WIDTH >= bounding_box[2]):
            bounding_box[2] = x + BLOCK_WIDTH
        if (y <= bounding_box[1]):
            bounding_box[1] = y
        if (y+BLOCK_HEIGHT >= bounding_box[3]):
            bounding_box[3] = y + BLOCK_HEIGHT 
        return bounding_box

def add_deadzone(x, y, deadzone, occupied):
    # Add all points in the row directly above the block
    for px in range(x-BLOCK_WIDTH+1, x + BLOCK_WIDTH):
        if not((px, y-BLOCK_HEIGHT) in occupied):
            deadzone[(px, y-BLOCK_HEIGHT)] = True
    if not((x-BLOCK_WIDTH, y) in occupied):
        deadzone[(x-BLOCK_WIDTH, y)] = True
    if not((x+BLOCK_WIDTH, y) in occupied):
        deadzone[(x+BLOCK_WIDTH, y)] = True

deadblocks = []
bounding_box = [0,0,0,0]
deadzone = {}
occupied = {}
blocks = []
running = True

capture_frames = True
frames = []
MAX_VIDEO_FRAMES = 9000
VIDEO_FPS = 60
VIDEO_FILENAME = "animation.mp4"



img = pygame.image.load('skyline.png')
if (HAS_INITIAL and INITIAL_TYPE == "image"):
    # img = pygame.transform.scale(img, (1875,344))
    screen.fill((0,0,0))
    screen.blit(img,(0,500))
if (HAS_INITIAL):
    if (INITIAL_TYPE == "circle"):
        bounding_box[0] = CIRCLE_CENTRE[0]-CIRCLE_RADIUS
        bounding_box[1] = CIRCLE_CENTRE[1]-CIRCLE_RADIUS
        bounding_box[2] = CIRCLE_CENTRE[0]+CIRCLE_RADIUS
        bounding_box[3] = CIRCLE_CENTRE[1]+CIRCLE_RADIUS
        for x in range(max(bounding_box[0], 0), bounding_box[2]):
            for y in range(bounding_box[1], min(bounding_box[3], HEIGHT)):
                for i in range(1- BLOCK_WIDTH,BLOCK_WIDTH):
                    if (x - CIRCLE_CENTRE[0])**2 + (y - CIRCLE_CENTRE[1])**2 <= CIRCLE_RADIUS**2:
                        if ( x+i - CIRCLE_CENTRE[0])**2 + (y- BLOCK_WIDTH - CIRCLE_CENTRE[1])**2 > CIRCLE_RADIUS**2:
                            deadzone[(x+i, y)] = True
                        if (x-BLOCK_WIDTH- CIRCLE_CENTRE[0])**2 + (y - CIRCLE_CENTRE[1])**2 > CIRCLE_RADIUS**2 > CIRCLE_RADIUS**2:
                            deadzone[(x-BLOCK_WIDTH, y)] = True
                        if (x+BLOCK_WIDTH- CIRCLE_CENTRE[0])**2 + (y - CIRCLE_CENTRE[1])**2 > CIRCLE_RADIUS**2 > CIRCLE_RADIUS**2:
                            deadzone[(x+BLOCK_WIDTH, y)] = True
    if (INITIAL_TYPE == "image"):
        bounding_box[0] = 0
        bounding_box[1] = 300
        bounding_box[2] = 1500
        bounding_box[3] = 900
        for x in range(max(bounding_box[0], 0), bounding_box[2]):
            for y in range(bounding_box[1], min(bounding_box[3], HEIGHT)):
                if screen.get_at((x,y))[1] >150:
                    for i in range(-1,2):
                        for j in range(-1,1):
                            if (screen.get_at( (max(x+i,0), y +j) )[1] <100):
                                deadzone[max(x+i,0), y +j] = True

                    
def update(block, deadblocks, deadzone, gone_index, bounding_box, occupied):
    if block.alive:
        if (ENABLE_BM):
            block.x += np.random.randint(-4,5)
        block.y += block.v 
        if block.y >= HEIGHT - BLOCK_HEIGHT or isOverLapBox( (block.x, block.y, block.x+BLOCK_WIDTH, block.y+BLOCK_HEIGHT), bounding_box ):
            block.y -= block.v
            for i in range(block.v):
                block.y += 1
                if ( block.y >= HEIGHT-BLOCK_HEIGHT and not HAS_INITIAL):
                    if False and ( (block.x <450) or (block.x > 550)):
                        block.gone = True
                        bisect.insort(gone_index, -k)
                    else:
                        block.y = HEIGHT - BLOCK_HEIGHT
                        block.alive = False
                        deadblocks.append(block)
                        block.gone = True
                        bisect.insort(gone_index, -k)
                        if ( not np.array(bounding_box).any()):
                            bounding_box[0] = block.x
                            bounding_box[1] = block.y
                            bounding_box[2] = block.x + BLOCK_WIDTH
                            bounding_box[3] = block.y + BLOCK_HEIGHT

                        if isOverLapBox( (block.x, block.y, block.x+BLOCK_WIDTH, block.y+BLOCK_HEIGHT), bounding_box ):
                            bounding_box = expand_box(block.x,block.y, bounding_box)
                        occupied[(block.x,block.y)] = True
                        add_deadzone(block.x, block.y, deadzone, occupied)
                    return
                elif isOverLapBox( (block.x, block.y, block.x+BLOCK_WIDTH, block.y+BLOCK_HEIGHT), bounding_box ):
                    if (block.x, block.y) in deadzone:
                        # if (intersect(block, other)):
                        #     if not((abs(block.x - other.x) == BLOCK_WIDTH) and (block.y == other.y)):
                        #         block.y = other.y - BLOCK_HEIGHT
                        block.alive = False
                        deadblocks.append(block)
                        block.gone = True
                        bisect.insort(gone_index, -k)
                        bounding_box = expand_box(block.x,block.y, bounding_box)
                        occupied[(block.x,block.y)]= True
                        del deadzone[(block.x, block.y)]
                        add_deadzone(block.x, block.y, deadzone, occupied)
                        return


while running:
    delta_t = clock.tick(120)/1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill(BG_COLOR)

    n = np.random.poisson(RATE)
    new_blocks = []
    gone_index = []
    for i in range(n):
        new_blocks = Block(np.random.randint(0, WIDTH/SPACING)*SPACING , 0, np.random.randint(V_MIN,V_MAX))
        if gone_index != []:
            blocks[-gone_index[-1]] = new_blocks
            gone_index = gone_index[:-1]
        else:
            blocks.append(new_blocks)
    for j in range(1):
        k =0
        for block in blocks:
           update(block, deadblocks, deadzone, gone_index, bounding_box, occupied)
        k += 1

    for block in blocks:
        if (block.gone is False):
            pygame.draw.rect(screen, (150,150,150), (block.x, block.y, BLOCK_WIDTH, BLOCK_HEIGHT))
    for block in deadblocks:
        ratio = 0
        if (HAS_INITIAL and INITIAL_TYPE == "circle"):
            ratio = 0.5 + np.sqrt((block.x -CIRCLE_CENTRE[0])**2 + (block.y - CIRCLE_CENTRE[1])**2)/(2*CIRCLE_RADIUS)
        elif (HAS_INITIAL and INITIAL_TYPE == "image"):
            ratio = 10
        else:
            ratio = 0.5 + np.sqrt((block.x -500)**2 + (block.y - HEIGHT-1)**2)/300
        pygame.draw.rect(screen, brighten((107,177,210), ratio), (block.x, block.y, BLOCK_WIDTH, BLOCK_HEIGHT))
    if HAS_INITIAL:
        if INITIAL_TYPE == "circle":
            pygame.draw.circle(screen, (58,72,102), CIRCLE_CENTRE, CIRCLE_RADIUS)

    if HAS_INITIAL and INITIAL_TYPE == "image":
        screen.blit(img,(0,500))


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

