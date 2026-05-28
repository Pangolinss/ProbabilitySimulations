from sympy import *
import numpy as np
from sympy import symbols, Function, integrate, diff
from scipy.special import airy
from scipy.integrate import solve_ivp, quad
import matplotlib.pyplot as plt
import seaborn as sns
import random


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

t0 = 4
tf = -6

y0_0 = airy(t0)[0]
y0_1 = airy(t0)[1]
y0_2 = quad(lambda x: (x-t0)*airy(x)[0]**2, t0, np.inf)[0]
y0_3 = airy(t0)[0]
y0_4 = quad(lambda x: airy(x)[0], t0, np.inf)[0]
y0 = np.array([y0_0, y0_1, y0_2, y0_3, y0_4])


sol = solve_ivp(f, (t0, tf) ,y0, max_step=.1)
F2 = np.exp(-sol.y[2])
f2 = -sol.y[3] * F2
F1 = np.sqrt(F2 * np.exp(-sol.y[4]))
f1 = 1/(2*F1)*(f2+sol.y[0]*F2)*np.exp(-sol.y[4])




plt.plot(sol.t, f2, label="β=2")
plt.plot(sol.t, f1, label="β=1")
plt.xlabel("t")
plt.ylabel("density")
plt.title("Tracy Widom for β=1,2")
plt.legend()
plt.show()




