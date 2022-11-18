import cv2
from PySide2.QtWidgets import (
    QScrollBar, QGraphicsView, QGraphicsEllipseItem,
    QGraphicsPixmapItem, QGraphicsScene, QGraphicsRectItem
)
from PySide2.QtCore import (
    qDebug, QMimeData, Qt, Signal, QPointF, QObject, QThread, QPoint
)
from PySide2.QtGui import (
    QPixmap, QImage, QTransform, QBrush, QColor
)
from edge_draw import findCorners, findNearLines
from gftt import gftt
from enum import Enum
import numpy as np

class Mode(Enum):
    PREVIEW = 1
    ZOOMIN = 2


class LineDetectWorker(QObject):
    line_detect_finished = Signal(np.ndarray)
    
    def __init__(self, image) -> None:
        super().__init__()
        self.image = cv2.cvtColor( image, cv2.COLOR_BGR2GRAY)
        self.ed = None

    def detect_line(self):
        if self.ed is None:
            # init edge drawing
            self.ed = cv2.ximgproc.createEdgeDrawing()
            EDParams = cv2.ximgproc_EdgeDrawing_Params()
            EDParams.EdgeDetectionOperator = 2
            EDParams.AnchorThresholdValue = 8
            # EDParams.MinPathLength = 100     # try changing this value between 5 to 1000
            EDParams.PFmode = True         # defaut value try to swich it to True
            EDParams.MinLineLength = 13     # try changing this value between 5 to 100
            # EDParams.NFAValidation = False   # defaut value try to swich it to False
            # EDParams.Sigma = 0.8

            # printEDParams(EDParams)
            self.ed.setParams(EDParams)
        
        # detect lines
        self.ed.detectEdges(self.image)
        all_lines = self.ed.detectLines(self.image)
        self.line_detect_finished.emit(all_lines)


