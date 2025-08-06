import os, sys
os.environ['PYOPENGL_PLATFORM'] = 'egl'

import numpy as np
import cv2
import shutil
from pathlib import Path
import pyrender

from visualize.pyrender_olat_scene import PyRenderOLATScene
from utils.avif_image_utils import load_image_np


class ImageSequence:
    """Represents a sequence of images found in a particular directory."""

    def __init__(self, sequence_id, image_path_dir, image_end=".avif"):
        """
        Parameters
        ----------
        sequence_id : str
            Identifier for the sequence
        image_path_dir : Path, str
            Path to the directory containing the sequence
        image_end : str, optional
            Type of images in directory (default is ".avif")
        """

        self.sequence_id = sequence_id
        self.image_path_dir = Path(image_path_dir)
        self.image_paths = list(sorted(self.image_path_dir.glob(f'*{image_end}')))[:361] # Find images in dir

        print(f"[DEBUG] Initialized ImageSequence: {sequence_id}, Found {len(self.image_paths)} images in {image_path_dir}")

    def __len__(self):
        """Returns number of found images"""
        return len(self.image_paths)

    def __getitem__(self, idx):
        """Loads the image with index idx into a numpy array and returns it"""  

        if idx < 0 or idx >= len(self.image_paths):
            raise IndexError("Image index out of range")

        print(f"[DEBUG] Loading image {idx} from sequence {self.sequence_id}")
        img_np = load_image_np(str(self.image_paths[idx]))

        return img_np


class Take:
    """Represents a single capture (set of ImageSequences, one for each camera)."""


    def __init__(self, take_id):
        """
        Parameters
        ----------
        take_id : str
            Identifier for the take
        """

        self.take_id = take_id
        self.sequences = []  # List of ImageSequence objects
        print(f"[DEBUG] Initialized Take: {take_id}")

        # Optional rendering for mesh
        self.pyrender_scene = None
        self.renderer = None

    def add_cameras(self, sequences):
        self.sequences.extend(sequences)
        print(f"[DEBUG] Added {len(sequences)} sequences to Take {self.take_id}")
    
    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        """Returns the ImageSequence with index idx"""

        if idx < 0 or idx >= len(self.sequences):
            raise IndexError("Sequence index out of range")
        
        img_seq = self.sequences[idx]

        return img_seq

    def render_mesh(self, idx):
        """ If available, also returns the mesh rendered from camera with index idx.
        Camera is adjusted automatically, lighting of the mesh must be controlled manually."""
        mesh_img_np = None

        if self.pyrender_scene is not None and self.renderer is not None:
            self.pyrender_scene.change_camera(idx)
            mesh_img_np = self.renderer.render(self.pyrender_scene.scene, flags=pyrender.constants.RenderFlags.SHADOWS_ALL)[0][:, :, ::-1]/255.

        return mesh_img_np

    def add_pyrender_scene(self, mesh_path, texture_path, calib_folder, lights_pos_path, lights_seq_path):
        """ Adds a pyrender scene for mesh rendering to this capture

        Parameters
        ----------
        mesh_path : Path, str
            Path to the model.obj
        texture_path : Path, str
            Path to the texture
        calib_folder : Path, str
            Path to the directory containing the camera.calib
        lights_pos_path : Path, str
            Path to the light position .pc
        lights_seq_path : Path, str
            Path to the light order .txt
        """
        img_sample = self.sequences[0][0]
        W, H = img_sample.shape[1], img_sample.shape[0]

        self.pyrender_scene = PyRenderOLATScene(W, H, mesh_path, texture_path, calib_folder, lights_pos_path, lights_seq_path)
        self.renderer = pyrender.offscreen.OffscreenRenderer(W, H)

        print(f"[DEBUG] Added pyrender scene to Take {self.take_id}")


