from utils.avif_image_utils import load_image_np, linear_to_srgb
from tqdm import tqdm
import numpy as np
import cv2, os
from pathlib import Path


class OLATRelight:
    """Base class for OLAT relighting"""

    def __init__(self):
        self.olat_tensors = dict()
        self.light_bases = dict()
        self.env_maps = dict()
    
    def load_olats(self, olat_id, paths_to_olat):
        """Load a set of olat images and store it under olat_id
        
        Parameters
        ----------
        olat_id : str
            identifier for this set of OLATs
        paths_to_olat : list of Path/str objects
            (sorted) paths to individual OLATs
        """
        assert olat_id not in self.olat_tensors.keys(), f"ID {olat_id} already in use"

        self.olat_tensors[olat_id] = np.stack([load_image_np(str(p), return_linear=True) for p in tqdm(paths_to_olat)])


    def load_envmap(self, envmap_id, path_to_env, clip=-1., scale_to_0_1=True):
        """Load a hdr envmap and store it under envmap_id
        
        Parameters
        ----------
        envmap_id : str
            identifier for this EnvMap
        path_to_env : Path,str
            path to envmap
        clip : float, optional
            clip all color values above this, default:10, -1 for no clipping
        scale_to_0_1 : bool, optional
            scale values in hdr to 0-1 range, default: True
        """

        assert envmap_id not in self.env_maps.keys(), f"ID {envmap_id} already in use"

        hdr = np.float32(cv2.imread(str(path_to_env), -1))
        if clip >= 0:
            hdr[hdr > clip] = clip

        if scale_to_0_1:
            max_val, min_val = hdr.max(), hdr.min()
            hdr = (hdr - min_val) / (max_val - min_val)

        self.env_maps[envmap_id] = hdr

    def generate_base(self, envmap_id):
        """Generate basis vector envmap envmap_id. Not implemented in base, overwrite.
        
        Parameters
        ----------
        envmap_id : str
            EnvMap identifier to generate base for
        """

        assert False, "NOT IMPLEMENTED, OVERWRITE"

    def relight(self, olat_id, envmap_id, scale=1.0, return_linear=False, regenerate_basis=False):
        """Generate basis vector envmap envmap_id. Not implemented in base, overwrite.
        
        Parameters
        ----------
        olat_id : str
            OLAT identifier to use for relighting
        envmap_id : str
            EnvMap identifier to use for relighting
        scale : float, optional
            scale to apply (in linear space), default: 1.0
        return_linear : bool, optional
            return linear instead of sRGB, default: False
        regenerate_basis : bool, optional
            regenerate the lighting basis, default: False
        """

        if envmap_id not in self.light_bases.keys() or regenerate_basis:
            self.generate_base(envmap_id)
        
        relit_img = np.sum((scale * self.light_bases[envmap_id][:, None, None, :] * self.olat_tensors[olat_id]), axis=0)

        if return_linear:
            return relit_img
        
        return linear_to_srgb(relit_img)


class OLATRelightWithEnvMap(OLATRelight):
    """Class for OLAT relighting using the OLAT envmaps"""
    def __init__(self, path_to_olat_envmaps):
        super().__init__()

        self.OLAT_envmaps = [] 

        # Load envmaps
        hdr_map_paths = list(sorted(Path(path_to_olat_envmaps).glob(f'*.png')))
        for idx in tqdm(range(len(hdr_map_paths))):
            in_image = np.float32(cv2.imread(hdr_map_paths[idx], -1)) / 255.0
            if in_image.max() < 0.5:
                continue # Skip fullbright OLATs

            self.OLAT_envmaps.append(in_image) 

        self.OLAT_envmaps = np.stack(self.OLAT_envmaps)
        self.OLAT_envmaps_div = np.sum((self.OLAT_envmaps), axis=(1, 2))
    
    def generate_base(self, envmap_id, scale=1.):
        assert envmap_id in self.env_maps.keys(), f"No envmap for id {self.env_maps}"

        basis = scale * np.sum((self.env_maps[envmap_id][None,] * self.OLAT_envmaps), axis=(1, 2)) / self.OLAT_envmaps_div

        self.light_bases[envmap_id] = basis