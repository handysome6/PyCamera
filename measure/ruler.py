import cv2
import numpy as np
import time

class Ruler():
    def __init__(self, Q, left_img, right_img) -> None:
        """Measure segment length using stereo images.
        """
        self.Q = Q
        self.point1 = None
        self.point2 = None

        self.left_img = left_img
        self.right_img = right_img

    def update_point1(self, left, right):
        self.point1 = np.array([left, right], dtype=np.int32)

    def update_point2(self, left, right):
        self.point2 = np.array([left, right], dtype=np.int32)

    def measure_segment(self):
        """Measure a segment length by clicking points"""
        Q = self.Q

        # click to get segment
        point1, point2 = self.point1, self.point2
        # print(point1, point2)
        # print('world')
        world_coord1 = Ruler.get_world_coord_Q(Q, point1[0], point1[1])
        world_coord2 = Ruler.get_world_coord_Q(Q, point2[0], point2[1])
        # dx, dy, dz = world_coord2[0] - world_coord1[0], world_coord2[1] - world_coord1[1], world_coord2[2] - world_coord1[2]
        # print(world_coord1, world_coord2)
        # print(f"dx: {dx:.2f}mm, dy: {dy:.2f}mm, dz: {dz:.2f}mm,")
        self.segment_len = cv2.norm(world_coord1, world_coord2)
        return self.segment_len



    def get_result(self):
        timestart = time.time()
        point1, point2 = self.point1, self.point2
        world_coord1 = Ruler.get_world_coord_Q(self.Q, point1[0], point1[1])
        world_coord2 = Ruler.get_world_coord_Q(self.Q, point2[0], point2[1])
        point1L = point1[0].astype(np.int32)
        point1R = point1[1].astype(np.int32)
        point2L = point2[0].astype(np.int32)
        point2R = point2[1].astype(np.int32)
        height, width = self.left_img.shape[:2]
        line_thickness = 8
        # show_img = self.left_img.copy()
        show_img = self.left_img
        # show end_points
        point1_left = Ruler.draw_line_crop(self.left_img, point1L)
        point1_right = Ruler.draw_line_crop(self.right_img, point1R)
        point2_left = Ruler.draw_line_crop(self.left_img, point2L)
        point2_right = Ruler.draw_line_crop(self.right_img, point2R)
        # show segment length
        cv2.line(show_img, point1L, point2L, (0, 255, 0), thickness=line_thickness)
        dx, dy, dz = world_coord2[0] - world_coord1[0], world_coord2[1] - world_coord1[1], world_coord2[2] - \
                     world_coord1[2]
        if point1R[0] > 0 and point2R[0] > 0:
            cv2.putText(show_img, f"Length of segment: {self.segment_len:.1f}mm",
                (20,150), cv2.FONT_HERSHEY_SIMPLEX, 5, (0,255,0), 12)
            # show different x, y z
            #cv2.putText(show_img, f"dx: {dx:.2f}mm, dy: {dy:.2f}mm, dz: {dz:.2f}mm,",
             #           (20, 300),  cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 8)
        else:
            cv2.putText(show_img, "Can't measure line segment, please choose again",
                        (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 12)
        # show point coordinates
        x1, y1, z1 = world_coord1[0].astype(np.float32), world_coord1[1].astype(np.float32), world_coord1[2].astype(
            np.float32)
        x2, y2, z2 = world_coord2[0].astype(np.float32), world_coord2[1].astype(np.float32), world_coord2[2].astype(
            np.float32)
        if point1R[0] > 0:
            cv2.putText(show_img, f"point1: ({x1:.1f}, {y1:.1f}, {z1:.1f})", (20, 300),  cv2.FONT_HERSHEY_SIMPLEX, 5,
                        (0, 255, 0), 10)
        else:
            cv2.putText(show_img, "point1: too close to boundary", (20, 300), cv2.FONT_HERSHEY_SIMPLEX, 5,
                        (0, 0, 255), 10)
        if point2R[0] > 0:
            cv2.putText(show_img, f"point2: ({x2:.1f}, {y2:.1f}, {z2:.1f})", (20, 450), cv2.FONT_HERSHEY_SIMPLEX, 5,
                        (0, 255, 0), 10)
        else:
            cv2.putText(show_img, "point1: too close to boundary", (20, 450), cv2.FONT_HERSHEY_SIMPLEX, 5,
                        (0, 0, 255), 10)
        cv2.putText(show_img, '1', (point1L[0], point1L[1] + 80), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 12)
        cv2.putText(show_img, '2', (point2L[0], point2L[1] + 80), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 12)
        
        showsize = self.left_img.shape[0]
        p1 = cv2.resize(np.vstack([point1_left, point1_right]), (int(showsize/2), int(showsize)))
        p2 = cv2.resize(np.vstack([point2_left, point2_right]), [int(showsize/2), int(showsize)])
        result = np.concatenate([p1, show_img, p2], axis=1)
        return result



    def show_endpoints(self):
        """Show selected endpoints"""
        point1, point2 = self.point1, self.point2

        point1_left = Ruler.draw_line_crop(self.left_img, point1[0])
        point1_right = Ruler.draw_line_crop(self.right_img, point1[1])
        point2_left = Ruler.draw_line_crop(self.left_img, point2[0])
        point2_right = Ruler.draw_line_crop(self.right_img, point2[1])
        p1 = np.hstack([point1_left, point1_right])
        p2 = np.hstack([point2_left, point2_right])
        result = np.vstack([p1, p2])

        return result



    @staticmethod
    def draw_line_crop(img, point):
        """Draw a corss around the corner"""
        # d = 100
        # line_thickness = 1
        # point = (int(point[0]), int(point[1]))
        # cv2.line(img, point, (point[0], 0), (0,0,255), thickness=line_thickness)
        # cv2.line(img, point, (0, point[1]), (0,0,255), thickness=line_thickness)
        # return \
        #     img[point[1]-d:point[1]+d,
        #         point[0]-d:point[0]+d,]

        point = np.array(point, dtype=np.int)
        print(point)
        line_thickness = 1
        d = 100
        color = (0,0,0)
        cropimg = np.zeros([2*d,2*d,3],dtype=np.uint8)
        print(img.dtype)
        print(cropimg.shape)
        if point[0] > 0 and point[1] > 0:
            cropimg[int(max(d-point[1], 0)):, int(max(d-point[0], 0)):,:] = \
            img[int(max(point[1]-d, 0)):point[1]+d,\
            int(max(point[0]-d, 0)):point[0]+d,:]
            cv2.line(cropimg, (d,d), (d, 0), (0, 0, 255), thickness=line_thickness)
            cv2.line(cropimg, (d,d), (0, d), (0, 0, 255), thickness=line_thickness)
            return cropimg
        else:
            cv2.putText(cropimg, "no matching", (0, 80), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                    (0, 0, 255), 1)
            cv2.putText(cropimg, "point", (0, 120), cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 0, 255), 1)
            return cropimg


    @staticmethod
    def get_world_coord_Q(Q, img_coord_left, img_coord_right):
        """Compute world coordniate by the Q matrix
        
        img_coord_left:  segment endpoint coordinate on the  left image
        img_coord_right: segment endpoint coordinate on the right image
        """
        x, y = img_coord_left
        d = img_coord_left[0] - img_coord_right[0]
        # print(x, y, d); exit(0)
        homg_coord = Q.dot(np.array([x, y, d, 1.0]))
        coord = homg_coord / homg_coord[3]
        # print(coord[:-1])
        return coord[:-1]

