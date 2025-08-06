import os
from pathlib import Path

from visualize.olat_explorer import *
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="View data in HumanOLAT.")
    parser.add_argument("path", type=str, help="Path to the dataset")
    parser.add_argument("--subject_name", type=str, default="", help="Name of the subject, leave empty to load all")
    parser.add_argument(
        "--image_dir",
        type=str,
        default="images_processed",
        help='Name of the image directory to use (default: "images_processed")'
    )
    return parser.parse_args()



if __name__ == "__main__":
    args = parse_args()

    MAIN_PATH = Path(args.path)
    subjects = [args.subject_name]
    if args.subject_name == "":
        subjects = sorted(os.listdir(MAIN_PATH))

    explorer = OLATExplorer()

    # Loading of takes can be adjusted freely

    for subject in subjects:
        print(f"Loading subject {subject}")
        for i in range(len(os.listdir(MAIN_PATH / subject ))-1):
            pose_name = f"POSE_{i:02}"
            take_id = subject + "_" + pose_name
            take = Take(take_id)

            for cam in range(1, 41):
                image_path_dir = MAIN_PATH / subject / pose_name / args.image_dir / f"Cam{cam:02}"
                sequence = ImageSequence(take_id+f"_Cam{cam:02}", image_path_dir)
                take.add_cameras([sequence])

            take.add_pyrender_scene(
                mesh_path=MAIN_PATH / subject / pose_name / "model" / "model.obj",
                texture_path=MAIN_PATH / subject / pose_name / "model" / "model.jpeg",
                calib_folder=MAIN_PATH / subject / "shared",
                lights_pos_path=MAIN_PATH / subject / "shared" / "LSX_light_positions_aligned.pc",
                lights_seq_path=MAIN_PATH / subject  / "shared" / "LSX3_light_z_spiral.txt"
            )

            explorer.add_take(take)
        
    explorer.run()


