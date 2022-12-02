from PySide2.QtCore import (
    Qt, QTimer, QThread, qDebug, QEvent, QPointF, QPoint, Signal, QObject
)
from PySide2.QtGui import (
    QPainter, QPaintEvent, QPen, QPixmap, QTransform, QImage, QMovie
)
from PySide2.QtWidgets import (
    QWidget, QPushButton, QSizePolicy, QVBoxLayout, 
    QGridLayout, QLabel
)
import cv2
import numpy as np
from pathlib import Path

from model.camera_model import CameraModel
from calib.rectification import StereoRectify
from measure.ruler import Ruler
from my_graphicsview import MyGraphicsView
from resize_graphicsview import ResizeGraphicsView
from measure.matcher import AutoMatcher, MATCHER_TYPE
import q_icons  # hold resources

class CrossWidget(QWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event) -> None:
        # return super().paintEvent(event)
        self.resize(200, 200)
        painter = QPainter(self)
        r = 1
        painter.setPen(QPen(Qt.red, r*2, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(0, 100-r, 200, 100-r)
        painter.drawLine(100-r, 0, 100-r, 200)

class AutoMatchWorker(QObject):
    match_finished = Signal(np.ndarray, np.ndarray)
    def __init__(self, leftImg, rightImg, point1, point2) -> None:
        super().__init__()
        print("Start automatcher..." , point1 , point2)
        self.leftImg = leftImg
        self.rightImg = rightImg
        self.point1 = point1
        self.point2 = point2
        self.matcher = AutoMatcher(self.leftImg, self.rightImg, method=MATCHER_TYPE.BRIEF) #BRIEF

    def start_match(self):
        _, top_kps = self.matcher.match(self.point1, show_result=False)
        size_list=np.array([kp.size for kp in top_kps])
        index=np.argmax(size_list)
        matched_point1 = top_kps[index].pt
        _, top_kps = self.matcher.match(self.point2, show_result=False)
        size_list=np.array([kp.size for kp in top_kps])
        index=np.argmax(size_list)        
        matched_point2 = top_kps[index].pt
        self.match_finished.emit(matched_point1, matched_point2)

class LoadingWidget(QLabel):
    def __init__(self) -> None:
        super().__init__("")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: rgba(255, 255, 255, 50);")
        self.spinnerMovie = QMovie(":/icons/spinner.gif")
        self.setMovie(self.spinnerMovie)

    def start(self):
        self.spinnerMovie.start()
        self.show()
        self.raise_()

    def stop(self):
        self.spinnerMovie.stop()
        self.hide()

class RectifyWorker(QObject):
    rectify_finished = Signal(np.ndarray, np.ndarray)
    def __init__(self, img_path, rectifier) -> None:
        super().__init__()
        self.img_path = img_path
        self.rectifier = rectifier

    def rectify_img(self):
        # read image
        sbs_img = cv2.imread(str(self.img_path)) 
        # rectify
        self.leftImg, self.rightImg = self.rectifier.rectify_image(sbs_img=sbs_img)
        # cv2.imwrite("left.jpg", self.leftImg)
        # cv2.imwrite("right.jpg", self.rightImg)
        # emit on success
        self.rectify_finished.emit(self.leftImg, self.rightImg)


class GuiMeasure(QWidget):
    def __init__(self, img_path, cam_path):
        super().__init__()
        # GUI init
        self._init_gui()
        self.setWindowTitle("Ruler Measure - LEFT")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.showMaximized()

        # info
        print("--------View and Measure--------")
        print("Viewing image:", img_path)
        print("Measure using:", cam_path)

        # load camera model
        self._load_camera_model(cam_path=cam_path)

        # init rectify thread
        self.rectify_worker = RectifyWorker(img_path, self.rectifier)
        self.rectify_thread = QThread()
        self.rectify_worker.moveToThread(self.rectify_thread)
        self.rectify_thread.started.connect(self.rectify_worker.rectify_img)
        self.rectify_worker.rectify_finished.connect(self.rectify_thread.quit)
        self.rectify_worker.rectify_finished.connect(self._slot_rectify_finished)
        self.rectify_thread.start()


    def _load_camera_model(self, cam_path=None):
        """Load the camera model. Default from example folder"""
        if cam_path is None:
            qDebug("Loading default camera model...")
            cam_path = Path(".") / "example" / "camera_model.json"
        else:
            qDebug("Loading selected camera model...")
        self.camera_model = CameraModel.load_model(cam_path)
        self.rectifier = StereoRectify(self.camera_model, None)


    def _init_gui(self):
        # graphic views
        self.leftView = MyGraphicsView()
        self.rightView = MyGraphicsView()

        # toolbox layout 
        # point 1 button
        self.point1_button = QPushButton("Point 1")
        sp = QSizePolicy()
        sp.setVerticalPolicy(QSizePolicy.Expanding)
        self.point1_button.setSizePolicy(sp)
        self.point1_button.clicked.connect(self._slot_point1_clicked)
        self.point1_button.setCheckable(True)

        # point 2 button
        self.point2_button = QPushButton("Point 2")
        self.point2_button.setSizePolicy(sp)
        self.point2_button.clicked.connect(self._slot_point2_clicked)
        self.point2_button.setCheckable(True)

        # finish button
        self.finish_button = QPushButton("Finish")
        self.finish_button.setSizePolicy(sp)
        self.finish_button.clicked.connect(self._slot_finish_clicked)
        self.finish_button.setDisabled(True)

        # organize layout
        self.tool_layout = QVBoxLayout()
        self.tool_layout.addWidget(self.point1_button)
        self.tool_layout.addWidget(self.point2_button, alignment=Qt.AlignHCenter)
        self.tool_layout.addWidget(self.finish_button)

        self.main_layout = QGridLayout(self)
        self.main_layout.addWidget(self.leftView, 0, 0)
        self.main_layout.addLayout(self.tool_layout, 0, 1)


    def showEvent(self, event) -> None:
        # return super().showEvent(event)
        event.accept()
        # initial state on start up
        self.current_view_flag = 1

        # create the cross widget 
        self.crossWidget = CrossWidget(self)
        self.main_layout.addWidget(self.crossWidget, 0, 0)
        self.crossWidget.hide()
        self.leftView.showCrossWidget.connect(lambda : self.crossWidget.raise_())
        self.leftView.hideCrossWidget.connect(lambda : self.crossWidget.lower())
        self.rightView.showCrossWidget.connect(lambda : self.crossWidget.raise_())
        self.rightView.hideCrossWidget.connect(lambda : self.crossWidget.lower())
        self.leftView.finishPicking.connect(
            lambda : self.finish_button.setDisabled(False)
        )
        self.rightView.finishPicking.connect(
            lambda : self.finish_button.setDisabled(False)
        )
        
        # create the loading icon
        self.loading_widget = LoadingWidget()
        self.main_layout.addWidget(self.loading_widget, 0, 0)
        self.loading_widget.raise_()
        self.loading_widget.start()

    def _slot_rectify_finished(self, leftImg, rightImg):
        self.leftImg = leftImg
        self.rightImg = rightImg

        self.leftView. load_scene_image(self. leftImg)
        self.rightView.load_scene_image(self.rightImg)
        self._slot_point1_clicked()

        # fit full photo into view
        QTimer.singleShot(50, self.leftView.previewMode)

        self.loading_widget.stop()
        self.loading_widget.lower()
        self.crossWidget.show()
        self.crossWidget.lower()
        QTimer.singleShot(100, self.widgetSizeMove) 

    def widgetSizeMove(self):
        centrePos = None
        if self.current_view_flag == 1:
            centrePos = self.leftView.viewport().mapTo(
                self, self.leftView.viewport().rect().center()
            )
        else:
            centrePos = self.rightView.viewport().mapTo(
                self, self.rightView.viewport().rect().center()
            )
        self.crossWidget.move(centrePos - self.crossWidget.rect().center() + QPoint(1,1))

    def event(self, event) -> bool:
        if event.type() == QEvent.Resize or \
            event.type() == QEvent.Move:
            QTimer.singleShot(10, self.widgetSizeMove)
        return super().event(event)

    def _slot_point1_clicked(self):
        self.point1_button.setChecked(True)
        self.point2_button.setChecked(False)
        if self.current_view_flag == 1:
            self.leftView.previewMode()
            self.leftView.current_point_flag = 1
        else:
            self.rightView.previewMode()
            self.rightView.current_point_flag = 1
        qDebug("selecting point 1...")

    def _slot_point2_clicked(self):
        self.point1_button.setChecked(False)
        self.point2_button.setChecked(True)
        if self.current_view_flag == 1:
            self.leftView.previewMode()
            self.leftView.current_point_flag = 2
        else:
            self.rightView.previewMode()
            self.rightView.current_point_flag = 2
        qDebug("selecting point 2...")

    def _slot_finish_clicked(self):
        if self.current_view_flag == 1:
            if self.leftView.point1 is None or self.leftView.point2 is None:
                qDebug("Not enough points in Left View")
            else:
                # start another thread to automatch
                self.am_worker = AutoMatchWorker(
                    self.leftImg, self.rightImg, 
                    self.leftView.point1, self.leftView.point2
                )
                self.am_thread = QThread()
                self.am_worker.moveToThread(self.am_thread)
                self.am_thread.started.connect(self.am_worker.start_match)
                self.am_worker.match_finished.connect(self.am_thread.quit)
                self.am_worker.match_finished.connect(self._slot_matched_finished)
                self.am_thread.start()

                # switch to right view
                # take UI to the right View
                self.finish_button.setDisabled(True)
                self.current_view_flag = 2
                self.main_layout.replaceWidget(self.leftView, self.rightView)
                self.setWindowTitle("Ruler Measure - Right")
                self.loading_widget.start()

        else:
            print("Start measuring..." , self.rightView.point1 , self.rightView.point2)
            # calculate length - TODO
            ruler = Ruler(self.rectifier.Q, self.leftImg, self.rightImg)
            ruler.update_point1(self.leftView.point1, self.rightView.point1)
            ruler.update_point2(self.leftView.point2, self.rightView.point2)
            len = ruler.measure_segment()
            print("measured length:", len)
            # show result
            result = ruler.get_result()
            print(result.shape)
            self.result_view = ResizeGraphicsView()
            self.result_view.load_scene_image(result)
            self.result_view.showMaximized()
            QTimer.singleShot(50, self.result_view.previewMode)
            self.close()

    def _slot_matched_finished(self, matched_point1, matched_point2):
        print("recieved matched points:", matched_point1, matched_point2)
        matched_point1 = np.array(matched_point1)
        matched_point2 = np.array(matched_point2)
        self.rightView.updatePoint(matched_point1, 1)
        self.rightView.updatePoint(matched_point2, 2)
        self.rightView.drawPoints()
        self.loading_widget.stop()
        QTimer.singleShot(50, self.widgetSizeMove)
        QTimer.singleShot(50, self._slot_point1_clicked)