from Point2D import Point2D

class HermiteCurve:
    def __init__(self):
        self.control_points = []   # P0, P1, P2, P3...
        self.points = []           # punctele finale ale curbei

    def add_point(self, p: Point2D):
        self.control_points.append(p)

    def clear(self):
        self.control_points = []
        self.points = []

    def compute(self, steps=100):
        self.points = []

        pts = self.control_points
        n = len(pts)

        if n < 4 or n % 2 != 0:
            return


        i = 0
        while i + 3 < n:
            A  = pts[i]
            A1 = pts[i+1]
            B  = pts[i+2]
            B1 = pts[i+3]

            # vectori tangenta
            ax = A1.x - A.x
            ay = A1.y - A.y
            bx = B1.x - B.x
            by = B1.y - B.y

            for s in range(steps+1):
                u = s / steps
                u2 = u*u
                u3 = u*u*u

                F1 =  2*u3 - 3*u2 + 1
                F2 = -2*u3 + 3*u2
                F3 =  u3 - 2*u2 + u
                F4 =  u3 - u2

                x = F1*A.x + F2*B.x + F3*ax + F4*bx
                y = F1*A.y + F2*B.y + F3*ay + F4*by

                self.points.append(Point2D(x, y))

            i += 2
