import pygame
import numpy as np
import imageio
import bisect 


def color_gradient(ratio):
    r = ratio %1
    if r < 0.1667:
        a = r/0.1667
        return (0, 255 * a,255 * a)
    elif r < 2 * 0.1667:
        a = (r - 0.1667)/0.1667
        return (255 * a, 255 * (1-a), 255)
    if r < 3 * 0.1667:
        a = (r - 2*0.1667)/0.1667
        return (255, 0, 255*(1-a))
    if r < 4 * 0.1667:
        a = (r - 3*0.1667)/0.1667
        return (255 * (1-a), 255 * a, 0)
    if r < 5 * 0.1667:
        a = (r - 4*0.1667)/0.1667
        return (255 * a, 255 * (1-a), 255* a)
    else:
        a = (r - 5*0.1667)/0.1667
        return (255 * (1-a), 0, 255 * (1-a))



WIDTH, HEIGHT = 800, 800
SCALE = 2
ARRAY_WIDTH = 500
ARRAY_HEIGHT = 500
INITIAL = (250,250)
BG_COLOR = (255,255,255)
X_OFFSET = -100
Y_OFFSET = -100
DIRECTIONS = [(1,0), (0,1), (0,-1), (-1,0)]


capture_frames = True
frames = []
MAX_VIDEO_FRAMES = 9000
VIDEO_FPS = 60
VIDEO_FILENAME = "animation.mp4"


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Eden Model")
clock = pygame.time.Clock()

grid = np.zeros(shape = (ARRAY_HEIGHT, ARRAY_WIDTH))

active_blocks = {}

active_blocks[INITIAL] = 0
boundary_index = [INITIAL]
grid[INITIAL[0]][INITIAL[1]] = 1/1000




def update(grid, active_blocks, boundary_index, frame_count):
    for i in range(frame_count//100 + 1):
        L = len(boundary_index )
        k = np.random.randint(0,L)
        coord = boundary_index[k]
        randir = np.random.permutation(DIRECTIONS)
        for a in randir:
            if (not (a[0] + coord[0], a[1] + coord[1]) in active_blocks ):
                new_growth =  (a[0] + coord[0], a[1] + coord[1])
                sum = 0
                for dir in DIRECTIONS:
                    if ( (new_growth[0]+dir[0], new_growth[1]+dir[1]) in active_blocks ):
                        active_blocks[(new_growth[0]+dir[0], new_growth[1]+dir[1])] += 1
                        sum += 1
                        if (active_blocks[(new_growth[0]+dir[0], new_growth[1]+dir[1])] == 4):
                            index = boundary_index.index( (new_growth[0]+dir[0], new_growth[1]+dir[1]) )
                            boundary_index[index], boundary_index[-1] = boundary_index[-1], boundary_index[index]
                            boundary_index.pop()
                active_blocks[new_growth] = sum
                grid[ min(ARRAY_WIDTH, max(0, new_growth[0]))  ][min(ARRAY_HEIGHT, max(0, new_growth[1]))  ] = frame_counter/1000
                if (sum <4):
                    boundary_index.append((a[0] + coord[0], a[1] + coord[1]))
                break

running = True
frame_counter = 0
while running:
    frame_counter +=1 
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill(BG_COLOR)
    for i in range(ARRAY_HEIGHT):
        for j in range(ARRAY_WIDTH):
            if grid[i][j] > 1e-8:
                pygame.draw.rect(screen, color_gradient(grid[i][j]), (X_OFFSET + SCALE*i, Y_OFFSET + SCALE*j, SCALE,SCALE))
    update(grid, active_blocks, boundary_index, frame_counter)

    if capture_frames and len(frames) < MAX_VIDEO_FRAMES:
        frame = pygame.surfarray.array3d(screen)
        frame = np.transpose(frame, (1, 0, 2))
        frames.append(frame)
    pygame.display.flip()


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
    


