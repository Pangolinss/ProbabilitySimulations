import pygame
import numpy as np
import hashlib

# Initialize pygame
pygame.init()

# Screen setup
WIDTH, HEIGHT = 1200, 300
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("1D Brownian Motion")
clock = pygame.time.Clock()

# Colors
BG_COLOR = (255, 255, 255)
LINE_COLOR = (200, 200, 200)
PARTICLE_COLOR = (0, 255, 100)
TRAIL_COLOR = (100, 150, 255)

# Brownian motion parameters
BM = {0.0: 0.0}

np.random.seed(25)

def _seed_for_interval(a, t, b):
    key = f'{a:.17g},{t:.17g},{b:.17g}'
    digest = hashlib.sha256(key.encode('utf-8')).digest()
    return int.from_bytes(digest[:8], 'little', signed=False)

def computeBM(t):
    """Compute Brownian motion value at time t using interpolation"""
    t = float(t)
    if t in BM:
        return BM[t]

    times = sorted(BM.keys())
    left = max((s for s in times if s < t), default=None)
    right = min((s for s in times if s > t), default=None)

    if left is None and right is None:
        left = 0.0
        right = None
    if left is None:
        mean = BM[right]
        variance = abs(t - right)
    elif right is None:
        mean = BM[left]
        variance = abs(t - left)
    else:
        if left == right:
            mean = BM[left]
            variance = 0.0
        else:
            t_left = left
            t_right = right
            left_val = BM[t_left]
            right_val = BM[t_right]
            fraction = (t - t_left) / (t_right - t_left)
            mean = left_val + fraction * (right_val - left_val)
            variance = (t - t_left) * (t_right - t) / (t_right - t_left)

    if variance == 0.0:
        value = mean
    else:
        value = np.random.normal(mean, np.sqrt(variance))

    BM[t] = value
    return value

# Simulation parameters
time_step = 0.05
total_time = 30.0
time_values = []
bm_values = []

# Pre-compute brownian motion values
current_time = 0.0
while current_time <= total_time:
    bm_value = computeBM(current_time)
    time_values.append(current_time)
    bm_values.append(bm_value)
    current_time += time_step

# Graph setup
margin = 50
graph_width = WIDTH - 2 * margin
graph_height = HEIGHT - 2 * margin
graph_left = margin
graph_top = margin

font = pygame.font.Font(None, 24)

# Draw once
screen.fill(BG_COLOR)

# Draw graph axes
# pygame.draw.line(screen, LINE_COLOR, (graph_left, graph_top + graph_height), 
#                  (graph_left + graph_width, graph_top + graph_height), 2)  # X-axis
# pygame.draw.line(screen, LINE_COLOR, (graph_left, graph_top), 
#                  (graph_left, graph_top + graph_height), 2)  # Y-axis

# Draw grid lines and labels
num_y_ticks = 11
y_min = min(bm_values) - 0.5
y_max = max(bm_values) + 0.5
# for i in range(num_y_ticks):
#     y_val = y_min + (y_max - y_min) * i / (num_y_ticks - 1)
#     screen_y = graph_top + graph_height - (y_val - y_min) / (y_max - y_min) * graph_height
#     pygame.draw.line(screen, (60, 60, 60), (graph_left, screen_y), 
#                     (graph_left + graph_width, screen_y), 1)
#     label = font.render(f"{y_val:.1f}", True, LINE_COLOR)
#     screen.blit(label, (graph_left - 40, screen_y - 12))

# Draw the graph line
time_min = time_values[0]
time_max = time_values[-1]
time_range = time_max - time_min if time_max > time_min else 1

for i in range(len(time_values) - 1):
    x1 = graph_left + (time_values[i] - time_min) / time_range * graph_width
    y1 = graph_top + graph_height - ((bm_values[i] - y_min) / (y_max - y_min)) * graph_height
    
    x2 = graph_left + (time_values[i+1] - time_min) / time_range * graph_width
    y2 = graph_top + graph_height - ((bm_values[i+1] - y_min) / (y_max - y_min)) * graph_height
    
    # Clamp to graph area
    y1 = max(graph_top, min(graph_top + graph_height, y1))
    y2 = max(graph_top, min(graph_top + graph_height, y2))
    
    pygame.draw.line(screen, TRAIL_COLOR, (x1, y1), (x2, y2), 2)

# Draw labels
title_label = font.render(f"Brownian Motion (Points: {len(BM)})", True, LINE_COLOR)
screen.blit(title_label, (10, 10))

x_label = font.render("Time", True, LINE_COLOR)
screen.blit(x_label, (graph_left + graph_width - 40, graph_top + graph_height + 10))

pygame.display.flip()

# Keep window open
running = True
time = 0
while running:
    time+=1
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    clock.tick(60)

pygame.quit()
