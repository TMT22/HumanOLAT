import numpy as np
import os

# Light reader
def read_OLAT_info(lights_pos_file, lights_order_file, OLAT_START=14, OLAT_FB_MODULO=21, exclude_door_lights=True):
    """ Reads a list of valid light positions and associated image indices 

    Parameters
    ----------
    lights_pos_file : Path, str
        path to .pc containing light positions (LSX_light_positions_aligned.pc)
    lights_order_file : Path, str 
        path to .txt containing light order (LSX3_light_z_spiral.txt)
    OLAT_START : int
        index of frame in camera sequence where OLAT starts (fullbright (FB) frame before only one light is active)
    OLAT_FB_MODULO : int
        frequency of multiplexed FB images/number of images in one multiplex cycle (<= 0 if no multiplexing)
    exclude_door_lights : bool
        do not include lights on the hatch in the final list of valid light positions (recommended when light position is required for compute)

    Returns
    -------
    light_positions : np.array
        (N_LIGHTS, 3) array containing light positions in meters (m)
    light_img : np.array
        (N_LIGHTS) array where light_img[i] => index of camera image where only light at light_positions[i] is active
        index of camera image is the same as the six digit id in the image name
    """
   
    assert OLAT_FB_MODULO != 1

    # Hard-coded door light indices
    door_lights = [178, 179, 208, 209, 210, 237, 238, 239, 240, 267, 268, 269, 270, 271, 295, 296, 297, 298, 319, 320, 321]

    light_positions = []
    light_sequence = []
    light_img = []

    # Read .pc containing light positions
    with open(str(lights_pos_file), "r") as file:
        for line in file:
            line = line.rstrip().split()
            if line[0] != 'v':
                continue

            light_positions.append([float(line[1]), float(line[2]), float(line[3])])

    # Read .txt containing light pattern (first light indexed as 1)
    with open(str(lights_order_file), "r") as file:
        for line in file:
            light_sequence.append(int(line.rstrip()) - 1)

    # Generate associations to image files
    N_LIGHTS = len(light_positions)
    N_IMGS = N_LIGHTS+1 # (+1 for first fullbright, does NOT account for FB reconstruction frames)

    # Account for FB reconstruction frames
    if OLAT_FB_MODULO > 0:
        N_IMGS += N_LIGHTS//(OLAT_FB_MODULO-1) # After this, N_IMGS should be the length of the olat recording (including FB reconstruction frames)

    # Relevant slice of frames
    light_img = list(range(OLAT_START, OLAT_START+N_IMGS))

    # Get rid of multiplexed FB frames
    if OLAT_FB_MODULO > 0:
        del light_img[OLAT_FB_MODULO-1::OLAT_FB_MODULO]

    # Get rid of beginning and end FB frames
    light_img = light_img[1:len(light_positions)+1]

    # Sanity check
    assert len(light_positions) == len(light_img) and len(light_positions) == len(light_sequence)

    # If requested, remove lights in door_lights
    if exclude_door_lights:
        new_light_sequence = []
        to_remove = []
        for i in range(len(light_sequence)):
            if light_sequence[i] in door_lights:
                to_remove.append(i)
                continue

            new_light_sequence.append(light_sequence[i])
            
        for index in sorted(to_remove, reverse=True):
            del light_img[index]

        light_sequence = new_light_sequence
    
    # Finalize lists to return
    light_sequence = np.array(light_sequence)
    light_positions = np.array(light_positions)[light_sequence]
    light_img = np.array(light_img)

    # Final sanity check and return
    assert len(light_img) == len(light_sequence) and len(light_positions) == len(light_img)


    return light_positions, light_img

# Camera reader
def read_calib(calib_dir, IMAGE_W, INTR, EXTR, scale_to_meters=False, DISTOR=None, invert_extr=True, focal_length=None):
    """ Reads camera intrinsics, extrinsics and distortion from the .calib file

    Parameters
    ----------
    calib_dir : Path, str
        path to directory containing the cameras.calib
    IMAGE_W : int
        width of the image for which to read intrinsics (read and get the shape of the first image for correct value)
    INTR : list
        an empty! list for storing read intrinsics
    EXTR : list
        an empty! list for storing read extrinsics (default setting: world-to-camera extrinsics in mm scale)
    scale_to_meters : bool, optional
        scale the read intrinsics to meters
    DISTOR : list, optional
        an empty! list for storing read distortion coefficents
    invert_extr : list, optional
        return world-to-camera (w2c) extrinsics instead of camera-to-world (c2w)
    focal_length : list, optional
        an empty! list for storing read focal lengths
    Returns
    -------
        Final intrinsics, extrinsics and distortion will be stored in the provided INTR, EXTR and DISTOR lists
    """


    calib_dir = str(calib_dir)

    INTR.clear()
    EXTR.clear()
    if DISTOR != None: DISTOR.clear()	
    if focal_length != None: focal_length.clear()  
   
   
   
    calib_dir = os.path.join(calib_dir, 'cameras.calib')
   
    if not os.path.isfile(calib_dir):
        calib_dir = calib_dir.replace('cameras.calib', 'camera.calib') 
   
    with open(calib_dir, 'r') as fp:
        while True:
            text = fp.readline()  
            if not text:
                break
            if ('distortionModel' in text):
                continue
            if ('distortion' in text) and DISTOR != None:
                dist = np.fromstring(text.replace('distortion',''), dtype=float, sep=' ')			
                DISTOR.append(dist)	

            if ('focalLength' in text) and focal_length != None:		
                focal_length.append(float(text.replace('focalLength','').split()[0]))					

            if "pixelAspect" in text:
                pixelAspect = float(text.split()[1])

            elif "extrinsic" in text:
                lines = []
                for i in range(3):
                    line = fp.readline()
                    lines.append([float(w) for w in line.strip('#').strip().split()])
                lines.append([0,0,0,1])
                extrinsic = np.array(lines).astype(np.float32)
			   
                if scale_to_meters:
                    extrinsic[:3,3] /= 1000.0
                if invert_extr:				  
                    EXTR.append(np.linalg.inv(extrinsic))
                else:
                    EXTR.append(extrinsic.reshape((4,4)))           
            elif "intrinsic" in text:
                lines = []
                line = fp.readline()
                if "time" in line:
                    continue
                for i in range(3):
                    lines_3 = [float(w) for w in line.strip('#').strip().split()]
                    lines_3.append(0)
                    lines.append(lines_3)
                    line = fp.readline()

                lines.append([0,0,0,1])
                intrinsic = np.array(lines).astype(np.float32)


                intrinsic[0,2] *= IMAGE_W
                intrinsic[1,2] *= IMAGE_W
                intrinsic[0,0] *= IMAGE_W
                intrinsic[1,1] *= IMAGE_W
			   
                                    		  			  
                INTR.append(intrinsic) 
			   
		  





