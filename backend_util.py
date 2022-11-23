# This is intended for backend development.
import numpy as np
import cv2

from measure.matcher import AutoMatcher, MATCHER_TYPE
from measure.ruler import Ruler
from calib.rectification import StereoRectify
from model.camera_model import CameraModel

def python_match_points(input_image_left, input_image_right, input_point1, input_point2):
    """
    This function match two points with given rectified images.

    Parameters
    ----------
    input_image_left : np.ndarray
        Rectified left image.
    input_image_right : np.ndarray
        Rectified right image.
    input_point1 : np.ndarray
        The first point to be matched.
    input_point2 : np.ndarray
        The seond point to be matched.

    Returns
    -------
    matched_point1 : np.ndarray
        Match result for point 1. Shape: (2,)
    matched_point1 : np.ndarray
        Match result for point 2. Shape: (2,)
    """
    # Matcher construction
    matcher = AutoMatcher(input_image_left, input_image_right, method=MATCHER_TYPE.SIFT)

    # Match point 1
    _, top_kps = matcher.match(input_point1, show_result=False)
    size_list=np.array([kp.size for kp in top_kps])
    index=np.argmax(size_list)
    matched_point1 = top_kps[index].pt

    # Match point 2
    _, top_kps = matcher.match(input_point2, show_result=False)
    size_list=np.array([kp.size for kp in top_kps])
    index=np.argmax(size_list)
    matched_point2 = top_kps[index].pt

    return np.array(matched_point1), np.array(matched_point2)


def python_compute_length(camera_model_path, left_point1, left_point2, right_point1, right_point2):
    """
    Compute length given camera model image coords.

    Parameters
    ----------
    camera_model_path : path to camera model
    left_point1 : np.ndarray / list
    left_point2 : np.ndarray / list
    right_point1 : np.ndarray / list
    right_point2 : np.ndarray / list

    Returns
    -------
    len: computed length in world coord
    """
    # rectify model, get Q
    camera_model = CameraModel.load_model(camera_model_path)
    rectifier = StereoRectify(camera_model, None)
    print(rectifier.is_rectified())
    if not rectifier.is_rectified():
        rectifier.rectify_camera()

    # compute world coord
    world_coord1 = Ruler.get_world_coord_Q(rectifier.Q, left_point1, right_point1)
    world_coord2 = Ruler.get_world_coord_Q(rectifier.Q, left_point2, right_point2)
    len = cv2.norm(world_coord1, world_coord2)
    return len

if __name__=="__main__":
    input_image_left = cv2.imread("./resources/left.jpg")
    input_image_right = cv2.imread("./resources/right.jpg")
    input_point1 = np.array([1700, 1083])
    input_point2 = np.array([2471, 1100])
    matched_point1, matched_point2 = python_match_points(input_image_left, input_image_right, input_point1, input_point2)
    print(matched_point1, matched_point2)

    cam_path = "./resources/camera_model.json"
    len = python_compute_length(cam_path, input_point1, input_point2, matched_point1, matched_point2)
    print(len,type(len))