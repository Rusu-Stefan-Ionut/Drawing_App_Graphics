import numpy as np

class Point2D:
    def __init__(self, x: float, y: float):
        self.__x = x
        self.__y = y
    
    @property
    def x(self):
        return self.__x
    
    @x.setter
    def x(self, value):
        self.__x = value

    @property
    def y(self):
        return self.__y
    
    @y.setter
    def y(self, value):
        self.__y = value

    def toVector(self):
        return np.array([self.x, self.y, 1.0])
    
    @classmethod
    def fromVector(self, vector: np.ndarray):
        if vector[2] == 0:
            raise ValueError("Can't divide by 0")
        return cls(vector[0]/vector[2], vector[1]/vector[2])