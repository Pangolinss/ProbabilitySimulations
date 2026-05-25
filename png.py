import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as patches
import numpy as np
import itertools


def poisson_point_process_2d(intensity, membership, bbox, rng=None):
    """Generate points from a homogeneous 2D Poisson point process on a region.

    The region is defined by a membership function. Points are sampled
    uniformly over the bounding box and thinned by membership.

    Args:
        intensity: points per unit area (lambda).
        membership: callable(x, y) -> bool, region membership predicate.
        bbox: tuple (x_min, x_max, y_min, y_max) that contains the region.
        rng: optional numpy random Generator.

    Returns:
        numpy.ndarray of shape (N, 2) containing point coordinates.
    """
    if intensity < 0:
        raise ValueError('intensity must be non-negative')
    x_min, x_max, y_min, y_max = bbox
    if x_max <= x_min or y_max <= y_min:
        raise ValueError('bbox must define a positive rectangle')
    if rng is None:
        rng = np.random.default_rng()

    area = (x_max - x_min) * (y_max - y_min)
    count = rng.poisson(intensity * area)
    xs = rng.uniform(x_min, x_max, size=count)
    ys = rng.uniform(y_min, y_max, size=count)
    mask = [membership(x, y) for x, y in zip(xs, ys)]
    if not any(mask):
        return np.empty((0, 2))
    return np.column_stack((xs[mask], ys[mask]))


class Node(object):
    def __init__(self, data):
        self.data = data
        self.children = []

    def add_child(self, obj):
        self.children.append(obj)

class Tower(object):
    def __init__(self, left_, right_):
        self.left = left_
        self.right = right_

root = Node(Tower(-10, 10))
root.add_child(Node(Tower(0, 1)))

fig, ax = plt.subplots()
ax.set_aspect('equal', adjustable='box')
ax.set_title('Tree Nodes as Expanding Rectangles')
ax.set_xlabel('x')
ax.set_ylabel('y')

node_patches = []


def create_node_patch(node, depth):
    left = min(node.data.left, node.data.right)
    right = max(node.data.left, node.data.right)
    width = right - left
    height = 1
    y = depth
    rect = patches.Rectangle(
        (left, y),
        width,
        height,
        facecolor='cornflowerblue',
        edgecolor='none',
        alpha=0.5,
    )
    ax.add_patch(rect)
    info = {
        'rect': rect,
        'left0': left,
        'right0': right,
        'depth': depth,
    }
    node_patches.append(info)
    # attach patch info to the node for easy lookup/removal
    try:
        node.patch_info = info
    except Exception:
        pass
    return info


def merge_overlaps(node, depth=0):
    """Merge overlapping child nodes at the same depth.

    For each parent node, examine its immediate children. If any two
    children have overlapping x-intervals, replace them with a single
    merged node whose interval is the union and whose children are the
    concatenation of the two children's children. Also update the
    matplotlib patches to remove the old rectangles and add a new one.
    """
    if not node.children:
        return

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
                cur_right = max(cur_right, nxt_right)
                cur_children.extend(nxt.children)
                # mark nxt's patch for removal
                if hasattr(nxt, 'patch_info'):
                    try:
                        nxt.patch_info['rect'].remove()
                        if nxt.patch_info in node_patches:
                            node_patches.remove(nxt.patch_info)
                    except Exception:
                        pass
                j += 1
            else:
                break
        # if we merged anything (j > i+1) or leave as-is
        if j > i + 1:
            # remove cur's old patch as we'll create a merged one
            if hasattr(cur, 'patch_info'):
                try:
                    cur.patch_info['rect'].remove()
                    if cur.patch_info in node_patches:
                        node_patches.remove(cur.patch_info)
                except Exception:
                    pass
            # create merged node
            merged_node = Node(Tower(cur_left, cur_right))
            merged_node.children = cur_children
            merged_children.append(merged_node)
            # create a patch for the merged node
            create_node_patch(merged_node, depth + 1)
        else:
            # keep the current node (ensure its patch exists)
            merged_children.append(cur)
        i = j

    # replace parent's children with merged list
    node.children = merged_children

    # recurse into children
    for child in node.children:
        merge_overlaps(child, depth + 1)


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


def draw_tree_rectangles(node, depth=0):
    create_node_patch(node, depth)
    for child in node.children:
        draw_tree_rectangles(child, depth + 1)


max_depth, min_left, max_right = tree_stats(root)
expansion_duration = 5.0
speed = 1.0
max_expansion = speed * expansion_duration
ax.set_xlim(min_left - max_expansion - 1, max_right + max_expansion + 1)
ax.set_ylim(0, (max_depth + 2) * 1.5)

# draw rectangles for every node in the tree
draw_tree_rectangles(root)

interval = 50
frames = itertools.count()


def update(frame):

    points = np.random.poisson(0.1)
    for i in range(points):
        nucleation = np.random.random() * 20 - 10
        parent, parent_depth = find_deepest_node_for_x(root, nucleation)
        print(parent_depth)
        if parent is None:
            continue
        new_node = Node(Tower(nucleation - 0.1, nucleation + 0.1))
        parent.add_child(new_node)
        create_node_patch(new_node, parent_depth + 1)

    # merge any overlapping children produced this frame
    merge_overlaps(root, 0)

    t = frame * interval / 1000.0
    for info in node_patches:
        left = info['left0'] - frame * 0.1
        right = info['right0'] + frame * 0.1
        width = right - left
        rect = info['rect']
        rect.set_x(left)
        rect.set_width(width)
    return [info['rect'] for info in node_patches]

ani = animation.FuncAnimation(fig, update, frames=frames, interval=interval, blit=False, repeat=False)
plt.show()
