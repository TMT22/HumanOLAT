import os
from pathlib import Path

from train_tools.train_tools import *


# Example script for writing train/test .jsons and .ply files

# ---------------------------------------------------------

###########################
# ADJUST THESE PARAMETERS #
###########################

PATH_TO_DATASET = Path("/CT/HumanOLAT/static00/FinalData/") # Path to dataset root
SUBJECT = "SUBJECT_C003" # Name of subject to process
POSE = "POSE_00" # Name of pose to process

OUT_PATH = Path("./train_tools_out") # Where to write the .ply and json files

# ---------------------------------------------------------

lights_pos_path = PATH_TO_DATASET / SUBJECT / "shared" / "LSX_light_positions_aligned.pc"
lights_sort_path = PATH_TO_DATASET / SUBJECT  / "shared" / "LSX3_light_z_spiral.txt"

# We exclude door lights, since their position may be inaccurate
light_positions, light_img = read_OLAT_info(lights_pos_path,lights_sort_path, OLAT_START=14, OLAT_FB_MODULO=21, exclude_door_lights=True)

all_cams = list(range(30))


# ---------------------------------------------------------

##############################
# ADJUST THIS TO YOUR LIKING #
##############################

train_cams = [cam for cam in all_cams if cam % 5 != 0]
test_cams = [cam for cam in all_cams if cam % 5 == 0]

all_lights = list(range(len(light_positions)))
train_lights = all_lights[::3]
test_lights = all_lights[1::3]

OUT_PATH.mkdir(parents=True, exist_ok=True)
generate_point_cloud(PATH_TO_DATASET / SUBJECT / POSE / "model", OUT_PATH)

# Write train .json
generate_cam_jsons(
    PATH_TO_DATASET, SUBJECT+"_"+POSE, OUT_PATH,
    "train", train_cams, train_lights,
    light_positions, light_img
)

# Write test .jsons
generate_cam_jsons(
    PATH_TO_DATASET, SUBJECT+"_"+POSE, OUT_PATH,
    "test", test_cams, test_lights,
    light_positions, light_img
)


# ---------------------------------------------------------
