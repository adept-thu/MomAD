import os
from os.path import join
import gzip, json, pickle
import numpy as np
from pyquaternion import Quaternion
from tqdm import tqdm
import copy
# from vis_utils import calculate_cube_vertices,calculate_occlusion_stats,edges,DIS_CAR_SAVE
import cv2
import multiprocessing
import argparse
from shapely.geometry import LineString
# All data in the Bench2Drive dataset are in the left-handed coordinate system.
# This code converts all coordinate systems (world coordinate system, vehicle coordinate system,
# camera coordinate system, and lidar coordinate system) to the right-handed coordinate system
# consistent with the nuscenes dataset.

DATAROOT = 'data/bench2drive'
MAP_ROOT = 'data/bench2drive/maps'
OUT_DIR = 'data/infos_sparsedrive'
# split_file = 'data/bench2drive/bench2drive_mini_train_val_split.json'
split_file = 'data/splits/bench2drive_base_train_val_split.json'

MAP_CLASSES = [
    'Broken',
    'Solid',
    'SolidSolid',
    'Center',
    'TrafficLight',
    'StopSign',
]
point_cloud_range = [-15.0, -30.0, -2.0, 15.0, 30.0, 2.0]

MAX_DISTANCE = 75              # Filter bounding boxes that are too far from the vehicle
FILTER_Z_SHRESHOLD = 10        # Filter bounding boxes that are too high/low from the vehicle
FILTER_INVISINLE = True        # Filter bounding boxes based on visibility
NUM_VISIBLE_SHRESHOLD = 1      # Filter bounding boxes with fewer visible vertices than this value
NUM_OUTPOINT_SHRESHOLD = 7     # Filter bounding boxes where the number of vertices outside the frame is greater than this value in all cameras
CAMERAS = ['CAM_FRONT', 'CAM_FRONT_RIGHT', 'CAM_FRONT_LEFT', 'CAM_BACK', 'CAM_BACK_LEFT', 'CAM_BACK_RIGHT']
CAMERA_TO_FOLDER_MAP = {'CAM_FRONT':'rgb_front', 'CAM_FRONT_LEFT':'rgb_front_left', 'CAM_FRONT_RIGHT':'rgb_front_right', 'CAM_BACK':'rgb_back', 'CAM_BACK_LEFT':'rgb_back_left', 'CAM_BACK_RIGHT':'rgb_back_right'}

stand_to_ue4_rotate = np.array([[ 0, 0, 1, 0],
                                [ 1, 0, 0, 0],
                                [ 0,-1, 0, 0],
                                [ 0, 0, 0, 1]])

lidar_to_righthand_ego = np.array([[  0, 1, 0, 0],
                                   [ -1, 0, 0, 0],
                                   [  0, 0, 1, 0],
                                   [  0, 0, 0, 1]])

lefthand_ego_to_lidar = np.array([[ 0, 1, 0, 0],
                                  [ 1, 0, 0, 0],
                                  [ 0, 0, 1, 0],
                                  [ 0, 0, 0, 1]])

left2right = np.eye(4)
left2right[1,1] = -1

WINDOW_HEIGHT = 900
WINDOW_WIDTH = 1600

def point_in_canvas_hw(pos):
    """Return true if point is in canvas"""
    if (pos[0] >= 0) and (pos[0] < WINDOW_HEIGHT) and (pos[1] >= 0) and (pos[1] < WINDOW_WIDTH):
        return True
    return False

def calculate_cube_vertices(center, extent):
    cx, cy, cz = center
    x, y, z = extent
    vertices = [
        (cx + x, cy + y, cz + z),
        (cx + x, cy + y, cz - z),
        (cx + x, cy - y, cz + z),
        (cx + x, cy - y, cz - z),
        (cx - x, cy + y, cz + z),
        (cx - x, cy + y, cz - z),
        (cx - x, cy - y, cz + z),
        (cx - x, cy - y, cz - z)
    ]
    return vertices

