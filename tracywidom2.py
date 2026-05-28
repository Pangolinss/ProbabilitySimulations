from sympy import *
import numpy as np
from sympy import symbols, Function, integrate, diff
from scipy.special import airy
from scipy.integrate import solve_ivp, quad
import matplotlib.pyplot as plt
import seaborn as sns
import random

import matplotlib.animation as animation


fig, ax = plt.subplots()

np.random.seed(140)
random.seed(140)

# Definition of I(t)
t, x = symbols("t x")
q = Function("q")
I = integrate((x-t)*q(x)**2, (x, t, oo))

# I'(t)
I_prime = diff(integrate((x-t)*q(x)**2, (x, t, oo)), t)

# I''(t)
I_prime2 = diff(integrate((x-t)*q(x)**2, (x, t, oo)), t, 2)

J = integrate(q(x), (x, t, oo))

def f(t, y):
    d0 = y[1]
    d1 = t*y[0]+2*y[0]**3
    d2 = y[3]
    d3 = y[0]**2
    d4 = -y[0]
    return np.array([d0, d1, d2, d3, d4])

t0 = 10
tf = -20

y0_0 = airy(t0)[0]
y0_1 = airy(t0)[1]
y0_2 = quad(lambda x: (x-t0)*airy(x)[0]**2, t0, np.inf)[0]
y0_3 = airy(t0)[0]
y0_4 = quad(lambda x: airy(x)[0], t0, np.inf)[0]
y0 = np.array([y0_0, y0_1, y0_2, y0_3, y0_4])


sol = solve_ivp(f, (t0, tf) ,y0, max_step = 0.005)
F2 = np.exp(-sol.y[2])
f2 = -sol.y[3] * F2
F1 = np.sqrt(F2 * np.exp(-sol.y[4]))
f1 = 1/(2*F1)*(f2+sol.y[0]*F2)*np.exp(-sol.y[4])


# f3 = np.flip(sol.y[1] - sol.y[0]**2)
f3 = np.flip(sol.y[0])

# Build a searchable lookup from times to F1 values.
F1_lookup = {float(time_point): float(value) for time_point, value in zip(sol.t, F1)}

time = np.flip(np.array(sol.t))
fun = np.flip(np.array(F1))


t = 0.1

def update(frame):
    global t
    t += 0.1
    new_t = time * np.math.exp(np.math.log(t/4.0)* (-1/3))
    new_F = np.interp(new_t, time, fun, 0, 1) 
    ax.clear()

    ax.plot(time, new_F)
    ax.axis(xmin = -10, xmax = 10, ymin = -0.5, ymax = 1.5)

def update2(frame):
    global t
    t += 0.1
    new_t = time * np.math.exp(np.math.log(t/4.0)* (-1/3))
    new_F = np.math.exp(np.math.log(t/4.0) * (-2/3)) *np.interp(new_t, time, f3, 0, 1)
    ax.clear()
    ax.plot(time, new_F)


#ani = animation.FuncAnimation(fig=fig, func=update, frames=60, interval=10)

ax.plot(time, f3)

#plt.plot(sol.t, f2, label="β=2")
#plt.plot(sol.t, F1, label="β=1")
#plt.xlabel("t")
#plt.ylabel("density")
#plt.title("Tracy Widom for β=1,2")
#plt.legend()
plt.show()




