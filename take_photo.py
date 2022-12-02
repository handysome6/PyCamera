from Cambind import CameraHolder
from pathlib import Path
import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify
Notify.init("demo")

from PySide2.QtWidgets import (
    QWidget, QApplication, QPushButton, QSizePolicy, 
    QVBoxLayout, QHBoxLayout, QFileDialog, QLabel, QGridLayout
)
from PySide2.QtGui import QWindow, QIcon, QPalette, QColor
from PySide2.QtCore import QSize, Qt, QThread, QObject

import q_icons
from gui_measure import GuiMeasure, LoadingWidget

from test_scp.test_scp import scp

cam_path = "/home/jetson/PyCamera/example/camera_model.json"

class TakePhotoWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CameraApp - Python")
        self.showMaximized()

        # GUI component
        self.preview_area_holder = QLabel("Loading cameras...")
        self.preview_area_holder.setAlignment(Qt.AlignCenter)
        self.preview_area_holder.setAutoFillBackground(True)
        self.preview_area_holder.setPalette(QPalette(QColor("black")))
        # self.preview_area_holder.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._init_toolbar()
        # add to layout
        self.main_layout = QGridLayout(self)
        self.main_layout.addWidget(self.preview_area_holder, 0, 0)
        self.main_layout.addLayout(self.tool_layout, 0, 1)


        #start camera capture thread
        self.cam_thread = QThread()
        self.cam_holder = CameraHolder()
        self.cam_holder.moveToThread(self.cam_thread)
        self.cam_thread.started.connect(self.cam_holder.initAll)
        self.cam_holder.xWindowReady.connect(self._slot_replace_cam)
        self.cam_holder.captureSucceed.connect(self._slot_capture_succeed)
        self.cam_thread.start()

        self.capture_notice = Notify.Notification.new("Image Captured!")
        self.capture_notice.set_timeout(1000)


    def _init_toolbar(self):
        # camera button
        camera_button = QPushButton()
        icon = QIcon(":/icons/camera.png")
        camera_button.setIcon(icon)
        camera_button.setIconSize(QSize(85, 85))
        camera_button.setFlat(True)
        sp = QSizePolicy()
        sp.setVerticalPolicy(QSizePolicy.Expanding)
        camera_button.setSizePolicy(sp)
        camera_button.clicked.connect(self._slot_capture_clicked)

        # folder open images
        folder_button = QPushButton()
        icon = QIcon(":/icons/folder.png")
        folder_button.setIcon(icon)
        folder_button.setIconSize(QSize(85, 85))
        folder_button.setFlat(True)
        folder_button.setSizePolicy(sp)
        folder_button.clicked.connect(self._slot_folder_clicked)

        # measure images
        measure_button = QPushButton()
        icon = QIcon(":/icons/ruler.png")
        measure_button.setIcon(icon)
        measure_button.setIconSize(QSize(85, 85))
        measure_button.setFlat(True)
        measure_button.setSizePolicy(sp)
        measure_button.clicked.connect(self._slot_measure_clicked)
        measure_button.setDisabled(True)
        self.measure_button = measure_button

        # organize layout
        self.tool_layout = QVBoxLayout()
        self.tool_layout.addWidget(folder_button)
        self.tool_layout.addWidget(camera_button, alignment=Qt.AlignHCenter)
        self.tool_layout.addWidget(measure_button)

    def _slot_replace_cam(self, xid):
        # fetch embedded window handle, embed x11 window to qt widget
        preview_window_xid = xid
        embbed_preview_window = QWindow.fromWinId(preview_window_xid)
        embbed_preview_widget = QWidget.createWindowContainer(embbed_preview_window)
        self.main_layout.replaceWidget(self.preview_area_holder, embbed_preview_widget)

    def _slot_capture_clicked(self):
        """slot to take snapshot for both cameras"""
        # notify via bubble windows
        # self.capture_notice.show()
        print("capturing camera...")
        self.cam_holder.captureFrame()

    def _slot_capture_succeed(self, path):
        print("Capture Succeed!")
        self.capture_notice.show()
        self.cap_img_path = path
        scp(path)
        self.measure_button.setDisabled(False)

    def _slot_folder_clicked(self):
        str_path, _ = QFileDialog.getOpenFileName(self, "Select a sbs photo...", "/home/jetson/NewCam", "Images (*.png *.jpg)")
        if str_path != '':
            img_path = Path(str_path)
            print("Selected photo: " + str(img_path))
            self.measure_win = GuiMeasure(str(img_path), cam_path)
            self.measure_win.show()
        
    def _slot_measure_clicked(self):
        self.measure_win = GuiMeasure(self.cap_img_path, cam_path)
        self.measure_win.show()

    def closeEvent(self, event):
        """overriding default close event for qt window"""
        print("Exiting take photo window...")
        exit(0)
