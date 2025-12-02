import numpy as np
from Point2D import Point2D

class Transform2D:
    def __init__(self):
        self._matrix = np.eye(3, dtype=float)

    def get_matrix(self):
        return self._matrix
    
    def _left_transform(self, transform_matrix: np.ndarray):
        self._matrix = transform_matrix @ self._matrix

    def translation(self, dx: float, dy: float):
        A = np.array([[1, 0, dx],
                      [0, 1, dy],
                      [0, 0, 1]], 
                      dtype=float)
        self._left_transform(A)
        return self
    
    def scaling(self, sx: float, sy: float):
        A = np.array([[sx, 0, 0],
                      [0, sy, 0],
                      [0, 0, 1]], 
                      dtype=float)
        self._left_transform(A)
        return self

    def rotation(self, cos_a: float, sin_a: float):
        A = np.array([[ cos_a, -sin_a, 0],
                      [ sin_a,  cos_a, 0],
                      [0, 0, 1]], 
                      dtype=float)
        self._left_transform(A)
        return self

    def symmetry_x(self):
        return self.scaling(1, -1)

    def symmetry_y(self):
        return self.scaling(-1, 1)

    def symmetry_origin(self):
        return self.scaling(-1, -1)
    
    def scale_about_point(self, sx: float, sy: float, cx: float, cy: float):
        return self.translation(-cx, -cy).scaling(sx, sy).translation(cx, cy)

    def rotate_about_point(self, cos_a: float, sin_a: float, cx: float, cy: float):
        return self.translation(-cx, -cy).rotation(cos_a, sin_a).translation(cx, cy)
    
    def apply_to_point(self, point: Point2D) -> Point2D:
        vec = point.toVector()
        transformed_vec = self._matrix @ vec
        return Point2D(transformed_vec[0] / transformed_vec[2],
                       transformed_vec[1] / transformed_vec[2])