def calculate_occlusion_stats(bbox_points, depth, depth_map, max_render_depth):
    """ Draws each vertex in vertices_pos2d if it is in front of the camera
        The color is based on whether the object is occluded or not.
        Returns the number of visible vertices and the number of vertices outside the camera.
    """
    num_visible_vertices = 0
    num_invisible_vertices = 0
    num_vertices_outside_camera = 0
    points = []

    for i in range(len(bbox_points)):
        x_2d = bbox_points[i][0]
        y_2d = bbox_points[i][1]
        point_depth = depth[i]

        # if the point is in front of the camera but not too far away
        if max_render_depth > point_depth > 0 and point_in_canvas_hw((y_2d, x_2d)):
            #is_occluded_v = point_is_occluded_vectorized([[y_2d, x_2d]], point_depth, depth_map)
            is_occluded = point_is_occluded(
                (y_2d, x_2d), point_depth, depth_map)
                
            if is_occluded:
                vertex_color = (0,0,255) # bgr, red
                num_invisible_vertices += 1
            else:
                num_visible_vertices += 1
                vertex_color = (0,255,0) # bgr, green
            points.append((x_2d, y_2d, vertex_color))
        else:
            num_vertices_outside_camera += 1
    return num_visible_vertices, num_invisible_vertices, num_vertices_outside_camera, points

def point_is_occluded(point, vertex_depth, depth_map):
    """ Checks whether or not the four pixels directly around the given point has less depth than the given vertex depth
        If True, this means that the point is occluded.
    """
    y, x = map(int, point)
    from itertools import product
    neigbours = product((1, -1), repeat=2)
    is_occluded = []
    for dy, dx in neigbours:
        if point_in_canvas_hw((dy+y, dx+x)):
            # If the depth map says the pixel is closer to the camera than the actual vertex
            if depth_map[y+dy, x+dx] < vertex_depth:
                is_occluded.append(True)
            else:
                is_occluded.append(False)
    # Only say point is occluded if all four neighbours are closer to camera than vertex
    return all(is_occluded)

def apply_trans(vec,world2ego):
    vec = np.concatenate((vec,np.array([1])))
    t = world2ego @ vec
    return t[0:3]

def get_pose_matrix(dic):
    new_matrix = np.zeros((4,4))
    new_matrix[0:3,0:3] = Quaternion(axis=[0, 0, 1], radians=dic['theta']-np.pi/2).rotation_matrix
    new_matrix[0,3] = dic['x']
    new_matrix[1,3] = dic['y']
    new_matrix[3,3] = 1
    return new_matrix

def get_npc2world(npc):
    for key in ['world2vehicle','world2ego','world2sign','world2ped']:
        if key in npc.keys():
            npc2world = np.linalg.inv(np.array(npc[key]))
            yaw_from_matrix = np.arctan2(npc2world[1,0], npc2world[0,0])
            yaw = npc['rotation'][-1] / 180 * np.pi
            if abs(yaw-yaw_from_matrix)> 0.01:
                npc2world[0:3,0:3] = Quaternion(axis=[0, 0, 1], radians=yaw).rotation_matrix
            npc2world = left2right @ npc2world @ left2right
            return npc2world
    npc2world = np.eye(4)
    npc2world[0:3,0:3] = Quaternion(axis=[0, 0, 1], radians=npc['rotation'][-1]/180*np.pi).rotation_matrix
    npc2world[0:3,3] = np.array(npc['location'])
    return left2right @ npc2world @ left2right


def get_global_trigger_vertex(center,extent,yaw_in_degree):
    x,y = center[0],-center[1]
    dx,dy = extent[0],extent[1]
    yaw_in_radians = -yaw_in_degree/180*np.pi
    vertex_in_self = np.array([[ dx, dy],
                               [-dx, dy],
                               [-dx,-dy],
                               [ dx,-dy]])
    rotate_matrix = np.array([[np.cos(yaw_in_radians),-np.sin(yaw_in_radians)],
                              [np.sin(yaw_in_radians), np.cos(yaw_in_radians)]])
    rotated_vertex = (rotate_matrix @ vertex_in_self.T).T
    vertex_in_global = np.array([[x,y]]).repeat(4,axis=0) + rotated_vertex
    return vertex_in_global



