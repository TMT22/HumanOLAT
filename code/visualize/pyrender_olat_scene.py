import sys
import os
import math
from pathlib import Path

from pathlib import Path
from utils.metadata_readers import read_calib, read_OLAT_info
import cv2 as cv
import numpy as np

import pyrender
import trimesh
from scipy.spatial.transform import Rotation as R


# Internal PyRender scene for visualizing mesh under OLAT lighting
# TODO: Add docstrings

class PyRenderOLATScene:
    """Manages a PyRender scene for mesh rendering under OLAT lighting"""

    def __init__(self, W, H, mesh_path, texture_path, calib_folder, lights_pos_path, lights_seq_path, no_light_spheres=True):
        self.NO_LIGHT_SPHERES = no_light_spheres # Should spheres marking the light positions be rendered?
        # NOTE: Light spheres also throw shadows in directonal light mode, so we disable them

        self.W, self.H = W, H
        self.LIGHT_SOURCE_MODEL = ["DIRECTIONAL", "SPOT"][0]
        # NOTE: Spot light rendering does not seem to work properly for certain angles
        # NOTE: Sadly, point lights in PyRender do not support shadows


        self.scene = pyrender.Scene(ambient_light=[0.05, 0.05, 0.05])
        
        self.load_mesh(mesh_path, texture_path)
        self.load_camera(calib_folder)
        self.load_light_info(lights_pos_path, lights_seq_path)

        self.scene_camera = {
            "idx": -1,
            "node": None
        }
        self.change_camera(0)

        self.scene_lights = []
        self.default_spot_intensity = 25000000.0
        self.default_dir_intensity = 3

        self.fullbright_light()


    def load_mesh(self, mesh_path, texture_path):
        self.mesh_obj = dict()

        self.mesh_obj['tm'] = trimesh.load(str(mesh_path))
        self.mesh_obj['tex'] = pyrender.Texture(source=cv.cvtColor(cv.imread(str(texture_path)), cv.COLOR_BGR2RGB), source_channels='RGB')
        self.mesh_obj['mat'] = pyrender.MetallicRoughnessMaterial(
            metallicFactor=0.2,
            alphaMode='OPAQUE',
            baseColorFactor=(0.3, 0.3, 0.8, 1.0)
        )  # Default material
        self.mesh_obj['mat'] = pyrender.material.MetallicRoughnessMaterial(baseColorTexture=self.mesh_obj['tex'])
        self.mesh_obj['mesh'] = pyrender.Mesh.from_trimesh(self.mesh_obj['tm'], material=self.mesh_obj['mat'])
        self.mesh_obj['mesh_node'] = self.scene.add(self.mesh_obj['mesh'])

    def load_camera(self, calib_folder):
        self.INTR, self.EXTR, self.DISTOR, self.focal_length = [], [], [], []
        read_calib(str(calib_folder), self.W, self.INTR, self.EXTR,  DISTOR=self.DISTOR, focal_length=self.focal_length, invert_extr=False)

    def load_light_info(self, lights_pos_path, lights_seq_path):
        self.light_positions, self.light_img = read_OLAT_info(lights_pos_path, lights_seq_path, 14, 21, exclude_door_lights=False)
        self.ls_approximate_center = np.mean(self.light_positions, axis=0)

        self.light_spheres_node = None # self.add_light_spheres(range(len(self.light_positions)))
        self.active_light_spheres_node = None

    def add_light_spheres(self, light_ids, radius=50, color=[1.0, 0.0, 0.0], overwrite_add=False):
        if self.NO_LIGHT_SPHERES and not overwrite_add:
            return None

        pts =  1000*self.light_positions[np.array(light_ids)]
        sm = trimesh.creation.uv_sphere(radius=radius)
        sm.visual.vertex_colors = color
        tfs = np.tile(np.eye(4), (len(pts), 1, 1))
        tfs[:,:3,3] = pts

        lights_mesh = pyrender.Mesh.from_trimesh(sm, poses=tfs)

        return self.scene.add(lights_mesh)

    def change_camera(self, new_cam_idx):
        if self.scene_camera['node'] is not None:
            self.scene.remove_node(self.scene_camera['node'])

        # Intrinic parameters 
        fx, fy, cx, cy = self.INTR[new_cam_idx][0, 0], self.INTR[new_cam_idx][1, 1], self.INTR[new_cam_idx][0, 2], self.INTR[new_cam_idx][1, 2]

        # Extrinsic parameters (pose)
        extr = np.linalg.inv(np.copy(self.EXTR[new_cam_idx]))
        extr[:3, 1:3] *= -1

        # Create final camera
        cam_obj = pyrender.IntrinsicsCamera(fx, fy, cx, cy, zfar=10000.0)
        
        self.scene_camera['idx'] = new_cam_idx
        self.scene_camera['node'] = self.scene.add(cam_obj, pose=extr)

    def change_lights(self, new_light_ids, intensity_spot=50000000.0, intensity_dir=2):

        def normalize(v):
            norm = np.linalg.norm(v)
            if norm == 0: 
                return v
            return v / norm

        # Remove previous lights
        for light in self.scene_lights:
            self.scene.remove_node(light['node'])

        if self.active_light_spheres_node is not None:
            self.scene.remove_node(self.active_light_spheres_node)

        self.scene_lights = []

        for light_id in new_light_ids:
            if self.LIGHT_SOURCE_MODEL == "DIRECTIONAL":
                light_obj = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=intensity_dir)

                pose = np.identity(4)
                pose[:3, 3] = 1000*np.array(self.light_positions[light_id])

                light_dir = normalize(self.ls_approximate_center - self.light_positions[light_id])
                rot_quat = normalize(np.array([light_dir[1], -light_dir[0], 0, 1-light_dir[2]])) # x, y, z, w
                r = R.from_quat(rot_quat)
                pose[:3, :3] = r.as_matrix()

                self.scene_lights.append({
                    "idx": light_id,
                    "node": self.scene.add(light_obj, pose=pose)
                })

            elif self.LIGHT_SOURCE_MODEL == "SPOT":
                light_obj = pyrender.SpotLight(color=[1.0, 1.0, 1.0], intensity=intensity_spot, innerConeAngle=(np.pi / 2.0)-1e-4, outerConeAngle = np.pi / 2.0)

                light_dir = normalize(self.ls_approximate_center - self.light_positions[light_id])

                pose = np.identity(4)
                pose[:3, 3] = 1000*np.array(self.light_positions[light_id])

                self.scene_lights.append({
                    "idx": light_id,
                    "node": self.scene.add(light_obj, pose=pose)
                })
        
        self.active_light_spheres_node = self.add_light_spheres(new_light_ids, radius=50, color=[0.0, 1.0, 0.0])

    def fullbright_light(self, light_scale=1.):
        self.change_lights(
            list(range(len(self.light_positions))), 
            intensity_spot = light_scale * self.default_spot_intensity,
            intensity_dir = light_scale * self.default_dir_intensity
        )
        self.scene.ambient_light = [light_scale * 1.0, light_scale * 1.0, light_scale * 1.0]
    
    def olat_light(self, light_idx, light_scale=1.):
        self.change_lights(
            [light_idx], 
            intensity_spot= light_scale * self.default_spot_intensity,
            intensity_dir = light_scale * self.default_dir_intensity
        )
        self.scene.ambient_light = [0.05, 0.05, 0.05]

