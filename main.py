import sys
import numpy as np

from Point2D import Point2D
from transformare2D import Transform2D

from PyQt5.QtGui import QPainter, QPixmap, QImage, QPen, QColor, QIcon
from PyQt5.QtCore import Qt, QPoint, QPointF, QRect, QSize, pyqtSignal
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QAction,
    QFileDialog,
    QColorDialog,
    QSpinBox,
)


class Canvas(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.points: list[Point2D] = [] 
        self.drag_index: int | None = None
        self.drag_threshold: int = 10
        self.mode = "edit"
        self.point_radius: int = 6

        #Transformations
        self.drag_start: QPoint | None = None
        self.original_points: list[Point2D] | None = None

        self.geometric_center: Point2D | None = None
        self.start_angle: np.ndarray | None = None

        #parametric cuve
        self.curve_points: list[Point2D] = []
        # self.L = self.width()
        # self.H = self.height()

        self.L = 800
        self.H = 500

        self.setMinimumSize(400, 300)
        self.setFocusPolicy(Qt.StrongFocus)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        pen = QPen(QColor(30, 30, 30))
        pen.setWidth(2)
        painter.setPen(pen)

        if self.mode == "transform" and len(self.points) > 1:
            for i in range(len(self.points) - 1):
                painter.drawLine(
                    QPointF(self.points[i].x, self.points[i].y),
                    QPointF(self.points[i+1].x, self.points[i+1].y)
                )
            painter.drawLine(
                QPointF(self.points[-1].x, self.points[-1].y),
                QPointF(self.points[0].x, self.points[0].y)
            )
        elif self.mode == "parametric_curve" and len(self.curve_points) > 1:
            for i in range(len(self.curve_points) - 1):
                p1, p2 = self.curve_points[i], self.curve_points[i+1]
                painter.drawLine(QPointF(p1.x, p1.y),QPointF(p2.x, p2.y))

            axis_pen = QPen(QColor(0, 0, 255))  # Blue
            axis_pen.setWidth(3)
            painter.setPen(axis_pen)

            origin = Point2D(0,0)
            origin = self.apply_tranformations([origin])[0]

            # Draw axes
            p_x_end = Point2D(self.L, origin.y)
            p_y_end = Point2D(origin.x, 0)
            # painter.drawLine(QPointF(origin.x, origin.y), QPointF(p_x_end.x, p_x_end.y))
            # painter.drawLine(QPointF(origin.x, origin.y), QPointF(p_y_end.x, p_y_end.y))   
            self.draw_arrow(painter, origin, p_x_end)
            self.draw_arrow(painter, origin, p_y_end) 

        for p in self.points:
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(QPointF(p.x, p.y), self.point_radius, self.point_radius)

    def draw_arrow(self, painter: QPainter, start: Point2D, end: Point2D, size=10):
        painter.drawLine(QPointF(start.x, start.y), QPointF(end.x, end.y))
        
        dx = end.x - start.x
        dy = end.y - start.y
        length = (dx**2 + dy**2)**0.5
        if length == 0:
            return

        ux = dx / length
        uy = dy / length

        perp_x = -uy
        perp_y = ux

        wing1 = Point2D(end.x - ux*size + perp_x*size/2, end.y - uy*size + perp_y*size/2)
        wing2 = Point2D(end.x - ux*size - perp_x*size/2, end.y - uy*size - perp_y*size/2)

        painter.drawLine(QPointF(end.x, end.y), QPointF(wing1.x, wing1.y))
        painter.drawLine(QPointF(end.x, end.y), QPointF(wing2.x, wing2.y))

    def mousePressEvent(self, event):

        if "edit" == self.mode: 
            if event.button() == Qt.LeftButton:
                pos = event.pos()
                
                for i, p in enumerate(self.points):
                    mouse_point = Point2D(pos.x(), pos.y())
                    if self.euclidian_distance(p, mouse_point) <= self.drag_threshold:
                        self.drag_index = i
                        self.setCursor(Qt.ClosedHandCursor)
                        self.update()
                        return
                
                self.points.append(Point2D(pos.x(), pos.y()))
                self.update()
                
        elif "transform" == self.mode:
            self.geometric_center = self.compute_centroid()
            self.original_points = [Point2D(p.x, p.y) for p in self.points]

            if event.button() == Qt.LeftButton:
                self.drag_start = event.pos()
                

            elif event.button() == Qt.RightButton:
                
                self.drag_start = event.pos()
                dx = event.x() - self.geometric_center.x
                dy = event.y() - self.geometric_center.y
                self.start_angle = np.arctan2(dy, dx)
            

    def mouseMoveEvent(self, event):

        if "edit" == self.mode:
            if self.drag_index is not None and (event.buttons() & Qt.LeftButton):
                pos = event.pos()
                self.points[self.drag_index].x = pos.x()
                self.points[self.drag_index].y = pos.y()
                self.update()

        elif "transform" == self.mode:
            if (event.buttons() & Qt.LeftButton) and self.drag_start is not None:
                dx = event.x() - self.drag_start.x()
                dy = event.y() - self.drag_start.y()

                shift_pressed = QApplication.keyboardModifiers() & Qt.ShiftModifier

                if shift_pressed:
                    dist = (dx**2 + dy**2) ** 0.5
                    factor = 1.0 + (dist / 10.0) * 0.1

                    # direction: shrinking or enlarging
                    if dx + dy < 0:
                        factor = 1/factor

                    cx, cy = self.geometric_center.x, self.geometric_center.y
                    T = Transform2D().scale_about_point(factor, factor, cx, cy)
                    self.apply_transformation(T)
                    self.update()

                else:
                    T = Transform2D().translation(dx, dy)
                    self.apply_transformation(T)
                    self.update()

            if (event.buttons() & Qt.RightButton) and self.drag_start is not None:
                cx, cy = self.geometric_center.x, self.geometric_center.y

                # current angle
                dx = event.x() - cx
                dy = event.y() - cy
                current_angle = np.arctan2(dy, dx)

                delta_angle = current_angle - self.start_angle

                cos_a = np.cos(delta_angle)
                sin_a = np.sin(delta_angle)

                T = Transform2D().rotate_about_point(cos_a, sin_a, cx, cy)
                self.apply_transformation(T)

                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drag_index is not None:
            self.drag_index = None
            self.setCursor(Qt.ArrowCursor)
            self.update()
        self.start_angle = None

    def keyPressEvent(self, event):     
        key = event.key()

        match key:
            case Qt.Key_E:
                self.mode = "edit"
                print("Mode:", self.mode)
                self.update()
                return
            case Qt.Key_T:
                self.mode = "transform"

                self.drag_start = None
                self.original_points = None
                self.start_angle = None

                print("Mode:", self.mode)
                self.update()
                return
            
            case Qt.Key_C:
                self.mode = "parametric_curve"
                self.draw_parametric_curve(-3, 3, 100, self.spiral)
                print("Mode:", self.mode)
                self.update()
                return

            case _:
                super().keyPressEvent(event)

    def euclidian_distance(self, p1: Point2D, p2: Point2D) -> float:
        dx = p1.x - p2.x
        dy = p1.y - p2.y
        return (dx * dx + dy * dy) ** 0.5
    
    def compute_centroid(self) -> Point2D:
        if not self.points:
            return Point2D(0, 0)
        
        x_sum = sum(p.x for p in self.points)
        y_sum = sum(p.y for p in self.points)
        n = len(self.points)
        return Point2D(x_sum / n, y_sum / n)
    
    def apply_transformation(self, T: Transform2D):
        self.points = [T.apply_to_point(p) for p in self.original_points]
        self.update()


    def draw_parametric_curve(self, a: float, b: float, n: int, *args):
        #S
        list_points = self.compute_parametric_points(a, b, n, *args)
        self.curve_points = self.apply_tranformations(list_points)
        

    def apply_tranformations(self, points: list[Point2D]):
        #S'
        points = self.translate_to_first_quadrant(points)
        #S''
        points = self.scale_to_fit(points, self.L, self.H)
        #S'''
        points = self.center_points(points, self.L, self.H)
        #S''''
        points = self.flip_Oy(points, self.H)
        
        return points

    def compute_parametric_points(self, a, b, n, *args):
        points = []
        for i in range(n+1):
            u = a + i * (b - a) / n
            if len(args) == 1:
                pred_func = args[0]
                f_u, g_u = pred_func(u)
                points.append(Point2D(f_u, g_u))
            elif len(args) == 2:
                f,g = args[0], args[1]
                points.append(Point2D(f(u), g(u)))
            else:
                raise ValueError("Must pass either 1 or 2 functions")
        return points

    def translate_to_first_quadrant(self, points):
        min_x = min(p.x for p in points)
        min_y = min(p.y for p in points)
        return [Point2D(p.x - min_x, p.y - min_y) for p in points]
    
    def scale_to_fit(self, points, L, H):
        max_x = max(p.x for p in points)
        max_y = max(p.y for p in points)

        if max_x == 0: max_x = 1
        if max_y == 0: max_y = 1

        S = min(H / max_y, L / max_x)

        return [Point2D(p.x * S, p.y * S) for p in points]

    def center_points(self, points, L, H):
        max_x = max(p.x for p in points)
        max_y = max(p.y for p in points)
        dx = (L - max_x) / 2
        dy = (H - max_y) / 2

        return [Point2D(p.x + dx, p.y + dy) for p in points]

    def flip_Oy(self, points, H):
        return [Point2D(p.x, H - p.y) for p in points]
    

    def ellipse(self, u, c=100, d=50):
        return c * np.cos(u), d * np.sin(u)
    def spiral(self, u):
        return u * np.cos(u), u * np.sin(u) 
    def parabola(self, u): 
        return u, u-1


    

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("main.ui", self)
        self.canvas = Canvas(self)
        self.setCentralWidget(self.canvas)
        self.setWindowTitle("Drawing App")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()