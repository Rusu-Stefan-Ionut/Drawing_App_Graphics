import sys
from PyQt5.QtGui import QPainter, QPixmap, QImage, QPen, QColor, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QSize, pyqtSignal
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
        self.points: list[QPoint] = [] 
        self.drag_index: int | None = None
        self.drag_threshold: int = 10
        self.draw_polygon: bool = False
        self.point_radius: int = 6

        self.setMinimumSize(400, 300)
        self.setFocusPolicy(Qt.StrongFocus)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        pen = QPen(QColor(30, 30, 30))
        pen.setWidth(2)
        painter.setPen(pen)

        
        if self.draw_polygon:
            for i in range(len(self.points) - 1):
                painter.drawLine(self.points[i], self.points[i + 1])
            
            painter.drawLine(self.points[-1], self.points[0])

        for p in self.points:
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(p, self.point_radius, self.point_radius)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            
            for i, p in enumerate(self.points):
                if self._distance(p, pos) <= self.drag_threshold:
                    self.drag_index = i
                    self.setCursor(Qt.ClosedHandCursor)
                    self.update()
                    return
            
            self.points.append(QPoint(pos))
            self.update()

    def mouseMoveEvent(self, event):
        if self.drag_index is not None and (event.buttons() & Qt.LeftButton):
            pos = event.pos()
            self.points[self.drag_index] = QPoint(pos)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drag_index is not None:
            self.drag_index = None
            self.setCursor(Qt.ArrowCursor)
            self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_T:
            self.draw_polygon = not self.draw_polygon
            self.update()
        else:
            super().keyPressEvent(event)

    def _distance(self, p1: QPoint, p2: QPoint) -> float:
        dx = p1.x() - p2.x()
        dy = p1.y() - p2.y()
        return (dx * dx + dy * dy) ** 0.5


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