class OLATExplorer:
    """ Adds a pyrender scene for mesh rendering to this capture"""

    def __init__(self):
        self.takes = []

        self.number_cams = None
        self.number_frames = None

        self.take_idx = 0
        self.seq_idx = 0
        self.img_idx = 0

        self.mesh_enable = True
        self.mesh_image_overlap = 0

        print("[DEBUG] Initialized OLATExplorer")


    def add_take(self, take):
        """ Adds a take (capture) for rendering
        Parameters
        ----------
        take : Take
            take to render
        """

        if self.number_cams is None or self.number_frames is None:
            self.number_cams = len(take.sequences)
            self.number_frames = len(take.sequences[0]) if take.sequences else 0

            OLAT_FB_FRAMES = [14, 34, 55, 76, 97, 118, 139, 160, 181, 202, 223, 244, 265, 286, 307, 328, 349]
            self.frame_to_light = [] # -1 fullbright, other is single light

            count = 0
            for frame in range(self.number_frames):
                if frame <= OLAT_FB_FRAMES[0] or frame in OLAT_FB_FRAMES or count >= 331:
                    self.frame_to_light.append(-1)
                    continue
                
                self.frame_to_light.append(count)
                count += 1
        
        assert len(take) == self.number_cams, "Number of sequences in take does not match the expected number of cameras."
        for sequence in take.sequences:
            assert len(sequence) == self.number_frames, "Number of images in sequence does not match the expected number of frames."


        

        self.takes.append(take)
        print(f"[DEBUG] Added Take {take.take_id} with {len(take.sequences)} sequences to OLATExplorer")

    def display_image(self, image, window_name="OLATExplorer"):
        """ Displays an image using opencv
        Parameters
        ----------
        image : np.array
            image to display
        window_name : str
            name of the opencv window
        """

        if not isinstance(image, np.ndarray):
            raise ValueError("Input image must be a numpy array.")
        print(f"[DEBUG] Displaying image in window: {window_name}")
        cv2.imshow(window_name, image)

    def run(self):
        """ Starts the render loop. Left: GT image, Right (if enabled): rendered mesh
        Controls:
        r: reset image and camera index
        q/w: previous/next take
        i/k: previous/next camera
        j/l: previous/next image
        m: enable/disable mesh rendering
        n: switch image/mesh overlap (0: None, 1: Blend, 2: Outline)
        """

        print("[DEBUG] Starting OLATExplorer run loop")

        while True:
            print(f"[DEBUG] Current state: take_idx={self.take_idx}, cam_idx={self.seq_idx+1}, img_idx={self.img_idx}, olat_light={self.frame_to_light[self.img_idx]}")

   
            image = self.takes[self.take_idx][self.seq_idx][self.img_idx]
            
            # Scale the image down by half
            height, width = image.shape[:2]
            image = cv2.resize(image, (width // 2, height // 2), interpolation=cv2.INTER_AREA)


            # Also render mesh if enabled
            if self.mesh_enable:
                # Adjust lighting
                if self.frame_to_light[self.img_idx] == -1:
                    self.takes[self.take_idx].pyrender_scene.fullbright_light()
                else:
                    self.takes[self.take_idx].pyrender_scene.olat_light(self.frame_to_light[self.img_idx])

                # Get correct mesh image
                mesh_img = self.takes[self.take_idx].render_mesh(self.seq_idx)
                assert mesh_img is not None, "Unable to render mesh"
                mesh_height, mesh_width = mesh_img.shape[:2]
                assert mesh_width == width and mesh_height == height, "Rendered mesh does not match image size"
                mesh_img = cv2.resize(mesh_img, (width // 2, height // 2), interpolation=cv2.INTER_AREA)

                if self.mesh_image_overlap == 0: # Do nothing
                    pass

                if self.mesh_image_overlap == 1: # Blend mesh render with main image
                    mask_mesh = mesh_img.mean(axis=2)
                    mask_mesh[mask_mesh > 230./250.] = 0
                    mesh_img[mask_mesh == 0] = 0

                    image = image*0.5 + mesh_img*0.55


                if self.mesh_image_overlap == 2: # Draw outline of mesh on image
                    mask_mesh = mesh_img.mean(axis=2)
                    mask_mesh[mask_mesh > 230./250.] = 0
                    kernel = np.ones((3, 3), np.uint8)
                    erosion = cv2.erode(np.copy(mask_mesh), kernel, iterations=1)
                    erosion = mask_mesh - erosion

                    mask_mesh = mesh_img.mean(axis=2)
                    image[mask_mesh == erosion, :] = np.array([0, 0, 1])

                # Final image to display
                image = np.concatenate((image, mesh_img), axis=1)


            self.display_image(image)

            key = cv2.waitKey(0)
            if key == ord('q'):  # Previous take
                self.take_idx = (self.take_idx - 1) % len(self.takes)
                print("[DEBUG] Moved to previous take")
            elif key == ord('w'):  # Next take
                self.take_idx = (self.take_idx + 1) % len(self.takes)
                print("[DEBUG] Moved to next take")
            elif key == ord('i'):  # 'i' key (previous sequence)
                self.seq_idx = (self.seq_idx - 1) % len(self.takes[self.take_idx])
                print("[DEBUG] Moved to previous sequence")
            elif key == ord('k'):  # 'k' key (next sequence)
                self.seq_idx = (self.seq_idx + 1) % len(self.takes[self.take_idx])
                print("[DEBUG] Moved to next sequence")
            elif key == ord('j'):  # 'j' key (previous image)
                self.img_idx = (self.img_idx - 1) % len(self.takes[self.take_idx][self.seq_idx])
                print("[DEBUG] Moved to previous image")
            elif key == ord('l'):  # 'l' key (next image)
                self.img_idx = (self.img_idx + 1) % len(self.takes[self.take_idx][self.seq_idx])
                print("[DEBUG] Moved to next image")
            elif key == ord('r'):  # Reset image and sequence
                self.seq_idx = 0
                self.img_idx = 0
                print("[DEBUG] Reset sequence and image indices")
            elif key == ord('m'):  # Enable/Disable mesh rendering
                self.mesh_enable = not self.mesh_enable
                print("[DEBUG] Flip mesh_enable")
            elif key == ord('n'):  # Enable/Disable mesh rendering
                self.mesh_image_overlap = (self.mesh_image_overlap + 1) % 3
                print("[DEBUG] Next mesh image overlap mode")
            elif key == 27:  # Escape key to exit
                print("[DEBUG] Exiting OLATExplorer")
                cv2.destroyAllWindows()
                break




