import cv2
from Cambind import CameraHolder
from pathlib import Path
from shutil import copy
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
from uploadfiles import upload
from calib.rectification import StereoRectify
from model.camera_model import CameraModel
from sensor.uart_imu import IMU

cam_path = "/home/jetson/PyCamera/example/camera_model.json"
export_path = "/home/jetson/image_export"

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
        # init imu
        self._init_imu()

        #start camera capture thread
        self.cam_thread = QThread()
        self.cam_holder = CameraHolder()
        self.cam_holder.moveToThread(self.cam_thread)
        self.cam_thread.started.connect(self.cam_holder.initAll)
        self.cam_holder.xWindowReady.connect(self._slot_replace_cam)
        self.cam_holder.captureSucceed.connect(self._slot_capture_succeed)
        self.cam_thread.start()

        self.camera_model = None
        self.rectifier = None

        self.capture_notice = Notify.Notification.new("Image Captured!", icon="/home/jetson/icons/shutter.png")
        self.capture_notice.set_timeout(1500)

        self.success_notice = Notify.Notification.new("Upload successful", icon="/home/jetson/icons/success.png")
        self.success_notice.set_timeout(1500)

        self.fail_notice = Notify.Notification.new("Upload failed", icon="/home/jetson/icons/fail.png")
        self.fail_notice.set_timeout(1500)


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

        # upload image as project - DEMO
        upload_button = QPushButton("Upload")
        upload_button.clicked.connect(self._slot_upload_clicked)
        sp = QSizePolicy()
        sp.setHorizontalPolicy(QSizePolicy.Fixed)
        upload_button.setSizePolicy(sp)
        upload_button.resize(85, upload_button.height())

        # organize layout
        self.tool_layout = QVBoxLayout()
        self.tool_layout.addWidget(folder_button)
        self.tool_layout.addWidget(camera_button, alignment=Qt.AlignHCenter)
        self.tool_layout.addWidget(measure_button)
        self.tool_layout.addWidget(upload_button)

    def _slot_replace_cam(self, xid):
        # fetch embedded window handle, embed x11 window to qt widget
        preview_window_xid = xid
        embbed_preview_window = QWindow.fromWinId(preview_window_xid)
        embbed_preview_widget = QWidget.createWindowContainer(embbed_preview_window)
        self.main_layout.replaceWidget(self.preview_area_holder, embbed_preview_widget)

    def _slot_capture_clicked(self):
        """slot to take snapshot for both cameras"""
        print("capturing camera...")
        self.cam_holder.captureFrame()

    def _slot_capture_succeed(self, path):
        print("Capture Succeed!")
        # notify via bubble windows
        self.capture_notice.show()
        self.cap_img_path = path
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

    def _slot_upload_clicked(self):
        str_path, _ = QFileDialog.getOpenFileName(self, 
            "Select to upload a photo...",  # Title
            "/home/jetson/temp_images",     # folder path
            "Images (*.png *.jpg)"          # selection type
        )
        if str_path == '' or str_path is None or len(str_path)==0:
            return      # if closed without selection

        # process the image 
        img_path = Path(str_path)
        print("Selected photo: " + str(img_path))
        # Step 1. load camera model
        if self.camera_model is None or self.rectifier is None:
            self._load_camera_model(cam_path=cam_path)
        # Step 2. rectify image
        sbs_img = cv2.imread(str(img_path)) 
        leftImg, rightImg = self.rectifier.rectify_image(sbs_img=sbs_img)
        # Step 3. write required files into folder
        project_name = img_path.stem[4:]                # image filename without suffix, without prefix (sbs_)
        folder_path = Path(export_path) / project_name
        folder_path.mkdir(parents=True, exist_ok=True)
        copy(str(img_path), str(folder_path))       # copy sbs image
        copy(str(cam_path), str(folder_path))       # copy cam model
        cv2.imwrite(str(folder_path / "left.jpg"), leftImg)     # write rect left
        cv2.imwrite(str(folder_path / "right.jpg"), rightImg)   # write rect right
        # Step 4. scp and upload
        if scp(str(folder_path)):
            print("Successfully copied project folder to remote.")
            if upload(project_name, "left.jpg", "right.jpg", "camera_model.json"):
                print("Successfully post project info to database.")
                self.success_notice.show()
                return
        # else show failed
        self.fail_notice.show()


    def _load_camera_model(self, cam_path=None):
        """Load the camera model. Default from example folder"""
        if cam_path is None:
            print("Loading default camera model...")
            cam_path = Path(".") / "example" / "camera_model.json"
        else:
            print("Loading selected camera model...")
        self.camera_model = CameraModel.load_model(cam_path)
        self.rectifier = StereoRectify(self.camera_model, None)


    def closeEvent(self, event):
        """overriding default close event for qt window"""
        print("Exiting take photo window...")
        exit(0)
