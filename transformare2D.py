import numpy as np

from Point2D import Point2D

class Transformare2D:
    def __init__(self):
        self._matrix = np.eye(3, dtype=float)

    def getMatrix(self):
        return self._matrix
    
    def _left_transf(self, trasnf_matrix: np.ndarray):
        self._matrix = trasnf_matrix @ self._matrix

    def translatie(self, dx: float, dy: float):
        A = np.array([[1, 0, dx],
                     [0, 1, dy],
                     [0, 0, 1]],
                     dtype=float)
        self._left_transf(A)
        return self
    
    def scalare(self, sx: float, sy: float):
        A = np.array([[sx, 0, 0],
                      [0, sy, 0],
                      [0,  0, 1]], dtype=float)
        self._left_transf(A)
        return self

    def rotatie(self, cos_a: float, sin_a: float):
        A = np.array([[ cos_a, -sin_a, 0],
                      [ sin_a,  cos_a, 0],
                      [     0,      0, 1]], dtype=float)
        self._left_transf(A)
        return self

    def simetrie_ox(self):
        return self.scalare(1, -1)

    def simetrie_oy(self):
        return self.scalare(-1, 1)

    def simetrie_origine(self):
        return self.scalare(-1, -1)
    
    def apply_to_point(self, point: Point2D) -> Point2D:
        vec = point.toVector()
        transformed_vec = self._matrix @ vec
        return Point2D(transformed_vec[0] / transformed_vec[2],
                       transformed_vec[1] / transformed_vec[2])