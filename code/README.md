# Tools for HumanOLAT

## Contents
1. [Install](#install)
2. [General](#general)
3. [Dataset Visualizer](#dataset-visualizer)

## Install

To setup a conda environment to run the code in this directory, simply run
```
conda env create -f environment.yml
conda activate HumanOLAT_Tools
```

## General

General dataset readers (cameras and lights) can be found in `./utils`. An example on how to perform OLAT-based image relighting using the OLAT EnvMaps can be found in `run_olat_relight_example.py` and `./olat_relight`. We also provide a script and code to write out training and testing `.json` files as well as `.ply` pointclouds sampled from the meshes in `run_json_write_example.py` and `./train_tools`.

All scripts expect the data to be organized in the same way as the `processed` dataset. If you have dowloaded `extracted_avif`images, please also download the `processed` dataset and move the `images_raw` folders into the same directories as their respective `images_processed` folders.

Please view the repective files for comprehensive documentation.

## Dataset Visualizer

We provide an opencv-based viewer for the images and meshes contained in the dataset. To start, run
```
python run_dataset_viewer.py --subject SUBJECT_C003 /PATH/TO/YOUR
```

You can replace SUBJECT_C003 with whatever subject you with to view. In the viewer, the left side shows the current image, while the right side the rendered mesh (if available and enabled), rendered under OLAT light for OLAT frames and fullbright light otherwise. 

Controls are:
```
esc: close the visualizer
j/l: previous/next image
i/k: previous/next camera
q/w: previous/next capture
m: enable/disable mesh rendering
n: switch mesh-onto-image rendering (cycles through NONE => BLEND => OUTLINE => NONE) 
```
