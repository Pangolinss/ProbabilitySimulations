import pygame
import numpy as np
import imageio
import PerlineNoise
import math as math

# Initialize pygame
pygame.init()

# Screen setup
WIDTH, HEIGHT = 1600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tree Visualization with Rectangles")
clock = pygame.time.Clock()

# Colors
BG_COLOR =  (255,255,255)#(92, 75, 119)
RED = (228, 3, 3)
ORANGE = (255, 140, 0)
YELLOW = (255, 237, 0)
GREEN = (0, 128, 38)
BLUE = (0, 76, 255)
VIOLET = (115, 41, 130)
COLORS = [(155, 112, 157), (169, 104, 147), (204, 109, 110), (148, 152, 199), (101, 80, 123)]
COLORS2 = [(138, 147, 202) , (210, 116, 134), (255, 189, 141), (253, 187, 152), (237, 130, 120)]

RANDOM_INITIAL = True

NUM_OF_NODES = 1
SCALE = 5
X_OFFSET = 800
Y_OFFSET = 770
SPACING = 5
RECT_HEIGHT = 5
EXPAND_RATE = 0.01

capture_frames = True


def complementary_color(rgb):
    """Return the complementary RGB color for a given (r, g, b) triple.

    Each channel is inverted around 255 so the complementary color is
    (255-r, 255-g, 255-b).
    """
    r, g, b = rgb
    return (255 - r, 255 - g, 255 - b)


class Node(object):
    def __init__(self, data, parent=None):
        self.data = data
        self.children = []
        self.parent = parent

    def add_child(self, obj):
        obj.parent = self
        self.children.append(obj)


class Line(object):
    def __init__(self, p1_, p2_, d, color = (0,0,0), thickness = 1):
        self.p1 = p1_
        self.p2 = p2_
        self.depth = d
        self.color = color
        self.thickness = thickness
class Tower(object):
    def __init__(self, left_, right_):
        self.left = left_
        self.right = right_


def tree_stats(node, depth=0):
    min_left = node.data.left
    max_right = node.data.right
    max_depth = depth
    for child in node.children:
        c_depth, c_left, c_right = tree_stats(child, depth + 1)
        max_depth = max(max_depth, c_depth)
        min_left = min(min_left, c_left)
        max_right = max(max_right, c_right)
    return max_depth, min_left, max_right

def find_deepest_node_for_x(node, x):
    def helper(current, depth=0):
        left = min(current.data.left, current.data.right)
        right = max(current.data.left, current.data.right)
        if x < left or x > right:
            return None, -1
        best_node = current
        best_depth = depth
        for child in current.children:
            child_node, child_depth = helper(child, depth + 1)
            if child_node is not None and child_depth > best_depth:
                best_node = child_node
                best_depth = child_depth
        return best_node, best_depth

    node_found, node_depth = helper(node, 0)
    return node_found, node_depth

def merge_overlaps(node, merge_locations, depth=0):
    """Merge overlapping child nodes at the same depth."""
    if not node.children:
        return []

    # sort children by left coordinate
    children = sorted(node.children, key=lambda c: min(c.data.left, c.data.right))
    merged_children = []
    i = 0
    while i < len(children):
        cur = children[i]
        cur_left = min(cur.data.left, cur.data.right)
        cur_right = max(cur.data.left, cur.data.right)
        cur_children = list(cur.children)
        j = i + 1
        while j < len(children):
            nxt = children[j]
            nxt_left = min(nxt.data.left, nxt.data.right)
            nxt_right = max(nxt.data.left, nxt.data.right)
            # consider overlap or touching as mergeable
            if nxt_left <= cur_right:
                # extend current interval and absorb children
                merge_locations.append((nxt_left, cur_right))
                cur_right = max(cur_right, nxt_right)
                cur_children.extend(nxt.children)
                j += 1
            else:
                break
        # if we merged anything (j > i+1) or leave as-is
        if j > i + 1:
            # create merged node
            merged_node = Node(Tower(cur_left, cur_right))
            merged_node.children = cur_children
            for child in merged_node.children:
                child.parent = merged_node
            merged_children.append(merged_node)
        else:
            # keep the current node
            merged_children.append(cur)
        i = j

    # replace parent's children with merged list
    node.children = merged_children
    for child in node.children:
        child.parent = node

    # recurse into children
    for child in node.children:
        merge_overlaps(child, merge_locations, depth + 1)

