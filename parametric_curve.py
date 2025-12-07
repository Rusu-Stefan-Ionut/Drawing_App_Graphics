import numpy as np
from Point2D import Point2D


class ParametricCurve:

    def __init__(self):
        self.raw_points: list[Point2D] = []
        self.points: list[Point2D] = []

        self.min_x = 0
        self.min_y = 0
        self.scale_factor = 1
        self.dx_center = 0
        self.dy_center = 0

        # stored params for resize
        self.last_a = None
        self.last_b = None
        self.last_n = None
        self.last_funcs = None

    def compute_points(self, a: float, b: float, n: int, *args):
        self.last_a = a
        self.last_b = b
        self.last_n = n
        self.last_funcs = args

        pts = []
        for i in range(n + 1):
            u = a + i * (b - a) / n

            if len(args) == 1:
                f_u, g_u = args[0](u)
            elif len(args) == 2:
                f, g = args
                f_u = f(u)
                g_u = g(u)
            else:
                raise ValueError("Must pass either 1 or 2 functions")

            pts.append(Point2D(f_u, g_u))

        self.raw_points = pts

    def step1_translate(self, pts):
        self.min_x = min(p.x for p in pts)
        self.min_y = min(p.y for p in pts)

        return [
            Point2D(p.x - self.min_x, p.y - self.min_y)
            for p in pts
        ]

    def step2_scale(self, pts, L, H):
        max_x = max(p.x for p in pts)
        max_y = max(p.y for p in pts)

        max_x = max_x if max_x != 0 else 1
        max_y = max_y if max_y != 0 else 1

        Sx = L / max_x
        Sy = H / max_y
        self.scale_factor = min(Sx, Sy)

        return [
            Point2D(p.x * self.scale_factor,
                    p.y * self.scale_factor)
            for p in pts
        ]

    def step3_center(self, pts, L, H):
        max_x = max(p.x for p in pts)
        max_y = max(p.y for p in pts)

        self.dx_center = (L - max_x) / 2
        self.dy_center = (H - max_y) / 2

        return [
            Point2D(p.x + self.dx_center,
                    p.y + self.dy_center)
            for p in pts
        ]

    def step4_flip(self, pts, H):
        return [
            Point2D(p.x, H - p.y)
            for p in pts
        ]

    def transform(self, L: float, H: float):
        pts = self.raw_points
        # S'
        pts = self.step1_translate(pts)
        # S''
        pts = self.step2_scale(pts, L, H)
        # S'''
        pts = self.step3_center(pts, L, H)
        # S''''
        pts = self.step4_flip(pts, H)
        self.points = pts

    def transformed_origin(self, L: float, H: float) -> Point2D:
        x = -self.min_x
        y = -self.min_y

        x *= self.scale_factor
        y *= self.scale_factor

        x += self.dx_center
        y += self.dy_center

        y = H - y

        return Point2D(x, y)
    
    def fcallable(self, u):
        return u
    
    def gcallable(self, u):
        return u**2

    def ellipse(self, u, c=100, d=50):
        return c * np.cos(u), d * np.sin(u)
    
    def spiral(self, u):
        return u * np.cos(u), u * np.sin(u) 
    
    def parabola(self, u): 
        return u, u-1
