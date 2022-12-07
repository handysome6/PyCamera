from gui_measure import AutoMatchWorker

import cv2
import sys
import numpy as np
from PySide2.QtWidgets import QApplication, QWidget

class TestWidget(QWidget):
    def __init__(self):
        super().__init__()
        left = cv2.imread("left.jpg", cv2.IMREAD_GRAYSCALE)
        right  = cv2.imread("right.jpg", cv2.IMREAD_GRAYSCALE)
        point1 = np.array([1532, 1256])
        point2 = np.array([2173, 1164])
        self.am = AutoMatchWorker(left, right, point1, point2)
        self.am.start_compute()


if __name__ == "__main__":
    app = QApplication([])

    w = TestWidget()
    w.show()

    sys.exit(app.exec_())