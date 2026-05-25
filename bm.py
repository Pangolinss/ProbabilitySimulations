import hashlib
import matplotlib.pyplot as plt
import numpy as np
import pygame as pg

import matplotlib.animation as animation

np.random.seed(25) #seeding with 25 on my machine looks good

BOUND = 10
STEP = 0.05
SCALE = 1.005

fig, ax = plt.subplots()
ax.axis('off')

calls = 0
zoom = 1.0
filter = 16
linewidth = 1.0
max_calls = 150
BM = {0.0: 0.0}

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


x = np.arange(-BOUND, BOUND, STEP)
bm = np.zeros(len(x))
for i in range(len(x)):
    bm[i] = computeBM(x[i])

plot = ax.plot(x, bm, linewidth=1.0)
# quadratic scaling
s = 1.0
def update2(frame):
    global s, calls
    s += 0.25
    #bm_scaled =   np.sqrt(s)*bm
    bm_scaled = np.zeros(len(x))
    for i in range(len(x)):
        bm_scaled[i] = (np.sqrt(s)) * computeBM((1/(np.round(s))) * x[i])
    #x_scaled = x*s


    plot[0].set_ydata(bm_scaled)
    #plot[0].set_xdata(x_scaled)
    return plot


animation_duration = 5.0
interval = 50
frames = int(animation_duration * 1000 / interval)

ani = animation.FuncAnimation(fig=fig, func=update2, frames=frames, interval=interval)
#ani.save('bm.gif', writer='pillow', fps=20)
plt.show()
