import hashlib
import matplotlib.pyplot as plt
import numpy as np

import matplotlib.animation as animation



BOUND = 10
STEP = 0.025
SCALE = 1.005

fig, ax = plt.subplots()
ax.axis('off')

calls = 0
zoom = 1.0
filter = 16
linewidth = 1.0
max_calls = 150
BM = {0.0: 0.0}

np.random.seed(25)

def _seed_for_interval(a, t, b):
    key = f'{a:.17g},{t:.17g},{b:.17g}'
    digest = hashlib.sha256(key.encode('utf-8')).digest()
    return int.from_bytes(digest[:8], 'little', signed=False)


def computeBM(t):
    t = float(t)
    if t in BM:
        return BM[t]

    times = sorted(BM.keys())
    left = max((s for s in times if s < t), default=None)
    right = min((s for s in times if s > t), default=None)

    if left is None and right is None:
        # No known anchors other than 0, should not happen because BM[0]=0.
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


def brownian_bridge_sample(x1, y1, x2, y2, s):
    """Sample Brownian motion at an intermediate point constrained by endpoints.
    
    Given two points (x1, y1) and (x2, y2), generates a sample of Brownian motion
    at x1 + s*(x2 - x1) such that B(x1) = y1 and B(x2) = y2.
    
    Args:
        x1: First time/position point
        y1: Value of B at x1
        x2: Second time/position point
        y2: Value of B at x2
        s: Ratio in (0, 1), representing relative position between x1 and x2
        
    Returns:
        A sample from the Brownian bridge distribution at x1 + s*(x2 - x1)
    """
    if not (0 < s < 1):
        raise ValueError(f"s must be in (0, 1), got {s}")
    if x2 <= x1:
        raise ValueError(f"x2 must be > x1, got x1={x1}, x2={x2}")
    
    # Position at which to sample
    t = x1 + s * (x2 - x1)
    
    # Brownian bridge formula:
    # B(t) = y1 + (t - x1)/(x2 - x1) * (y2 - y1) + sqrt((t - x1)(x2 - t)/(x2 - x1)) * Z
    # where Z ~ N(0, 1)
    
    fraction = (t - x1) / (x2 - x1)
    drift = y1 + fraction * (y2 - y1)
    
    variance = (t - x1) * (x2 - t) / (x2 - x1)
    stddev = np.sqrt(variance)
    
    noise = np.random.normal(0, 1)
    sample = drift + stddev * noise
    
    return sample


def unique_sorted_by_x(pairs, tol=1e-20):
    """Sort pairs by x and remove duplicate x values.

    If the same x appears multiple times, the last occurrence is kept.
    """
    sorted_pairs = sorted(pairs, key=lambda pair: pair[0])
    unique = []
    last_x = None
    for x_val, y_val in sorted_pairs:
        if last_x is None or abs(x_val - last_x) > tol:
            unique.append((x_val, y_val))
            last_x = x_val
        else:
            unique[-1] = (x_val, y_val)
    return unique


# x = np.arange(-BOUND, BOUND, STEP)
# bm = np.zeros(len(x))
# for i in range(len(x)):
#     bm[i] = computeBM(x[i])

# zip1 = [None]*len(x)
# for i in range(len(x)):
#     zip1[i] = (x[i], bm[i])

# x2 = np.arange(-BOUND//2, BOUND//2, STEP/2)
# bm2 = np.zeros(len(x2))
# for i in range(len(x2)):
#     bm2[i] = computeBM(x2[i])

# zip2 = [None]*len(x2)
# for i in range(len(x2)):
#     zip2[i] = (x2[i], bm2[i])

combine = []
for j in range(0,2):
    x = np.arange(-BOUND/(2**j), BOUND/(2**j), STEP/(2**j))
    bm = np.zeros(len(x))
    for i in range(len(x)):
        bm[i] = computeBM(x[i])
    zip1 = [None]*len(x)
    for i in range(len(x)):
        zip1[i] = (x[i], bm[i])
    combine.extend(zip1)

def refine_bm(x, y):
    q1 = len(x)//4
    q3 = 3*len(x)//4
    # q1 = 0
    # q3 = len(x)
    new_points = []
    for i in range(q1, q3-1):
        mid_x = (x[i] + x[i+1]) / 2
        mid_y = brownian_bridge_sample(x[i], y[i], x[i+1], y[i+1], 0.5) 
        new_points.append((mid_x, mid_y))
    return new_points  

new_zip = sorted_pairs = sorted(combine, key=lambda pair: pair[0])


new_x = np.array([x for x, y in new_zip])
new_y = np.array([y for x, y in new_zip])

plot = ax.plot(new_x, new_y, linewidth=1.0)

def prune_and_scale(x, y, x_min, x_max, scale_factor):
    min = 0
    max = 0
    for i in range(len(x)):
        if x[i] >= x_min:
            min = i
        if x[i] >= x_max:
            max = i
            break
    new_x = x[min:max]
    new_y = y[min:max] /scale_factor
    return (new_x, new_y)
            

# quadratic scaling
s = 1.0
k = 2
def update2(frame):
    global s, calls, BM, new_x, new_y, k, plot
    s = 1.01 * s
    #ax.axis([-10/s, 10/s, -0.5/(s**2), 0.5/(s**2)])
    ax.axis([-10/(s**2), 10/(s**2), -3/s, 3/s])
    xdata = plot[0].get_xdata()
    ydata = plot[0].get_ydata()
    if (s> np.sqrt(k) ):
        k = k*2
        min_index = 0
        max_index = 0
        for i in range(len(xdata)):
            if (min_index == 0) and (xdata[i] >= ax.get_xlim()[0]):
                min_index = i
            if (min_index != 0) and (xdata[i] < ax.get_xlim()[1]):
                max_index = i
        x = xdata[min_index:max_index]
        y = ydata[min_index:max_index]
        print(len(x))
        
        pairs = [(a,b) for a,b in zip(x,y)]
        pairs.extend(refine_bm(list(x), list(y)))
        pairs = unique_sorted_by_x(pairs)
        new_x = np.array([x for x, y in pairs])
        new_y = np.array([y for x, y in pairs])
        plot[0].set_xdata(new_x)
        plot[0].set_ydata(new_y)
    # if (abs(xdata[0] - xdata[-1]) <= 1e-2 ):
    #     print("a")
    #     ax.axis([-10, 10, ax.get_ylim()[0], ax.get_ylim()[1]])
    #     scale = 20/(plot[0].get_xdata()[0] - plot[0].get_ydata()[-1])
    #     x = np.array(plot[0].get_xdata())* scale
    #     y = np.array(plot[0].get_ydata()) * s
    #     plot[0].set_xdata(x)
    #     plot[0].set_ydata(y)
    #     s = 1.0
    #     k = 2


    #bm_scaled =   np.sqrt(s)*bm
    #scaled_x = (1/s)*new_x
    #bm_scaled = np.sqrt(s) * np.interp( scaled_x, new_x, new_y, left=0, right=0)

    #plot[0].set_ydata(bm_scaled)
    #plot[0].set_xdata(x_scaled)
    return plot


animation_duration = 5.0
interval = 50
frames = int(animation_duration * 1000 / interval)

ani = animation.FuncAnimation(fig=fig, func=update2, frames=600, interval = 10, save_count= 600)
ani.save("BM.mp4", writer="ffmpeg", fps=60)
plt.show()
