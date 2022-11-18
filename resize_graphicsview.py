import cv2
from PySide2.QtWidgets import (
    QScrollBar, QGraphicsView, QGraphicsEllipseItem,
    QGraphicsPixmapItem, QGraphicsScene
)
from PySide2.QtCore import (
    qDebug, QMimeData, Qt, Signal, QPointF, QObject, QThread, QPoint
)
from PySide2.QtGui import (
    QPixmap, QImage
)
from edge_draw import findCorners, findNearLines
from enum import Enum
import numpy as np

class Mode(Enum):
    PREVIEW = 1
    ZOOMIN = 2


class ResizeGraphicsView(QGraphicsView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.CrossCursor)
        # self.setCursor(Qt.CursorShape.WaitCursor)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.mode = Mode.PREVIEW
        self.mouseDragging = False
        self.image = None

    def load_scene_image(self, image):
        self.image = image
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width, channel = image.shape
        bytesPerLine = 3 * width
        qImg = QImage(image.data, width, height, bytesPerLine, QImage.Format_RGB888)
        item = QGraphicsPixmapItem(QPixmap.fromImage(qImg))

        scene = QGraphicsScene()
        scene.addItem(item)
        self.setScene(scene)


    def previewMode(self):
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        self.mode = Mode.PREVIEW

    def zoominMode(self, zoomPoint : QPoint):
        self.resetTransform()
        self.centerOn(zoomPoint)
        self.mode = Mode.ZOOMIN

    def mousePressEvent(self, event) -> None:
        # return super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            if self.mode == Mode.PREVIEW:
                qp = self.mapToScene(event.pos())
                self.zoominMode(qp)
            else:
                # qDebug("dragging started @"+str(self.mapToScene(self.viewport().rect().center())))
                self.mouseDragging = True
                self.lastPoint = event.pos()
                self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mouseMoveEvent(self, event) -> None:
        # return super().mouseMoveEvent(event)
        if self.mouseDragging:
            delta : QPoint = event.pos() - self.lastPoint
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            self.lastPoint = event.pos()

    def mouseDoubleClickEvent(self, event) -> None:
        # return super().mouseDoubleClickEvent(event)
        if event.button() == Qt.LeftButton:
            self.previewMode()