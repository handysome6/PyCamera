# Must import cv2 before qt to avoid potential errors 
import cv2
import sys
from PySide2 import QtWidgets
from gui_measure import GuiMeasure
from take_photo import TakePhotoWindow
from pathlib import Path

# cam_path = Path("example") / "camera_model.json"
# img_path = Path("test.jpg")

app = QtWidgets.QApplication([])
window = TakePhotoWindow()
window.show()

sys.exit(app.exec_())