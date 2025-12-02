import sys
import numpy as np

from Point2D import Point2D
from transformare2D import Transformare2D

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
        self.draw_polygon: bool = False
        self.mode = "edit"
        self.point_radius: int = 6

        #Transformations
        self.drag_start: QPoint | None = None
        self.original_points: list[Point2D] | None = None

        self.geometric_center: float | None = None
        self.start_angle: float | None = None

        self.setMinimumSize(400, 300)
        self.setFocusPolicy(Qt.StrongFocus)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        pen = QPen(QColor(30, 30, 30))
        pen.setWidth(2)
        painter.setPen(pen)

        if self.draw_polygon and len(self.points) > 1:
            for i in range(len(self.points) - 1):
                painter.drawLine(
                    QPointF(self.points[i].x, self.points[i].y),
                    QPointF(self.points[i+1].x, self.points[i+1].y)
                )
            painter.drawLine(
                QPointF(self.points[-1].x, self.points[-1].y),
                QPointF(self.points[0].x, self.points[0].y)
            )

        for p in self.points:
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(QPointF(p.x, p.y), self.point_radius, self.point_radius)

    def mousePressEvent(self, event):

        if "edit" == self.mode: 
            if event.button() == Qt.LeftButton:
                pos = event.pos()
                
                for i, p in enumerate(self.points):
                    if self._distance(p, pos) <= self.drag_threshold:
                        self.drag_index = i
                        self.setCursor(Qt.ClosedHandCursor)
                        self.update()
                        return
                
                self.points.append(Point2D(pos.x(), pos.y()))
                self.update()
                
        elif "transform" == self.mode:
            if event.button() == Qt.LeftButton:
                self.drag_start = event.pos()
                self.original_points = [Point2D(p.x, p.y) for p in self.points]
                self.geometric_center = self.compute_centroid()

                self.scaling_mode = event.modifiers() & Qt.ShiftModifier

            elif event.button() == Qt.RightButton:
                self.drag_start = event.pos()
                self.original_points = [Point2D(p.x, p.y) for p in self.points]

                self.geometric_center = self.compute_centroid()

                dx = event.x() - self.geometric_center.x()
                dy = event.y() - self.geometric_center.y()
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

                if self.scaling_mode:
                    dist = (dx**2 + dy**2) ** 0.5
                    factor = 1.0 + (dist / 10.0) * 0.1

                    # direction: shrinking or enlarging
                    if dx + dy < 0:
                        factor = 1/factor

                    T = Transformare2D() \
                        .translatie(-self.geometric_center.x(), -self.geometric_center.y()) \
                        .scalare(factor, factor) \
                        .translatie(self.geometric_center.x(), self.geometric_center.y())

                    self.apply_transformation(T)
                    
                    self.update()

                else:
                    T = Transformare2D().translatie(dx, dy)

                    self.apply_transformation(T)

                    self.update()

            if (event.buttons() & Qt.RightButton) and self.drag_start is not None:
                cx, cy = self.geometric_center.x(), self.geometric_center.y()

                # current angle
                dx = event.x() - cx
                dy = event.y() - cy
                current_angle = np.arctan2(dy, dx)

                delta_angle = current_angle - self.start_angle

                cos_a = np.cos(delta_angle)
                sin_a = np.sin(delta_angle)

                T = Transformare2D() \
                        .translatie(-cx, -cy) \
                        .rotatie(cos_a, sin_a) \
                        .translatie(cx, cy)

                self.apply_transformation(T)

                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drag_index is not None:
            self.drag_index = None
            self.setCursor(Qt.ArrowCursor)
            self.update()

    def keyPressEvent(self, event):     
        key = event.key()

        match key:
            case Qt.Key_E:
                self.mode = "edit"
                print("Mode:", self.mode)
                self.draw_polygon = False
                self.update()
                return
            case Qt.Key_T:
                self.mode = "transform"
                
                self.draw_polygon = True
                self.drag_start = None
                self.original_points = None
                self.start_angle = None
                self.scaling_mode = False

                print("Mode:", self.mode)
                self.update()
                return
            
            case _:
                super().keyPressEvent(event)

    def _distance(self, p1: Point2D, p2: QPoint) -> float:
        dx = p1.x - p2.x()
        dy = p1.y - p2.y()
        return (dx * dx + dy * dy) ** 0.5
    
    def compute_centroid(self):
        if not self.points:
            return QPointF(0, 0)

        x_sum = sum(p.x for p in self.points)
        y_sum = sum(p.y for p in self.points)
        n = len(self.points)
        return QPointF(x_sum / n, y_sum / n)
    
    def apply_transformation(self, T: Transformare2D):
        self.points = [T.apply_to_point(p) for p in self.original_points]
        self.update()


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