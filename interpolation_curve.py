import numpy as np
from Point2D import Point2D

class InterpolationCurve:

    def __init__(self):
        self.control_points: list[Point2D] = []
        self.points: list[Point2D] = []

    def add_point(self, p: Point2D):
        self.control_points.append(p)

    def can_add_point(self, p: Point2D) -> bool:
        if not self.control_points:
            return True
        return p.x > self.control_points[-1].x

    def compute_lagrange(self, m=100):
        pts = self.control_points
        n = len(pts) - 1
        if n < 1:
            self.points = []
            return

        x0 = pts[0].x
        xn = pts[-1].x
        dist = (xn - x0) / m

        result = []
        for index in range(m + 1):
            x = x0 + index * dist
            Lx = self.lagrange_value(x)
            result.append(Point2D(x, Lx))

        self.points = result

    def lagrange_value(self, x):
        """
        Computes L_n(x) using Lagrange formula
        """
        pts = self.control_points
        n = len(pts)

        total = 0
        for i in range(n):
            xi, yi = pts[i].x, pts[i].y
            li = 1

            for j in range(n):
                if i == j:
                    continue
                xj = pts[j].x
                li *= (x - xj) / (xi - xj)

            total += yi * li

        return total


    # tema_4 newton code

    def compute_newton(self, m=100):
        x = np.array([point.x for point in self.control_points], dtype=float)
        y = np.array([point.y for point in self.control_points], dtype=float)

        coeffs = self.divided_diferences(x, y)

        x_values = np.linspace(x[0], x[-1], m+1)

        result = []
        for curve_point_x in x_values:
            curve_point_y = self.newton_eval(x, curve_point_x, coeffs)
            result.append(Point2D(curve_point_x, curve_point_y))

        self.points = result


    def newton_eval(self, x, curve_point_x, a_0):
        n = len(a_0)
        result = a_0[0]
        prod = curve_point_x - x[0]

        for h in range (1, n):
            result += a_0[h] * prod
            prod *= curve_point_x - x[h]

        return result 

    def divided_diferences(self, x, y):
        n = len(x)
        a = np.zeros((n, n), dtype=float)

        for h in range(n):
            a[h][h] = y[h]

        for h in range(n-1, -1, -1):
            for k in range(h+1, n):
                a[h][k] = (a[h+1][k] - a[h][k-1])/(x[k] - x[h])

        return [a[0][j] for j in range(n)]
    




        
