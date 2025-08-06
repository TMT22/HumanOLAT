from utils.metadata_readers import *
from utils.avif_image_utils import load_image_np

import scipy.ndimage
import pywavefront
import random
from plyfile import PlyData, PlyElement

import os, sys
import numpy as np
from pathlib import Path
from tqdm import tqdm
import cv2

import json 


# .ply point cloud writing

def storePly(path, xyz, rgb, norms):
    """ Stores a pointcloud with positions, color and normals
    Adapted from gaussian splatting code

    Parameters
    ----------
    path : Path, str
        path where to store the .ply
    xyz : np.array
        positions (N, 3)
    rgb : np.array
        colors (N, 3)
    norms : np.array
        normals (N, 3)
    """

    path = str(path)
    print(f"Storing PLY file at: {path}")
    print(f"XYZ shape: {xyz.shape}, RGB shape: {rgb.shape}, Normals shape: {norms.shape}")
    
    dtype = [('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
             ('nx', 'f4'), ('ny', 'f4'), ('nz', 'f4'),
             ('red', 'u1'), ('green', 'u1'), ('blue', 'u1')]
    
    normals = norms

    elements = np.empty(xyz.shape[0], dtype=dtype)
    attributes = np.concatenate((xyz, normals, rgb), axis=1)
    elements[:] = list(map(tuple, attributes))

    vertex_element = PlyElement.describe(elements, 'vertex')
    ply_data = PlyData([vertex_element])
    ply_data.write(path)

def sampleMesh_UNIFORM(mesh, n_samples, texture_img):
    """ Uniformly samples a pywavefront mesh. See generate_point_cloud(...) for use

    Parameters
    ----------
    mesh : []
        loaded pywavefront mesh
    n_samples : int
        number of samples to take
    texture_img : np.array
        texture image
    """

    print(f"Sampling mesh uniformly with {n_samples} samples.")
    
    def normal(triangles):
        return np.cross(triangles[:, 1, 5:] - triangles[:, 0, 5:], triangles[:, 2, 5:] - triangles[:, 0, 5:], axis=1)

    def area(triangles):
        return np.linalg.norm(normal(triangles), axis=1) / 2

    assert mesh.mesh_list[0].materials[0].vertex_format == 'T2F_N3F_V3F'

    face_data = np.reshape(np.array(mesh.mesh_list[0].materials[0].vertices), (-1, 3, 8)) 
    print(f"Face data shape: {face_data.shape}")
    
    face_num, primitive_corner_num, vert_size = face_data.shape
    face_areas = area(face_data)

    prob_dist = face_areas / sum(face_areas)
    samples = np.array(random.choices(range(face_num), k=n_samples, weights=prob_dist))
    face_data = face_data[samples]

    r_triangle = np.random.random_sample((n_samples, 2))
    r_triangle[:, 0] = np.sqrt(r_triangle[:, 0])
    vertex_weights = np.stack((1 - r_triangle[:, 0], r_triangle[:, 0] * (1 - r_triangle[:, 1]), r_triangle[:, 0] * r_triangle[:, 1]), axis=-1) 

    aggregated_data = np.sum(vertex_weights[:, :, None] * face_data, axis=1)

    tex_coords = aggregated_data[:, :2]
    norms = aggregated_data[:, 2:5]
    xyzs = aggregated_data[:, 5:]

    tex_height, tex_width, _ = texture_img.shape
    print(f"Texture image shape: {texture_img.shape}")

    tex_coords[:, 1] = 1 - tex_coords[:, 1]
    tex_coords[:, 0] *= tex_width
    tex_coords[:, 1] *= tex_height
    tex_coords = tex_coords[:, ::-1]

    rgbs = np.stack((scipy.ndimage.map_coordinates(texture_img[..., 2], tex_coords.T),
                     scipy.ndimage.map_coordinates(texture_img[..., 1], tex_coords.T),
                     scipy.ndimage.map_coordinates(texture_img[..., 0], tex_coords.T))).T

    print(f"Sampled XYZs shape: {xyzs.shape}, RGBs shape: {rgbs.shape}, Normals shape: {norms.shape}")
    return xyzs, rgbs, norms

def generate_point_cloud(model_dir, target_dir, n_samples = 300_000, out_name="points3d.ply", scale_to_m=True):
    """ Generates a pointcloud .ply for the "model.obj" found in model_dir

    Parameters
    ----------
    model_dir : Path, str
        path to the model directory
    target_dir : Path, str
        where to write the final .ply
    n_samples : int
        number of point samples to take
    out_name : str
        name of the final .ply
    scale_to_m : bool
        scale the pointcloud to meters. If false, point cloud will be in millimeters
    """
    
    model_dir = Path(model_dir)
    target_dir = Path(target_dir)


    print(f"Generating point clouds for model directory: {model_dir}")

    mesh = pywavefront.Wavefront(str(model_dir / "model.obj"), collect_faces=True)
    texture_img = cv2.imread(str(model_dir / "model.jpeg"), cv2.IMREAD_COLOR)

    scale = 1000. if scale_to_m else 1.

    xyzs, rgbs, norms = sampleMesh_UNIFORM(mesh, n_samples, texture_img)
    storePly(str(target_dir / out_name), xyzs / scale, rgbs, norms)

# camera json writing

def get_image_shape(image_path):
    print(f"Getting image shape for: {image_path}")
    im = load_image_np(str(image_path))	
    print(f"Image shape: {im.shape}")
    return im.shape


def generate_cam_jsons(dataset_dir, subject_pose, out_dir,
                        name, cams_to_include, lights_to_include,
                        light_positions, light_img,
                        scale_to_m=True, img_ext=".avif"):
    """ Writes a .json in NeRF format (for OLAT images)

    Parameters
    ----------
    dataset_dir : Path, str
        path to the dataset root
    subject_pose : str
        what subject and pose to write a camera json for (example: "SUBJECT_C003/POSE_00)")
    out_dir : Path, str
        where to write the final json

    name : str
        name of the json (e.g. "train"/"test")
    cams_to_include : list
        which cameras to include in this json
    lights_to_include : list
        which lights to include (from the loaded light_positions and light_img) in this json

    light_positions : np.array
        positions of loaded light in m as provided by utils.read_OLAT_info
    light_img : np.array
        image id for loaded light as provided by utils.read_OLAT_info

    scale_to_m : bool, optional
        scale the transforms to meters. If false, transforms will be in millimeters. Default: True
    img_ext : str, optional
        image extension to detect, Default: True
    """

    dataset_dir = Path(dataset_dir)
    out_dir = Path(out_dir)

    subject = subject_pose[:12]
    pose = subject_pose[13:]

    print(f"Generating camera {name} JSONs for at subject {subject}, pose {pose} at {dataset_dir}")

    imgs_path = dataset_dir / subject / pose / "images_processed"
    _, IMAGE_W, _ = get_image_shape(list(sorted((dataset_dir / subject / pose / "images_processed" /  "Cam01").glob(f'*{img_ext}')))[0])

    print(f"Loading intrinsics for image width: {IMAGE_W}")    
    intr, extr = [], []
    read_calib(str(dataset_dir / subject / "shared"), IMAGE_W, intr, extr, scale_to_meters=scale_to_m, invert_extr=False) # Gets c2w extrinsics
    
    
    nerf_json = dict()
    nerf_json["frames"] = []

    for cam in tqdm(cams_to_include):
        print(f"Processing camera: {cam}")
        CAM_PATH = dataset_dir / subject / pose / "images_processed" / f"Cam{cam+1:>02}"

        IMGS = list(sorted(CAM_PATH.glob(f'*{img_ext}')))
        print(f"Found {len(IMGS)} images for camera {cam}")

        for light in tqdm(lights_to_include):
            img_path = IMGS[light_img[light]]

            print(f"Processing light: {light}, Image path: {img_path}")

            frame = dict()

            frame["file_ext"] = img_ext
            frame["file_path"] = str(img_path)
            frame["light_idx"] = light
            frame["cam_idx"] = cam

            transform_matrix = extr[cam].copy()
            transform_matrix[:3, 1:3] *= -1 # Flip coordinate system from OpenCV to Blender style

            frame["transform_matrix"] = transform_matrix.tolist() # should be c2w

            frame["camera_intrinsics"] = [
                intr[cam][0, 2].item(),
                intr[cam][1, 2].item(),
                intr[cam][0, 0].item(),
                intr[cam][1, 1].item()
            ]

            frame["pl_intensity"] = [
                1.0,
                1.0,
                1.0
            ]

            frame["pl_pos"] = (light_positions[light]).tolist()
            if not scale_to_m:
                frame["pl_pos"] *= 1000 # Scale point lights to mm.


            nerf_json["frames"].append(frame)
    
    with open(out_dir / f"transforms_{name}.json", "w") as outfile: 
        print(f"Writing JSON file: {out_dir / f'transforms_{name}.json'}")
        json.dump(nerf_json, outfile, indent=4)
