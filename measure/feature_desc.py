import cv2
import numpy as np
from measure.matcher import MATCHER_TYPE

class FeatureDesc():
    def __init__(self, method=MATCHER_TYPE.SIFT):

        if method == MATCHER_TYPE.SIFT:
            self.point_discriptor = cv2.SIFT_create()
        elif method == MATCHER_TYPE.BRIEF:
            self.point_discriptor = cv2.xfeatures2d.BriefDescriptorExtractor_create(bytes=64)
        elif method == MATCHER_TYPE.LUCID:
            self.point_discriptor = cv2.xfeatures2d.LUCID_create()
        elif method == MATCHER_TYPE.LATCH:
            self.point_discriptor = cv2.xfeatures2d.LATCH_create(bytes=32, rotationInvariance=False)
        elif method == MATCHER_TYPE.DAISY:
            self.point_discriptor = cv2.xfeatures2d.DAISY_create(radius=30, use_orientation = False)
        elif method == MATCHER_TYPE.BOOST:
            self.point_discriptor = cv2.xfeatures2d.BoostDesc_create(use_scale_orientation=False, scale_factor=40.)
        elif method == MATCHER_TYPE.VGG:
            self.point_discriptor = cv2.xfeatures2d.VGG_create(use_scale_orientation=False, scale_factor=25.)
        elif method == MATCHER_TYPE.BRISK:
            self.point_discriptor = cv2.BRISK_create()
        elif method == MATCHER_TYPE.FREAK:
            self.point_discriptor = cv2.xfeatures2d.FREAK_create(orientationNormalized=False)

    def compute(self, rect_img, point_list : np.ndarray):
        """
        compute descriptor of the point list w.r.t. given image
            
        Parameters
        ----------
        rect_img: np.ndarray
            given grayscale image
        point_list: np.ndarray
            given candidates point
            
        Returns
        -------
        None
        """
        self.img = rect_img
        self.kp = cv2.KeyPoint_convert(point_list)

        _, descriptors = self.point_discriptor.compute(self.img, self.kp)
        self.descriptors : np.ndarray = np.array(descriptors)

        # split the composite list into two parts
        # point1, and point2
        half_len = int(self.descriptors.shape[0] / 2)
        self.point_list1 : np.ndarray = point_list[:half_len]
        self.point_list2 : np.ndarray = point_list[half_len:]
        self.desc_list1 : np.ndarray = self.descriptors[:half_len]
        self.desc_list2 : np.ndarray = self.descriptors[half_len:]

    def find_point1_match(self, target_desc):
        assert target_desc.shape[0] == self.desc_list1[0].shape[0]
        return self.find_match(target_desc, self.desc_list1, self.point_list1)

    def find_point2_match(self, target_desc):
        assert target_desc.shape[0] == self.desc_list2[0].shape[0]
        return self.find_match(target_desc, self.desc_list2, self.point_list2)


    def find_match(self, target_desc, desc_list, point_list):
        """
        Find matched point in the given point list, using desc list

        Parameters
        ----------
        target_desc: np.ndarray
            given pt's descriptor, e.g. SIFT 128 dims
        desc_list: np.ndarray
            given candidates descriptor list, feature dim show be same with target_desc
            number of descriptors should be the same wtih points
        point_list: np.ndarray
            given candidates point list 
            number of points should be the same wtih desclist

        Returns
        -------
        nearest_point: np.ndarray
            matched most similar point's coordinate, (y, x)
        """
        distances = []
        for desc in desc_list:
            dist = cv2.norm(target_desc, desc, normType=cv2.NORM_L2)
            distances.append(dist)
        distances = np.array(distances)
        top_ind = np.argpartition(distances, 10)[:10]
        top_points = point_list[top_ind]
        # top_descriptors = desc_list[top_ind]
        top_distances = distances[top_ind]

        return top_points[np.argmin(top_distances)]

    @classmethod
    def get_candidate_pts(cls, point, min_disp=50, max_disp=600, height=3):
        """
        Input points, get candidates keypoints region in right image
        point: left image corner coord.
               accepted shape: (2,) (1,2)
        """
        # remove empty axis 
        point = np.squeeze(point)
        
        coord_x, coord_y = point.astype(int)
        half = height // 2
        pts = []

        # iterate through the region
        for i in range(coord_y-half, coord_y+half+1):
            for j in range(max(coord_x-max_disp, 0), coord_x-min_disp+1):
                pts.append(np.array([j, i]) )
        pts = np.array(pts, dtype=np.float32)
        # keypoints = cv2.KeyPoint.convert(pts)
        # print("Got coorespond region for ", point)

        return pts



"""
cv2.KeyPoint.convert:
    requiring the input pts in np.array
        shape = (x, 2)
        dtype = float(32)
"""