class MyGraphicsView(QGraphicsView):
    showCrossWidget = Signal()
    hideCrossWidget = Signal()
    finishPicking = Signal()
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.CrossCursor)
        # self.setCursor(Qt.CursorShape.WaitCursor)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.mode = Mode.PREVIEW
        self.mouseDragging = False
        self.lastPoint = None   # QPoint
        self.current_point_flag = 1
        self.point1 = None  # should be np.ndarray of shape (2,)
        self.point2 = None  # should be np.ndarray of shape (2,)
        self.image = None
        self.ed = None

    def load_scene_image(self, image):
        self.image = image
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width, channel = image.shape
        bytesPerLine = 3 * width
        qImg = QImage(image.data, width, height, bytesPerLine, QImage.Format_RGB888)
        self.img_item = QGraphicsPixmapItem(QPixmap.fromImage(qImg))

        # black margin
        self.margin = m = 500
        rect_item = QGraphicsRectItem(0, 0, width+m*2, height+m*2)
        rect_item.setBrush(QBrush(QColor(0, 0, 0)))


        scene = QGraphicsScene()
        scene.addItem(rect_item)
        scene.addItem(self.img_item)
        self.img_item.setPos(m, m)
        self.setScene(scene)

        # deprecated line segment in thread
        # self.ed_worker = LineDetectWorker(image)
        # self.ed_thread = QThread()
        # self.ed_worker.moveToThread(self.ed_thread)
        # self.ed_thread.started.connect(self.ed_worker.detect_line)
        # self.ed_worker.line_detect_finished.connect(self.ed_thread.quit)
        # self.ed_worker.line_detect_finished.connect(self._slot_line_detect_finished)
        # self.ed_thread.start()

    def _slot_line_detect_finished(self, all_lines):
        # deprecated line segment in thread
        print("Line detection finished!")
        self.all_lines = all_lines

    def previewMode(self):
        # print(self.img_item.mapRectToScene(self.img_item.boundingRect()))
        self.fitInView(self.img_item.mapRectToScene(self.img_item.boundingRect()), Qt.KeepAspectRatio)

        self.mode = Mode.PREVIEW
        self.hideCrossWidget.emit()
        self.removePoints()
        self.drawPoints()

    def zoominMode(self, zoomPoint : QPoint):
        # self.resetTransform()
        self.setTransform(QTransform.fromScale(2., 2.))
        self.centerOn(zoomPoint)

        self.mode = Mode.ZOOMIN
        self.showCrossWidget.emit()
        self.removePoints()

    def drawPoints(self):
        radius = 10
        m = self.margin
        if self.point1 is not None:
            circle = QGraphicsEllipseItem(
                self.point1[0]-radius+m, self.point1[1]-radius+m,
                2*radius, 2*radius)
            circle.setBrush(Qt.red)
            self.scene().addItem(circle)
        if self.point2 is not None:
            circle = QGraphicsEllipseItem(
                self.point2[0]-radius+m, self.point2[1]-radius+m,
                2*radius, 2*radius)
            circle.setBrush(Qt.red)
            self.scene().addItem(circle)


    def removePoints(self):
        for item in self.scene().items():
            if item.type() == 4:
                self.scene().removeItem(item)

    def updatePoint(self, point : np.ndarray, current_point_flag):
        point = self.gftt_snap(point)
        if current_point_flag == 1:
            self.point1 = point
        else:
            self.point2 = point
        if self.point1 is not None and self.point2 is not None:
            self.finishPicking.emit()
        return point

    def corner_cross_snap(self, point : np.ndarray) -> np.ndarray:
        # deprecated line segment and cross intersection
        lines = findNearLines(self.all_lines, point)
        corners = findCorners(lines)
        # print(corners)
        distances = []
        for corner in corners:
            dist = cv2.norm(corner, point, cv2.NORM_L2)
            distances.append(dist)
        
        fld = cv2.ximgproc.createFastLineDetector()
        img = fld.drawSegments(cv2.cvtColor( self.image, cv2.COLOR_BGR2GRAY), lines)
        for corner in corners:
            print(corner)
            img = cv2.circle(img, np.array(corner, dtype=np.int32), 2, (255,0,0), thickness=-1, lineType=cv2.LINE_AA)
        cv2.imshow("test", img)
        id = np.argmin(distances)
        print("snapped to", corners[id])
        return corners[id]

    def gftt_snap(self, point):
        src = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        point = point.astype(np.float)

        # returned float type, but only int part
        # corners.shape: [num, 2]
        corners = gftt(src, point).astype(np.float)
        distances = [cv2.norm(point, corner, cv2.NORM_L2SQR) for corner in corners]
        idx = np.argmin(distances)

        corner : np.ndarray = np.array([corners[idx]], dtype=np.float32)
        winSize = (2, 2)
        zeroZone = (-1, -1)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TermCriteria_COUNT, 40, 0.001)
        # REQUIRED corner to be np.ndarray of shape (num, 2), dtype=np.float32
        corner = cv2.cornerSubPix(src, corner, winSize, zeroZone, criteria)

        return corner[0]



    def mousePressEvent(self, event) -> None:
        # return super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            if self.mode == Mode.PREVIEW:
                qpoint_scene = self.mapToScene(event.pos())
                qp_img = self.img_item.mapFromScene(qpoint_scene)
                point_img = self.updatePoint(np.array([qp_img.x(), qp_img.y()]), self.current_point_flag)
                qpoint_scene = self.img_item.mapToScene(QPoint(point_img[0], point_img[1]))
                self.zoominMode(qpoint_scene)
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

    def mouseReleaseEvent(self, event) -> None:
        # return super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton and \
            self.mouseDragging == True:
            qpoint_scene = self.mapToScene(self.viewport().rect().center())
            qp_img = self.img_item.mapFromScene(qpoint_scene)
            point = np.array([qp_img.x(), qp_img.y()])
            self.updatePoint(point, self.current_point_flag)
            qDebug("dragging ended @" + str(point))
            self.mouseDragging = False
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.previewMode()

    def closeEvent(self, event) -> None:
        # return super().closeEvent(event)
        pass