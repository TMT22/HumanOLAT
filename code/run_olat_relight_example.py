import os,cv2
from pathlib import Path

from olat_relight.olat_relight import *
from utils.metadata_readers import *


# Example script for OLAT relighting

# ---------------------------------------------------------

###########################
# ADJUST THESE PARAMETERS #
###########################

PATH_TO_DATASET = Path("/CT/HumanOLAT/static00/FinalData/") # Path to dataset root
SUBJECT = "SUBJECT_C058" # Name of subject to process
POSE = "POSE_00" # Name of pose to process
CAM = "Cam01" # Name of camera to process

OUT_PATH = Path("./out/olat_relight") # Where to write the .ply and json files

# ---------------------------------------------------------

lights_pos_path = PATH_TO_DATASET / SUBJECT / "shared" / "LSX_light_positions_aligned.pc"
lights_sort_path = PATH_TO_DATASET / SUBJECT  / "shared" / "LSX3_light_z_spiral.txt"

# We do not exclude door lights, since their lighting can still be used for OLAT relighing
light_positions, light_img = read_OLAT_info(lights_pos_path,lights_sort_path, OLAT_START=14, OLAT_FB_MODULO=21, exclude_door_lights=False)

# ---------------------------------------------------------

##############################
# ADJUST THIS TO YOUR LIKING #
##############################

OUT_PATH.mkdir(parents=True, exist_ok=True)

print("Building OLAT relighter ...")
olat_relighter = OLATRelightWithEnvMap("./olat_relight/OLAT_EnvMaps")

# Load OLATs
print("Loading OLATs ...")
olat_id = f"{SUBJECT}_{POSE}_{CAM}"
olat_paths = sorted(Path(PATH_TO_DATASET / SUBJECT / POSE / "images_processed" / CAM).glob(f"*.avif"))
olat_paths_filtered = list([olat_paths[i] for i in light_img])

olat_relighter.load_olats(olat_id, olat_paths_filtered)

# Load envmap
print("Loading EnvMap ...")
envmap_id = "class"
olat_relighter.load_envmap(envmap_id, f"./olat_relight/example_envmaps/{envmap_id}.exr")

# Relight and write
relit_image = olat_relighter.relight(olat_id, envmap_id, scale=1.)
cv2.imwrite(str(OUT_PATH / f"{olat_id}_{envmap_id}.png"), (255 * relit_image).astype(np.uint8))

# ---------------------------------------------------------
