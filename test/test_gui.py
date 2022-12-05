from gui_measure import GuiMeasure
from PySide2.QtWidgets import QApplication
import sys


cam_path = "/home/jetson/Documents/camera_model.json"
img_path = "/home/jetson/Documents/test.jpg"
cam_path = "/home/dell/Documents/camera_model.json"
img_path = "/home/dell/Documents/test.jpg"


if __name__ == "__main__":
    app = QApplication([])

    w = GuiMeasure(img_path, cam_path)
    w.show()

    sys.exit(app.exec_())