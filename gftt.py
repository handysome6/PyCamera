import cv2
import numpy as np
import datetime

def gftt(src : np.ndarray, point):
    point = np.array(point, dtype=np.int)
    d = 100
    crop = np.zeros([200, 200], dtype=np.float32)

    if point[0] < d and point[1] >= d:
        crop[:, d-point[0]:] = \
            src[point[1]-d  : point[1]+d,
                0           : point[0]+d]
    elif point[1] < d and point[0] >=d:
        crop[d-point[1]:, :] = \
            src[0       : point[1]+d,
              point[0]-d: point[0]+d]
    elif point[0] < d and point[1] < d:
        crop[d-point[1]:, d-point[0]:] = \
            src[0   : point[1]+d,
                0   : point[0]+d]
    else:
        crop = src[point[1]-d: point[1]+d,
                point[0]-d: point[0]+d]
    maxCorners = 50
    qualityLevel = 0.01
    minDistance = 5.
    blockSize = 5

    corners = cv2.goodFeaturesToTrack(
        crop, maxCorners, qualityLevel, minDistance, 
        blockSize=blockSize
    )

    corners = np.squeeze(corners)
    # remap to src coord
    corners += point-d

    return corners


if __name__ == "__main__":
    import sys
    from PySide2 import QtCore, QtWidgets
    from resize_graphicsview import ResizeGraphicsView

    point = [2522, 689]
    point = [2514, 563]
    point = [2401, 932]
    point = [1746, 963]
    point = [10, 1000]
    img = cv2.imread("right.jpg", cv2.IMREAD_GRAYSCALE)

    corners = gftt(img, point)
    r = 3
    for corner in corners:
        corner = np.array(corner, dtype=np.int)
        cv2.circle(img, corner, r, (255, 0 ,0), thickness=-1)


    app = QtWidgets.QApplication([])
    view = ResizeGraphicsView()
    view.load_scene_image(img)
    view.showMaximized()

    sys.exit(app.exec_())