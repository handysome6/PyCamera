import enum
import cv2
import numpy as np
from enum import Enum
from pathlib import Path
from utils.utils import imshow


class MATCHER_TYPE(Enum):
    """
    Descriptor Extractor Types
    Ranking: VGG 
    > FREAK / BRIEF 
    > DAISY 
    > SIFT / LATCH / BOOST 
    >> SURF > LUCID
    """
    SIFT = 1
    # SURF = 10
    BRIEF = 2
    LUCID = 3
    LATCH = 4
    DAISY = 5
    BOOST = 6
    VGG = 7
    BRISK = 8
    FREAK = 9


class AutoMatcher():
    def __init__(self, left_img, right_img, method = MATCHER_TYPE.VGG) -> None:
        """
        Using SIFT features to match
        left_img
        """
        self.left_img = left_img
        self.right_img = right_img
        self.block_y = 3
        self.max_disp = 600
        self.min_disp = 50
        self.method = method
        
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


    def match(self, point, show_result=False):
        """
        Find matching point in another image
        point: single reference point coord in left image. 
               accepted shape: (2,) (1,2)
        """
        print("Finding matching point...")
        # convert point to list, as required by cv2 functions
        if len(point.shape) == 1:
            point = np.expand_dims(point, axis=0)
            assert len(point.shape) == 2
        # compute reference LEFT
        print("start1")
        testp = [(point[0][0]-int(point[0][0]) + 8,point[0][1]-int(point[0][1]) + 8)]
        testp = cv2.KeyPoint.convert(np.array(testp, dtype=np.float32))
        print("start2")
        # ref_keypoints = cv2.KeyPoint.convert(np.array(point, dtype=np.float32))
        corpimgL = self.left_img[int(point[0][1])-8:int(point[0][1])+8,int(point[0][0])-8:int(point[0][0])+8]
        print("start3")
        ref_keypoints, ref_descriptors = self.point_discriptor.compute(corpimgL, testp)
        # point = np.array(point, dtype=np.int32)
        # compute candidates RIGHT
        # candidates = self._get_correspond_candidates(point[0])
        corpimgR = self.right_img[int(point[0][1]) - 8:int(point[0][1]) + 8, int(point[0][0]) - 608:int(point[0][0]) - 42]
        testr = (608,8)
        candidates = self._get_correspond_candidates(testr)
        print("start4")
        corr_keypoints, corr_descriptors = self.point_discriptor.compute(corpimgR, candidates)
        # select point feature
        feature = ref_descriptors[0]
        # compare with corr features
        distances = []
        # print(len(feature))
        for corr_f in corr_descriptors:
            distances.append(cv2.norm(feature, corr_f, cv2.NORM_L2))

        # find nearest feature
        distances = np.array(distances)
        ind = np.argpartition(distances, 1)[:1]
        top_keypoints = []
        for i in ind:
            dist = distances[i]
            # print(dist, corr_keypoints[i].pt)
            kp = corr_keypoints[i]
            kp.size = self.kp_size(dist)
            # print(kp.size)
            top_keypoints.append(kp)
        top_keypoints = np.array(top_keypoints)
        # map keypoint to original image
        print("start5")
        matchpoint = cv2.KeyPoint.convert(top_keypoints)
        print(matchpoint)
        for i in range(len(matchpoint)):
            matchpoint[i][1] = matchpoint[i][1] + point[0][1] - 8
            matchpoint[i][0] = matchpoint[i][0] + point[0][0] - 608
        top_keypoints = cv2.KeyPoint.convert(matchpoint)
        if show_result:
            # Search region - Green
            show_fig = cv2.drawKeypoints(self.right_img, corr_keypoints, None, color = (0, 255, 0))
            # Top keypoionts - Red
            show_fig = cv2.drawKeypoints(show_fig, top_keypoints, None, color = (0, 0, 255), 
                flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
            imshow("Matching result", show_fig)
        return corr_keypoints, top_keypoints


    def kp_size(self, dist):
        if self.method == MATCHER_TYPE.SIFT:
            return 140000 / (dist+0.01)
        elif self.method == MATCHER_TYPE.BRIEF:
            return 280000 / (dist+0.01)
        elif self.method == MATCHER_TYPE.DAISY:
            return 70 / (dist+0.01)
        elif self.method == MATCHER_TYPE.VGG:
            return 1400 / (dist+0.01)
        elif self.method == MATCHER_TYPE.FREAK:
            return 280000 / (dist+0.01)
        
        return 140000 / (dist+0.01)


    def _get_correspond_candidates(self, point):
        """
        Input points, get candidates keypoints region in right image
        point: left image corner coord.
               accepted shape: (2,) (1,2)
        """
        # remove empty axis 
        point = np.squeeze(point)
        
        coord_x, coord_y = point
        half = self.block_y // 2
        pts = []
        # iterate through the region
        for i in range(coord_y-half, coord_y+half+1):
            for j in range(max(coord_x-self.max_disp, 0), coord_x-self.min_disp+1):
                pts.append(np.array([j, i]) )
        pts = np.array(pts, dtype=np.float32)
        keypoints = cv2.KeyPoint.convert(pts)
        # print("Got coorespond region for ", point)
        return keypoints

