from gui_measure import GuiMeasure
from PySide2.QtWidgets import QApplication
import sys


cam_path = "/home/dell/Documents/camera_model.json"
img_path = "/home/dell/Documents/test.jpg"


app = QApplication([])

w = GuiMeasure(img_path, cam_path)
w.show()

sys.exit(app.exec_())