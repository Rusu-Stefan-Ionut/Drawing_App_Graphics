import sys
import numpy as np

from modes import Mode
from Point2D import Point2D
from transformare2D import Transform2D
from parametric_curve import ParametricCurve
from interpolation_curve import InterpolationCurve


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

        # Draw poligon
        self.points: list[Point2D] = [] 
        self.drag_index: int | None = None
        self.drag_threshold: int = 10
        self.mode: Mode = Mode.EDIT
        self.point_radius: int = 6

        # Transformations
        self.T: Transform2D = Transform2D()
        self.drag_start: QPoint | None = None
        self.original_points: list[Point2D] | None = None

        self.geometric_center: Point2D | None = None
        self.start_angle: np.ndarray | None = None

        # Parametric cuve
        self.curve = ParametricCurve()

        self.L = self.width()
        self.H = self.height()
        
        # interpolation curve
        self.interpolation = InterpolationCurve()
        self.interp_method = "lagrange"

        # Keyboard functions
        self.keymap = {
        Qt.Key_E: self.set_mode_edit,
        Qt.Key_T: self.set_mode_transform,
        Qt.Key_C: self.set_mode_parametric,
        Qt.Key_I: self.set_mode_interpolation,

        Qt.Key_1: self.set_method_lagrange,  
        Qt.Key_2: self.set_method_newton  
        }

        # Qt info
        self.setMinimumSize(500, 400)
        self.setFocusPolicy(Qt.StrongFocus)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        pen = QPen(QColor(30, 30, 30))
        pen.setWidth(2)
        painter.setPen(pen)

        if self.mode in (Mode.EDIT, Mode.TRANSFORM, Mode.INTERPOLATION):
            for p in self.points:
                painter.setBrush(QColor(255, 255, 255))
                painter.drawEllipse(QPointF(p.x, p.y), self.point_radius, self.point_radius)

        if self.mode == Mode.TRANSFORM and len(self.points) > 1:
            for i in range(len(self.points) - 1):
                painter.drawLine(
                    QPointF(self.points[i].x, self.points[i].y),
                    QPointF(self.points[i+1].x, self.points[i+1].y)
                )
            painter.drawLine(
                QPointF(self.points[-1].x, self.points[-1].y),
                QPointF(self.points[0].x, self.points[0].y)
            )
        elif self.mode == Mode.PARAMETRIC and self.curve.points:
            pen = QPen(QColor(30, 30, 30))
            pen.setWidth(2)
            painter.setPen(pen)

            for i in range(len(self.curve.points) - 1):
                p1 = self.curve.points[i]
                p2 = self.curve.points[i+1]
                painter.drawLine(QPointF(p1.x, p1.y), QPointF(p2.x, p2.y))

            #draw axes
            axis_pen = QPen(QColor(0, 0, 255))
            axis_pen.setWidth(3)
            painter.setPen(axis_pen)

            origin = self.curve.transformed_origin(self.L, self.H)

            A = Point2D(0, origin.y)
            B = Point2D(self.L, origin.y)
            self.draw_arrow(painter, A, B)

            C = Point2D(origin.x, 0)
            D = Point2D(origin.x, self.H)
            self.draw_arrow(painter, D, C)

        elif self.mode == Mode.INTERPOLATION:
            pts = self.interpolation.points
            if len(pts) > 1:
                for i in range(len(pts) - 1):
                    p1 = pts[i]
                    p2 = pts[i + 1]
                    painter.drawLine(QPointF(p1.x, p1.y),
                                    QPointF(p2.x, p2.y))

    def resizeEvent(self, event):
        self.L = self.width()
        self.H = self.height()

        if self.mode == Mode.PARAMETRIC and self.curve.raw_points:
            self.curve.transform(self.L, self.H)

        self.update()
        return super().resizeEvent(event)

    def mousePressEvent(self, event):

        if Mode.EDIT == self.mode: 

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
                
        elif Mode.TRANSFORM == self.mode:

            self.geometric_center = self.compute_centroid()
                

            if event.button() == Qt.LeftButton:
                self.drag_start = event.pos()
                

            elif event.button() == Qt.RightButton:
                
                self.drag_start = event.pos()
                dx = event.x() - self.geometric_center.x
                dy = event.y() - self.geometric_center.y
                self.start_angle = np.arctan2(dy, dx)
        
        elif Mode.INTERPOLATION == self.mode:

            if event.button() == Qt.LeftButton:
                p = Point2D(event.x(), event.y())

                if self.interpolation.can_add_point(p):
                    self.interpolation.add_point(p)
                    self.points.append(p)
                else:
                    print("Invalid point: x must be strictly increasing.")

                self.update()

            elif event.button() == Qt.RightButton:
                if self.interp_method == "lagrange":
                    self.interpolation.compute_lagrange()
                else:
                    self.interpolation.compute_newton()

                self.update()

    def mouseMoveEvent(self, event):

        if Mode.EDIT == self.mode:
            if self.drag_index is not None and (event.buttons() & Qt.LeftButton):
                pos = event.pos()
                self.points[self.drag_index].x = pos.x()
                self.points[self.drag_index].y = pos.y()
                self.update()

        elif Mode.TRANSFORM == self.mode:
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
                    self.T.scale_about_point(factor, factor, cx, cy)
                    self.apply_transformation()

                else:
                    self.T.translation(dx, dy)
                    self.apply_transformation()
                    
                self.drag_start = event.pos()
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

                self.T.rotate_about_point(cos_a, sin_a, cx, cy)
                self.apply_transformation()
                
                self.start_angle = current_angle

                self.update()

    def mouseReleaseEvent(self, event):
        if self.mode == Mode.TRANSFORM:
            self.drag_start = None
            self.start_angle = None
        if event.button() == Qt.LeftButton and self.drag_index is not None:
            self.drag_index = None
            self.setCursor(Qt.ArrowCursor)
            self.update()
        self.start_angle = None

    def keyPressEvent(self, event):
        func = self.keymap.get(event.key())
        if func:
            func()
            self.update()
        else:
            super().keyPressEvent(event)

    def set_mode_edit(self):
        self.mode = Mode.EDIT
        print("Mode: EDIT")

    def set_mode_transform(self):
        self.mode = Mode.TRANSFORM
        self.T = Transform2D()
        # if self.original_points is None:
        self.original_points = [Point2D(p.x, p.y) for p in self.points]
        print("Mode: TRANSFORM")

    def set_mode_parametric(self):
        self.mode = Mode.PARAMETRIC
        self.draw_parametric_curve(-5, 5, 100, self.curve.spiral)
        print("Mode: PARAMETRIC")

    def set_mode_interpolation(self):
        self.mode = Mode.INTERPOLATION
        self.points.clear()
        self.interpolation.control_points = []
        self.interpolation.points = []
        print("Mode: INTERPOLATION")

    def set_method_lagrange(self):
        self.interp_method = "lagrange"
        print("Interpolation method: LAGRANGE")

    def set_method_newton(self):
        self.interp_method = "newton"
        print("Interpolation method: NEWTON")

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
    
    def apply_transformation(self):
        self.points = [self.T.apply_to_point(p) for p in self.original_points]
        self.update()


    def draw_parametric_curve(self, a, b, n, *args):
        self.curve.compute_points(a, b, n, *args)
        self.curve.transform(self.L, self.H)
        self.update()

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