def get_image_point(loc, K, w2c):
    point = np.array([loc[0], loc[1], loc[2], 1])
    point_camera = np.dot(w2c, point)
    point_camera = point_camera[0:3]
    depth = point_camera[2]
    point_img = np.dot(K, point_camera)
    point_img[0] /= point_img[2]
    point_img[1] /= point_img[2]
    return point_img[0:2], depth

def get_action(index):
	Discrete_Actions_DICT = {
		0:  (0, 0, 1, False),
		1:  (0.7, -0.5, 0, False),
		2:  (0.7, -0.3, 0, False),
		3:  (0.7, -0.2, 0, False),
		4:  (0.7, -0.1, 0, False),
		5:  (0.7, 0, 0, False),
		6:  (0.7, 0.1, 0, False),
		7:  (0.7, 0.2, 0, False),
		8:  (0.7, 0.3, 0, False),
		9:  (0.7, 0.5, 0, False),
		10: (0.3, -0.7, 0, False),
		11: (0.3, -0.5, 0, False),
		12: (0.3, -0.3, 0, False),
		13: (0.3, -0.2, 0, False),
		14: (0.3, -0.1, 0, False),
		15: (0.3, 0, 0, False),
		16: (0.3, 0.1, 0, False),
		17: (0.3, 0.2, 0, False),
		18: (0.3, 0.3, 0, False),
		19: (0.3, 0.5, 0, False),
		20: (0.3, 0.7, 0, False),
		21: (0, -1, 0, False),
		22: (0, -0.6, 0, False),
		23: (0, -0.3, 0, False),
		24: (0, -0.1, 0, False),
		25: (1, 0, 0, False),
		26: (0, 0.1, 0, False),
		27: (0, 0.3, 0, False),
		28: (0, 0.6, 0, False),
		29: (0, 1.0, 0, False),
		30: (0.5, -0.5, 0, True),
		31: (0.5, -0.3, 0, True),
		32: (0.5, -0.2, 0, True),
		33: (0.5, -0.1, 0, True),
		34: (0.5, 0, 0, True),
		35: (0.5, 0.1, 0, True),
		36: (0.5, 0.2, 0, True),
		37: (0.5, 0.3, 0, True),
		38: (0.5, 0.5, 0, True),
		}
	throttle, steer, brake, reverse = Discrete_Actions_DICT[index]
	return throttle, steer, brake


