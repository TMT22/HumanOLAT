from PIL import Image
import pillow_avif # Depending on your python version, this may already be included in PIL
import numpy as np
import cv2, os
import torch

# Needed to allow loading .exr
os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"


# GAMMA CORRECTION
# Make sure to only use this, mixing with e.g. simple 2.2 gamma can cause quantization artifacts to be amplified 

def sRGB_to_linear(srgb, gamma=2.4):
    """ Conversion from gamma-corrected sRGB to linear RGB
    
    Parameters
    ----------
    srgb : np.array
        numpy sRGB image with values in range 0 - 1
    gamma : float
        gamma to use for decoding

    Returns
    -------
    linear : np.array
        numpy linear image with values in range 0 - 1
    """

    if isinstance(srgb, np.ndarray):
        srgb = np.clip(srgb, 0, 1)
        linear = np.where(
            srgb <= 0.04045,
            srgb / 12.92,
            ((srgb + 0.055) / 1.055) ** gamma
        )
        return linear
    
    if torch.is_tensor(srgb):
        srgb = torch.clamp(srgb, 0, 1)
        linear = torch.where(
            srgb <= 0.04045,
            srgb / 12.92,
            torch.pow((srgb + 0.055) / 1.055,  gamma)
        )
        return linear

    raise Exception(f"Expected numpy or torch array, but got {type(srgb)}.") 


def linear_to_srgb(linear, gamma=2.4):
    """ Conversion from linear RGB to gamma-corrected sRGB
    
    Parameters
    ----------
    srgb : np.array
        numpy linear image with values in range 0 - 1
    gamma : float
        gamma to use for encoding

    Returns
    -------
    srgb : np.array
        numpy sRGB image with values in range 0 - 1
    """
    if isinstance(linear, np.ndarray):
        linear = np.clip(linear, 0, 1)
        srgb = np.where(
            linear <= 0.0031308,
            12.92 * linear,
            1.055 * np.power(linear, 1/gamma) - 0.055
        )
        return srgb
    
    if torch.is_tensor(linear):
        linear = torch.clamp(linear, 0, 1)
        srgb = torch.where(
            linear <= 0.0031308,
            12.92 * linear,
            1.055 * torch.pow(linear, 1 / gamma) - 0.055
        )
        return srgb

    raise Exception(f"Expected numpy or torch array, but got {type(linear)}.") 
        

# IMAGE LOADING + PROCESSING

def load_image_np(image_path, return_linear=False):
    """ Loads a .exr or .avif image into a numpy arrar
    Note: as of now (July 2025) pillow does not support loading >8-bit AVIF images

    Parameters
    ----------
    image_path : Path, str
        path to the image
    return_linear : bool
        return linear instead of sRGB encoded values

    Returns
    -------
    image_np : np.array
        loaded numpy image (H, W, C) with values in range 0 - 1. Channels are in BGR order.
    """

    image_path = str(image_path)

    if image_path.endswith('.exr'):
        exr_image = cv2.imread(image_path, -1)
        image_np = np.array(exr_image)
        if return_linear:
            return image_np
        else:
            return linear_to_srgb(image_np)

    elif image_path.endswith('.avif'):
        image = Image.open(image_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')

        image_np = np.asarray(image).astype(np.float32)[:, :, ::-1] / 255.0        
        
        if return_linear:
            return sRGB_to_linear(image_np)
        else:
            return image_np

    else:
        raise ValueError("Unsupported file format.")


def undistort_image_cv(img, intrinsic, distortion):
    """ Undistorts a given image with opencv

    Parameters
    ----------
    img : np.array
        numpy cv2 image to undistort
    intrinsic : np.array
        intrinsic matrix of the image
    distortion : np.array
        opencv distortion coefficients

    Returns
    -------
    image : np.array
        undistorted image
    """

    return cv2.undistort(img, intrinsic[:3, :3], distortion)