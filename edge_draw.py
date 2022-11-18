import cv2
import numpy as np
from pprint import pprint
from tqdm import tqdm

def printEDParams(edp):
    print("AnchorThresholdValue", edp.AnchorThresholdValue)
    print("EdgeDetectionOarctanweenTwoLines", edp.MaxDistanceBetweenTwoLines)
    print("MaxErrorThreshold", edp.MaxErrorThreshold)
    print("MinLineLength", edp.MinLineLength)

def arrayIsEqual(arr1, arr2):
    if arr1.shape != arr2.shape:
        raise Exception("input shape incorrect")
    shape = arr1.shape
    total_num = 1
    for i in shape:
        total_num *= i
    if np.sum(arr1 == arr2) == total_num:
        return True
    else:
        return False

def findNearLines(lines, point):
    nearLines = []
    point = np.array(point, dtype="float32")
    for line in lines:
        endpoint1 = np.array(line[0][:2])
        endpoint2 = np.array(line[0][2:])
        if  cv2.norm(endpoint1, point, normType=cv2.NORM_L2) < 100 or \
            cv2.norm(endpoint2, point, normType=cv2.NORM_L2) < 100:
            nearLines.append( line )
    # print(len(nearLines))
    return np.array(nearLines)

def lineAngle(line):
    line = line[0]
    if (line[1]-line[3]) == 0:
        return np.pi / 2
    angle = np.arctan((line[0]-line[2]) / (line[1]-line[3]))
    return angle

def findCrossLines(lines, line):
    angle = lineAngle(line)
    crossLines = []
    for l_i in lines:
        if not arrayIsEqual(l_i, line):
            angle_i = lineAngle(l_i)
            if np.abs(angle-angle_i) > np.pi / 6:
                crossLines.append(l_i)
    return crossLines

def findNearestEnd(lines, endpoint):
    distance1 = []
    distance2 = []
    for line in lines:
        endpoint1 = np.array(line[0][:2])
        endpoint2 = np.array(line[0][2:])
        distance1.append(cv2.norm(endpoint-endpoint1))
        distance2.append(cv2.norm(endpoint-endpoint2))
    if np.min(distance1) < np.min(distance2):
        idx = np.argmin(distance1)
        return lines[idx], np.array(lines[idx][0][:2])
    else:
        idx = np.argmin(distance2)
        return lines[idx], np.array(lines[idx][0][2:])


def findCorners(lines):
    line_pairs = []
    corners = []
    for line in lines:
        l_1 = line
        s_1 = np.array(l_1[0][:2])
        # (1)
        Sc = findCrossLines(lines , l_1)
        # (2)
        l_2, s_2 = findNearestEnd(Sc, s_1)
        # (3)
        _Sc = findCrossLines(lines, l_2)    #1
        _l, _s = findNearestEnd(_Sc, s_2)   #2
        # print(s_1, s_2)
        # print(l_1, l_2, _l)
        if arrayIsEqual(l_1, _l):
            line_pairs.append( (l_1, l_2) )


        e_1 = np.array(l_1[0][2:])
        # (2)
        l_2, e_2 = findNearestEnd(Sc, e_1)
        # (3)
        _Sc = findCrossLines(lines, l_2)
        _l, _s = findNearestEnd(_Sc, e_2)
        # print(e_1, e_2)
        # print(l_1, l_2, _l)
        if arrayIsEqual(l_1, _l):
            line_pairs.append( (l_1, l_2) )

    for l1, l2 in line_pairs:
        a = l1[0][0]
        b = l1[0][1]
        c = l1[0][2]
        d = l1[0][3]
        e = l2[0][0]
        f = l2[0][1]
        g = l2[0][2]
        h = l2[0][3]
        A = np.array([
            [b-d, -(a-c)],
            [f-h, -(e-g)]
        ])
        B = np.array([
            (b-d)*a - (a-c)*b,
            (f-h)*e - (e-g)*f
        ])
        ans = np.linalg.solve(A, B)
        corners.append(ans)
        # print(ans)
    corners = np.array(corners, dtype=np.float64)
    print("num lines", lines.shape)
    print("line pairs:", len(line_pairs), "corner found:", corners.shape[0])

    return corners



if __name__ == "__main__":
    # img  = cv2.imread("right.jpg", cv2.IMREAD_GRAYSCALE)
    img = cv2.imread("right.jpg")
    img = cv2.cvtColor( img, cv2.COLOR_BGR2GRAY)

    # init edge drawing
    ed = cv2.ximgproc.createEdgeDrawing()
    EDParams = cv2.ximgproc_EdgeDrawing_Params()
    EDParams.EdgeDetectionOperator = 2
    EDParams.AnchorThresholdValue = 8
    # EDParams.MinPathLength = 100     # try changing this value between 5 to 1000
    EDParams.PFmode = True         # defaut value try to swich it to True
    EDParams.MinLineLength = 13     # try changing this value between 5 to 100
    # EDParams.NFAValidation = False   # defaut value try to swich it to False
    # EDParams.Sigma = 0.8

    # printEDParams(EDParams)
    ed.setParams(EDParams)

    # detect lines
    ed.detectEdges(img)
    all_lines = ed.detectLines(img)

    corner = [2712, 689]
    corner = [2522, 690]
    # corner = [2841, 931]
    lines = findNearLines(all_lines, corner)
    # draw lines 
    fld = cv2.ximgproc.createFastLineDetector()
    img = fld.drawSegments(img, all_lines)

    corners = findCorners(lines)
    # draw corners
    r = 2
    for corner in corners:
        print(corner)
        img = cv2.circle(img, np.array(corner, dtype=np.int32), r, (255,0,0), thickness=-1, lineType=cv2.LINE_AA)

    # show lines
    # cv2.namedWindow("test", cv2.WINDOW_NORMAL)
    # cv2.setWindowProperty("test", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN);
    # cv2.imshow("test", img)
    # cv2.waitKey(0)
    import sys
    from PySide2 import QtCore, QtWidgets
    # from my_graphicsview import MyGraphicsView
    from resize_graphicsview import ResizeGraphicsView

    app = QtWidgets.QApplication([])
    view = ResizeGraphicsView()
    view.load_scene_image(img)
    view.showMaximized()
    view.previewMode()

    sys.exit(app.exec_())


