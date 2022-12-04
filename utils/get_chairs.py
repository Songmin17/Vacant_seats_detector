import numpy as np
import matplotlib.pyplot as plt
import cv2

from visualization import *


def get_corners_3d(table_cluster):
    x_max, _, z_max = np.max(table_cluster, axis=0)
    idx_x_max, _, idx_z_max = np.argmax(table_cluster, axis=0)
    x_min, _, z_min = np.min(table_cluster, axis=0)
    idx_x_min, _, idx_z_min = np.argmin(table_cluster, axis=0)
    
    # four corners: (x_min, y_x_min), (x_max, y_x_max), (x_y_max, y_max), (x_y_min, y_min)
    return np.array([
        np.array([x_min, table_cluster[idx_x_min][1], table_cluster[idx_x_min][2]]), 
        np.array([x_max, table_cluster[idx_x_max][1], table_cluster[idx_x_max][2]]), 
        np.array([table_cluster[idx_z_min][0], table_cluster[idx_z_min][1], z_min]), 
        np.array([table_cluster[idx_z_max][0], table_cluster[idx_z_max][1], z_max])
    ])


def reprojection(points_3d, K, pose):
    pose = np.linalg.inv(pose)
    pose = pose[:3, :]
    
    points_3d_h = np.insert(points_3d, points_3d.shape[1], 1, axis=1)
    reprojection = K @ pose @ points_3d_h.T
    points_2d = np.divide(reprojection, reprojection[-1])[:2]

    return points_2d.T


if __name__ == "__main__":
    K = np.array([
        [975.813843, 0, 960.973816],
        [0, 975.475220, 729.893921],
        [0, 0, 1]
    ])

    plane_coeffs = np.array([0.04389121, -0.49583658, -0.25795586, 0.82805701])

    ### fetch camera poses
    num_cams = 4
    cam_poses = {} # key: cami, value: pose
    for i in range(num_cams):
        with open(f'./camera_poses/{i:05d}.txt', 'r') as f:
            lines = f.readlines()
            pose = []
            for line in lines:
                data = list(map(float, line.split(" ")))
                pose.append(data)
            pose = np.array(pose)
            cam_poses[f'cam{i}'] = pose.reshape(4, 4)

    # get clustered points
    points = get_table_points(K, cam_poses, plane_coeffs)
    points = remove_outliers(points)
    points = points[::20] # sample points for less computations
    bbox_max, bbox_min = get_bbox(points)
    clustered_points = cluster_tables(points=points, num_tables=6, min_tables=4, max_tables=10)
    clustered_points[1] = np.delete(clustered_points[1], list(range(3850, 3900)), axis=0)


    # get corner points for each table in 3D
    for i in range(4):
        img = cv2.imread(f'./data/layout/cam{i}/00000.jpg')
        for idx, table_cluster in enumerate(clustered_points):
            corners_3d = get_corners_3d(table_cluster=table_cluster)
            corners_2d = reprojection(corners_3d, K, cam_poses[f'cam{i}'])
            for corner in corners_2d:
                cv2.circle(img, list(map(int, corner)), 10, (255, 0, 0), -1)
        cv2.imwrite(f'./runs/get_chairs/corners_cam{i}.jpg', img)
 