def gengrate_map(map_root):
    map_infos = {}
    for file_name in os.listdir(map_root):
        if '.npz' in file_name:
            map_info = dict(np.load(join(map_root,file_name), allow_pickle=True)['arr'])
            town_name = file_name.split('_')[0]
            map_infos[town_name] = {} 
            lane_points = []
            lane_types = []
            lane_sample_points = []
            trigger_volumes_points = []
            trigger_volumes_types = []
            trigger_volumes_sample_points = []
            for road_id, road in map_info.items():
                for lane_id, lane in road.items():
                    if lane_id == 'Trigger_Volumes':
                        for single_trigger_volume in lane:
                            points = np.array(single_trigger_volume['Points'])
                            points[:,1] *= -1 #left2right
                            trigger_volumes_points.append(points)
                            trigger_volumes_sample_points.append(points.mean(axis=0))
                            trigger_volumes_types.append(single_trigger_volume['Type'])
                    else:
                        for single_lane in lane:
                            points = np.array([raw_point[0] for raw_point in single_lane['Points']])
                            points[:,1] *= -1
                            lane_points.append(points)
                            lane_types.append(single_lane['Type'])
                            lane_lenth = points.shape[0]
                            if lane_lenth % 50 != 0:
                                devide_points = [50*i for i in range(lane_lenth//50+1)]
                            else:
                                devide_points = [50*i for i in range(lane_lenth//50)]
                            devide_points.append(lane_lenth-1)
                            lane_sample_points_tmp = points[devide_points]
                            lane_sample_points.append(lane_sample_points_tmp)
            map_infos[town_name]['lane_points'] = lane_points
            map_infos[town_name]['lane_sample_points'] = lane_sample_points
            map_infos[town_name]['lane_types'] = lane_types
            map_infos[town_name]['trigger_volumes_points'] = trigger_volumes_points
            map_infos[town_name]['trigger_volumes_sample_points'] = trigger_volumes_sample_points
            map_infos[town_name]['trigger_volumes_types'] = trigger_volumes_types
    with open(join(OUT_DIR,'b2d_map_infos.pkl'),'wb') as f:
        pickle.dump(map_infos,f)
    return map_infos

def preprocess(folder_list,idx,tmp_dir,train_or_val,map_infos):

    data_root = DATAROOT
    cameras = CAMERAS
    final_data = []
    if idx == 0:
        folders = tqdm(folder_list)
    else:
        folders = folder_list

    for folder_name in folders:
        print(folder_name)
        folder_path = join(data_root, folder_name)
        last_position_dict = {}
        for ann_name in sorted(os.listdir(join(folder_path,'anno')),key= lambda x: int(x.split('.')[0])):
            if idx == 0:
                print(ann_name)
            position_dict = {}
            frame_data = {}
            cam_gray_depth = {}
            with gzip.open(join(folder_path,'anno',ann_name), 'rt', encoding='utf-8') as gz_file:
                anno = json.load(gz_file) 
            frame_data['folder'] = folder_name
            frame_data['town_name'] =  folder_name.split('/')[1].split('_')[1]
            frame_data['command_far_xy'] = np.array([anno['x_command_far'],-anno['y_command_far']])
            frame_data['command_far'] = anno['command_far']
            frame_data['command_near_xy'] = np.array([anno['x_command_near'],-anno['y_command_near']])
            frame_data['command_near'] = anno['command_near']
            frame_data['frame_idx'] = int(ann_name.split('.')[0])
            frame_data['timestamp'] = int(ann_name.split('.')[0]) / 10 * 1e6 # consistent with nusc
            frame_data['token'] = folder_name + '_' + str(int(ann_name.split('.')[0])).zfill(4)
            frame_data['ego_yaw'] = -np.nan_to_num(anno['theta'],nan=np.pi)+np.pi/2  
            frame_data['ego_translation'] = np.array([anno['x'],-anno['y'],0])
            frame_data['ego_vel'] = np.array([anno['speed'],0,0])
            frame_data['ego_accel'] = np.array([anno['acceleration'][0],-anno['acceleration'][1],anno['acceleration'][2]])
            frame_data['ego_rotation_rate'] = -np.array(anno['angular_velocity'])
            frame_data['ego_size'] = np.array([anno['bounding_boxes'][0]['extent'][1],anno['bounding_boxes'][0]['extent'][0],anno['bounding_boxes'][0]['extent'][2]])*2
            world2ego = left2right @ anno['bounding_boxes'][0]['world2ego'] @ left2right
            frame_data['world2ego'] = world2ego
            if frame_data['frame_idx'] == 0:
                expert_file_path = join(folder_path,'expert_assessment','-0001.npz')
            else:
                expert_file_path = join(folder_path,'expert_assessment',str(frame_data['frame_idx']-1).zfill(5)+'.npz')
            expert_data = np.load(expert_file_path,allow_pickle=True)['arr_0']
            action_id = expert_data[-1]
            # value = expert_data[-2]
            # expert_feature = expert_data[:-2]
            throttle, steer, brake = get_action(action_id)
            frame_data['brake'] = brake
            frame_data['throttle'] = throttle
            frame_data['steer'] = steer
            #frame_data['action_id'] = action_id
            #frame_data['value'] = value
            #frame_data['expert_feature'] = expert_feature
            ###get sensor infos###
            sensor_infos = {}
            for cam in CAMERAS:
                sensor_infos[cam] = {}
                sensor_infos[cam]['cam2ego'] = left2right @ np.array(anno['sensors'][cam]['cam2ego']) @ stand_to_ue4_rotate 
                sensor_infos[cam]['intrinsic'] = np.array(anno['sensors'][cam]['intrinsic'])
                sensor_infos[cam]['world2cam'] = np.linalg.inv(stand_to_ue4_rotate) @ np.array(anno['sensors'][cam]['world2cam']) @left2right
                sensor_infos[cam]['data_path'] = join(folder_name,'camera',CAMERA_TO_FOLDER_MAP[cam],ann_name.split('.')[0]+'.jpg')
                cam_gray_depth[cam] = cv2.imread(join(data_root,sensor_infos[cam]['data_path']).replace('rgb_','depth_').replace('.jpg','.png'))[:,:,0]
            sensor_infos['LIDAR_TOP'] = {}
            sensor_infos['LIDAR_TOP']['lidar2ego'] = left2right @ np.array(anno['sensors']['LIDAR_TOP']['lidar2ego']) @ left2right @ lidar_to_righthand_ego
            world2lidar = lefthand_ego_to_lidar @ np.array(anno['sensors']['LIDAR_TOP']['world2lidar']) @ left2right
            sensor_infos['LIDAR_TOP']['world2lidar'] = world2lidar
            frame_data['sensors'] = sensor_infos
            map_annos = get_map_anno(frame_data, map_infos)
            frame_data["map_annos"] = map_annos
            ###get bounding_boxes infos###
            gt_boxes = []
            gt_names = []
            gt_ids = []
            num_points_list = []
            npc2world_list = []
            for npc in anno['bounding_boxes']:
                if npc['class'] == 'ego_vehicle': continue
                if npc['distance'] > MAX_DISTANCE: continue
                if abs(npc['location'][2] - anno['bounding_boxes'][0]['location'][2]) > FILTER_Z_SHRESHOLD: continue
                center = np.array([npc['center'][0],-npc['center'][1],npc['center'][2]]) # left hand -> right hand
                # extent = np.array([npc['extent'][1],npc['extent'][0],npc['extent'][2]])  # lwh -> wlh
                extent = np.array([npc['extent'][0],npc['extent'][1],npc['extent'][2]])  # lwh
                position_dict[npc['id']] = center
                local_center = apply_trans(center, world2lidar)
                size = extent * 2 
                if 'world2vehicle' in npc.keys():
                    world2vehicle = left2right @ np.array(npc['world2vehicle'])@left2right
                    vehicle2lidar = world2lidar @ np.linalg.inv(world2vehicle) 
                    yaw_local = np.arctan2(vehicle2lidar[1,0], vehicle2lidar[0,0])

                else:
                    yaw_local = -npc['rotation'][-1]/180*np.pi - frame_data['ego_yaw'] +np.pi / 2  
                # yaw_local_in_lidar_box = -yaw_local - np.pi / 2  
                yaw_local_in_lidar_box = yaw_local  
                while yaw_local < -np.pi:
                    yaw_local += 2*np.pi
                while yaw_local > np.pi:
                    yaw_local -= 2*np.pi  
                if 'speed' in npc.keys():
                    if 'vehicle' in npc['class']:  # only vehicles have correct speed
                        speed = npc['speed']
                    else:
                        if npc['id'] in last_position_dict.keys():  #calculate speed for other object
                            speed = np.linalg.norm((center-last_position_dict[npc['id']])[0:2]) * 10
                        else:
                            speed = 0
                else:
                    speed = 0
                if 'num_points' in npc.keys():
                    num_points = npc['num_points']
                else:
                    num_points = -1
                npc2world = get_npc2world(npc)
                speed_x = speed * np.cos(yaw_local)
                speed_y = speed * np.sin(yaw_local)

                ###fliter_bounding_boxes###
                if FILTER_INVISINLE:
                    valid = False
                    box2lidar = np.eye(4)
                    box2lidar[0:3,0:3] = Quaternion(axis=[0, 0, 1], radians=yaw_local).rotation_matrix
                    box2lidar[0:3,3] = local_center
                    lidar2box = np.linalg.inv(box2lidar)
                    raw_verts = calculate_cube_vertices(local_center,extent)
                    verts = []
                    for raw_vert in raw_verts:
                        tmp = np.dot(lidar2box, [raw_vert[0], raw_vert[1], raw_vert[2],1])
                        tmp[0:3] += local_center
                        verts.append(tmp.tolist()[:-1])
                    for cam in cameras:
                        lidar2cam = np.linalg.inv(frame_data['sensors'][cam]['cam2ego']) @ sensor_infos['LIDAR_TOP']['lidar2ego']
                        test_points = [] 
                        test_depth = []
                        for vert in verts:
                            point, depth = get_image_point(vert, frame_data['sensors'][cam]['intrinsic'], lidar2cam)
                            if depth > 0:
                                test_points.append(point)
                                test_depth.append(depth)

                        num_visible_vertices, num_invisible_vertices, num_vertices_outside_camera, colored_points = calculate_occlusion_stats(np.array(test_points), np.array(test_depth),  cam_gray_depth[cam], max_render_depth=MAX_DISTANCE)
                        if num_visible_vertices>NUM_VISIBLE_SHRESHOLD and num_vertices_outside_camera<NUM_OUTPOINT_SHRESHOLD:
                            valid = True
                            break
                else:
                    valid = True
                if valid:
                    npc2world_list.append(npc2world)
                    num_points_list.append(num_points)            
                    gt_boxes.append(np.concatenate([local_center,size,np.array([yaw_local_in_lidar_box,speed_x,speed_y])]))
                    gt_names.append(npc['type_id'])
                    gt_ids.append(int(npc['id']))

            if len(gt_boxes) == 0:
                continue

            last_position_dict = position_dict.copy()    
            gt_ids = np.array(gt_ids)
            gt_names = np.array(gt_names)
            num_points_list = np.array(num_points_list)
            gt_boxes = np.stack(gt_boxes)
            npc2world = np.stack(npc2world_list)
            frame_data['gt_ids'] = gt_ids
            frame_data['gt_boxes'] = gt_boxes
            frame_data['gt_names'] = gt_names
            frame_data['num_points'] = num_points_list
            frame_data['npc2world'] = npc2world
            final_data.append(frame_data)
    
    os.makedirs(join(OUT_DIR,tmp_dir),exist_ok=True)
    with open(join(OUT_DIR,tmp_dir,'b2d_infos_'+train_or_val+'_'+str(idx)+'.pkl'),'wb') as f:
        pickle.dump(final_data,f)


def get_map_anno(ann_info, map_infos):
    town_name = ann_info['town_name']
    map_info = map_infos[town_name]
    lane_points = map_info['lane_points']
    lane_sample_points = map_info['lane_sample_points']
    lane_types = map_info['lane_types']
    trigger_volumes_points = map_info['trigger_volumes_points']
    trigger_volumes_sample_points = map_info['trigger_volumes_sample_points']
    trigger_volumes_types = map_info['trigger_volumes_types']
    world2lidar = np.array(ann_info['sensors']['LIDAR_TOP']['world2lidar'])
    ego_xy = np.linalg.inv(world2lidar)[0:2,3]
    max_distance = 50
    chosed_idx = []

    for idx in range(len(lane_sample_points)):
        single_sample_points = lane_sample_points[idx]
        distance = np.linalg.norm((single_sample_points[:,0:2]-ego_xy),axis=-1)
        if np.min(distance) < max_distance:
            chosed_idx.append(idx)

    map_anno = {}
    for i in range(len(MAP_CLASSES)):
        map_anno[i] = []

    for idx in chosed_idx:
        if not lane_types[idx] in MAP_CLASSES:
            continue
        points = lane_points[idx]
        points = np.concatenate([points,np.ones((points.shape[0],1))],axis=-1)
        points_in_lidar = (world2lidar @ points.T).T
        mask = (points_in_lidar[:,0]>point_cloud_range[0]) & (points_in_lidar[:,0]<point_cloud_range[3]) & (points_in_lidar[:,1]>point_cloud_range[1]) & (points_in_lidar[:,1]<point_cloud_range[4])
        points_in_lidar_range = points_in_lidar[mask,0:2]
        if len(points_in_lidar_range) > 1:
            label = MAP_CLASSES.index(lane_types[idx])
            line = LineString(points_in_lidar_range).simplify(0.2, preserve_topology=True)
            line = np.array(line.coords)
            map_anno[label].append(line)

    for idx in range(len(trigger_volumes_points)):
        if not trigger_volumes_types[idx] in MAP_CLASSES:
            continue
        points = trigger_volumes_points[idx]
        points = np.concatenate([points,np.ones((points.shape[0],1))],axis=-1)
        points_in_lidar = (world2lidar @ points.T).T
        mask = (points_in_lidar[:,0]>point_cloud_range[0]) & (points_in_lidar[:,0]<point_cloud_range[3]) & (points_in_lidar[:,1]>point_cloud_range[1]) & (points_in_lidar[:,1]<point_cloud_range[4])
        points_in_lidar_range = points_in_lidar[mask,0:2]
        if mask.all():
            label = MAP_CLASSES.index(trigger_volumes_types[idx])
            line = LineString(points_in_lidar_range).simplify(0.2, preserve_topology=True)
            line = np.array(line.coords)
            map_anno[label].append(line)

    return map_anno

def generate_infos(folder_list,workers,train_or_val,tmp_dir, map_infos):

    folder_num = len(folder_list)
    devide_list = [(folder_num//workers)*i for i in range(workers)]
    devide_list.append(folder_num)
    for i in range(workers):
        sub_folder_list = folder_list[devide_list[i]:devide_list[i+1]]
        process = multiprocessing.Process(target=preprocess, args=(sub_folder_list,i,tmp_dir,train_or_val, map_infos))
        process.start()
        process_list.append(process)
    for i in range(workers):
        process_list[i].join()
    union_data = []
    for i in range(workers):
        with open(join(OUT_DIR,tmp_dir,'b2d_infos_'+train_or_val+'_'+str(i)+'.pkl'),'rb') as f:
            data = pickle.load(f)
        union_data.extend(data)
    with open(join(OUT_DIR,'b2d_infos_'+train_or_val+'.pkl'),'wb') as f:
        pickle.dump(union_data,f)
        print("write!")
    print(train_or_val, len(union_data))

if __name__ == "__main__":

    os.makedirs(OUT_DIR,exist_ok=True)
    argparser = argparse.ArgumentParser(description=__doc__)
    argparser.add_argument('--tmp_dir', default="tmp_data", )
    args = argparser.parse_args()    
    process_list = []
    with open(split_file,'r') as f:
        train_val_split = json.load(f)
        
    all_folder = os.listdir(join(DATAROOT,'v1'))
    train_list = []
    for foldername in all_folder:
        if 'Town' in foldername and 'Route' in foldername and 'Weather' in foldername and not join('v1',foldername) in train_val_split['val']:
            train_list.append(join('v1',foldername))   
    print('processing map data...')
    # map_infos = gengrate_map(MAP_ROOT)
    with open(join(OUT_DIR,'b2d_map_infos.pkl'),'rb') as f:
        map_infos = pickle.load(f)

    #preprocess(train_list[1:2], 0, args.tmp_dir, "train", map_infos)
    # print('processing train data...')
    generate_infos(train_list, 16,'train',args.tmp_dir, map_infos)
    # print('processing val data...')
    # generate_infos(train_val_split['val'], 16,'val',args.tmp_dir, map_infos)

    print('finish!')