COLOR_INTERP_HEIGHT = 20

def gradient_color(initial_color, final_color, max_height, depth):
    if (depth//max_height) % 2 == 1:
        initial_color, final_color = final_color, initial_color
    ratio = (depth % max_height) / max_height
    r = int(initial_color[0] * (1 - ratio) + final_color[0] * ratio)
    g = int(initial_color[1] * (1 - ratio) + final_color[1] * ratio)
    b = int(initial_color[2] * (1 - ratio) + final_color[2] * ratio)
    return (r, g, b)

def draw_node_rectangles(node, initial_color, final_color, depth=0, x_scale=20, x_offset = 500, y_start=500, rect_height=40):
    """Draw rectangles for node and all children. Returns list of (left, top, width, height, depth)."""
    rects = []
    left = min(node.data.left, node.data.right)
    right = max(node.data.left, node.data.right)
    
    x1 = x_offset + int(left * x_scale )  # map to screen, centered around -10 to 10
    x2 = x_offset + int(right * x_scale)
    width = max(1, x2 - x1)
    
    y = y_start - depth * (rect_height)
    
    color = gradient_color(initial_color, final_color, COLOR_INTERP_HEIGHT, depth)
    # Draw rectangle for this node
    pygame.draw.rect(screen, color, (x1, y, width, rect_height))
    rects.append((x1, y, width, rect_height, depth))
    
    # Recursively draw children
    for child in node.children:
        child_rects = draw_node_rectangles(child, initial_color, final_color, depth + 1, x_scale, x_offset, y_start, rect_height)
        rects.extend(child_rects)
    
    return rects


def node_tree_to_lines(node):
    """Convert a tower node tree into a list of horizontal lines.

    Each line is either the top edge of a rectangle or the gap between
    adjacent rectangles at the same depth.
    """
    lines = []
    hori_lines = []
    def helper(current, lines, hori_lines, depth):
        if current is None:
            return
        hori_lines.append((current.data.left, current.data.right, depth))
        if current.children == []:
            lines.append(Line(current.data.left, current.data.right, depth))
            return
        left = min(current.data.left, current.data.right)
        right = max(current.data.left, current.data.right)
        node_left = 0
        node_right = 0
        for node in current.children:
            node_left = min(node.data.left, node.data.right)
            node_right = max(node.data.left, node.data.right)
            # add line for gap between current and child if they don't overlap
            if right > node_left:
                lines.append(Line( left, node_left, depth))
            helper(node, lines, hori_lines, depth + 1)
            left = node_right
        if (right > node_right):
            lines.append(Line(node_right, right, depth))
    helper(node, lines, hori_lines, 0)

    return lines, hori_lines


def expand_node_rectangles(node, elapsed_time, rate = 0.1):
    node.data.left -= rate*elapsed_time
    node.data.right += rate*elapsed_time
    for child in node.children:
        expand_node_rectangles(child, elapsed_time, rate)

def get_tree_depth(node, depth=0):
    """Get max depth of tree."""
    if not node.children:
        return depth
    return max(get_tree_depth(child, depth + 1) for child in node.children)


def discrete_random_walk(x, rate = 0.1):
    y = [None]*len(x)
    y[0] = 0
    for i in range(1,len(x)):
        y[i] = y[i-1] + (np.random.randint(0,2)*2-1)* np.random.poisson(rate)
        if y[i]< 0:
            y[i] = y[i-1]
    y[-1] = 0
    return y
def discrete_to_node(x, y):
    """Build a tree from x/y data using a stack for active nodes."""
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    if len(x) < 2:
        raise ValueError("At least two x/y points are required")

    points = sorted(zip(x, y), key=lambda p: p[0])
    xs, ys = zip(*points)
    ys = [int(round(v)) for v in ys]

    for i in range(1, len(ys)):
        if abs(ys[i] - ys[i-1] - round(ys[i] - ys[i-1])) > 1e-9:
            raise ValueError("Adjacent y values must differ by integer amounts")

    root = Node(Tower(xs[0], xs[-1]))
    stack = [root]

    for i in range(1, len(xs)):
        delta = ys[i] - ys[i-1]
        if delta > 0:
            for _ in range(delta):
                node = Node(Tower(xs[i], xs[i]))
                stack[-1].add_child(node)
                stack.append(node)
        elif delta < 0:
            for _ in range(-delta):
                if len(stack) <= 1:
                    raise ValueError("y decreased below the root level")
                closing = stack.pop()
                closing.data.right = xs[i]

    while len(stack) > 1:
        closing = stack.pop()
        closing.data.right = xs[-1]

    return root


            




node_array = []
if not RANDOM_INITIAL:
    for i in range(NUM_OF_NODES):
        node_array.append(Node(Tower(-0.5, 0.5)))

if RANDOM_INITIAL:
    x = np.linspace(-150,150,300)
    y = discrete_random_walk(x, 3)
    node = discrete_to_node(x,y)
    node_array.append(node)
    


# Simulation parameters
frame_count = 0
font = pygame.font.Font(None, 24)

# Video export settings

frames = []
MAX_VIDEO_FRAMES = 6000
VIDEO_FPS = 60
VIDEO_FILENAME = "animation.mp4"

# Main loop
running = True
cur_t = 0
delta_t = 0
while running:
    delta_t = clock.tick(60)
    cur_t += delta_t
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Add new nodes randomly
    # points = np.random.poisson(0.01+ 0.03*(cur_t/2000)  ) #use this rate for most of them
    points = np.random.poisson(2*(0.04+ 0.06*(cur_t/500))  ) #use this rate for most of them
    for i in range(points):
        base = node_array[0].data.right - node_array[0].data.left
        nucleation = np.random.random() * base - base/2
        parent, parent_depth = find_deepest_node_for_x(node_array[0], nucleation)
        if parent is not None:
            new_node = Node(Tower(nucleation - 0.05, nucleation + 0.05))
            parent.add_child(new_node)
    

    for node in node_array:
        expand_node_rectangles(node, delta_t, rate=EXPAND_RATE)

    # Merge overlapping nodes
    for i in range(NUM_OF_NODES):
        merges = []
        merge_overlaps(node_array[i], merges, 0)
        if (i != NUM_OF_NODES-1):
            if (merges is not None):
                for merge in merges:
                    merge_location = (merge[0] + merge[1]) / 2
                    parent, parent_depth = find_deepest_node_for_x(node_array[i+1], merge_location)
                    if parent is not None:
                        new_node = Node(Tower(merge_location - 0.1, merge_location + 0.1))
                        parent.add_child(new_node)
                    parent.children = sorted(parent.children, key=lambda c: min(c.data.left, c.data.right))
    
    # Draw
    screen.fill(BG_COLOR)
    
    # Draw rectangles for all nodes
    all_rects = []
    #for i in range(len(node_array)):
    #    all_rects.extend(draw_node_rectangles(node_array[i], COLORS[i % len(COLORS)], COLORS2[i % len(COLORS2)], 0, 20, 800, 465+80*i, 15))

    line_array = [None]*NUM_OF_NODES
    hori_line_array = [None]*NUM_OF_NODES
    for i in range(len(node_array)):
        line_array[i], hori_line_array[i] = node_tree_to_lines(node_array[i])
        for l in line_array[i]:
            pygame.draw.line(screen, (0,0,0), (l.p1*SCALE + X_OFFSET, Y_OFFSET+SPACING*i - l.depth*RECT_HEIGHT), (l.p2*SCALE + X_OFFSET, Y_OFFSET+SPACING*i - l.depth*RECT_HEIGHT), 3)
    
        for l in hori_line_array[i]:
            pygame.draw.line(screen, (0,0,0), (l[0]*SCALE + X_OFFSET, Y_OFFSET+SPACING*i - l[2]*RECT_HEIGHT), (l[0]*SCALE + X_OFFSET, Y_OFFSET+SPACING*i - (l[2]-1)*RECT_HEIGHT), 3)
            pygame.draw.line(screen, (0,0,0), (l[1]*SCALE + X_OFFSET, Y_OFFSET+SPACING*i - l[2]*RECT_HEIGHT), (l[1]*SCALE + X_OFFSET, Y_OFFSET+SPACING*i - (l[2]-1)*RECT_HEIGHT), 3) 


    if capture_frames and len(frames) < MAX_VIDEO_FRAMES:
        frame = pygame.surfarray.array3d(screen)
        frame = np.transpose(frame, (1, 0, 2))
        frames.append(frame)
    
    frame_count += 1
    pygame.display.flip()

pygame.quit()

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