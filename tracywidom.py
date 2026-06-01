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


def discrete_second_derivative(t, y):
    """Compute the discrete second derivative of y with respect to t.
    
    Uses finite differences to approximate y'' at each point.
    For interior points, uses central differences.
    For boundary points, uses forward/backward differences.
    
    Args:
        t: Array of time/position points (must be sorted)
        y: Array of function values corresponding to t
        
    Returns:
        Array of second derivative values with the same shape as y
    """
    t = np.asarray(t)
    y = np.asarray(y)
    
    if len(t) < 3:
        raise ValueError("Need at least 3 points to compute second derivative")
    
    n = len(t)
    y_double_prime = np.zeros(n)
    
    for i in range(n):
        if i == 0:
            # Forward difference at left boundary
            h1 = t[1] - t[0]
            h2 = t[2] - t[1]
            y_double_prime[i] = y[2]/(h2*(h1+h2)) - y[1]/(h1*h2) + y[0]/(h1*(h1+h2))
        elif i == n - 1:
            # Backward difference at right boundary
            h1 = t[i] - t[i-1]
            h2 = t[i-1] - t[i-2]
            y_double_prime[i] = y[i]/(h1* (h1 + h2)) - y[i-1]/(h1 * h2) + y[i-2]/(h2 * (h1 + h2))
        else:
            # Central difference for interior points
            h1 = t[i] - t[i-1]
            h2 = t[i+1] - t[i]
            y_double_prime[i] = 2*(y[i+1]/(h2 * (h1+h2)) - y[i]/(h1 * h2) + y[i-1]/(h1 * (h1+h2)))
    return y_double_prime


t0 = 10
tf = -10

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


f3 = np.flip(sol.y[1] - sol.y[0]**2)

# Build a searchable lookup from times to F1 values.
F1_lookup = {float(time_point): float(value) for time_point, value in zip(sol.t, F1)}

time = np.flip(np.array(sol.t))
fun = np.flip(np.array(F1))


t = 0.0001
s = 0
def heaviside_step_fun(x,t):
    return np.array([1 if xi > t else 0 for xi in x])


def update(frame):
    global t, s
    s+=1
    if (s < 50):
        ax.clear()
        ax.plot(time, heaviside_step_fun(time, 0))
        ax.axis(xmin = -10, xmax = 10, ymin = -0.5, ymax = 1.5)
        ax.axis('off')
    else:
        if (t < 10):
            t += 0.05*t
        else:
            t += 1
        new_t = time * np.math.exp(np.math.log(t/4.0)* (-1/3))
        new_F = np.interp(new_t, time, fun, 0, 1) 
        ax.clear()

        ax.plot(time, new_F)
        ax.axis(xmin = -10, xmax = 10, ymin = -0.5, ymax = 1.5)
        ax.axis('off')

def update2(frame):
    global t
    t += 0.1
    fprime = discrete_second_derivative(time, np.log(fun))
    new_t = time * np.math.exp(np.math.log(t/4.0)* (-1/3))

    new_F = np.math.exp(np.math.log(t/4.0) * (-2/3)) * fprime
    ax.clear()
    ax.plot(time, new_F)
    ax.axis(xmin = -20, xmax = 5, ymin = -500, ymax = 5)



#ax.plot(time,  discrete_second_derivative(time, np.log(fun)))

ani = animation.FuncAnimation(fig=fig, func=update2, frames=600, interval=10, save_count=600)
plt.show()

# try:
#     ani.save("tw-animation1.mp4", writer="ffmpeg", fps=60)
#     print("Saved animation to tw-animation1.mp4")
# except Exception as e:
#     print(f"Failed to save MP4: {e}")

#ax.plot(time, f3)

#plt.plot(sol.t, f2, label="β=2")
#plt.plot(sol.t, F1, label="β=1")
#plt.xlabel("t")
#plt.ylabel("density")
#plt.title("Tracy Widom for β=1,2")
#plt.legend()




