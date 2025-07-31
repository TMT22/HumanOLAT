Datasheet in the format of "Datasheets for datasets" as described in

> Gebru, Timnit, et al. "Datasheets for datasets." Communications of the ACM 64.12 (2021): 86-92.

Template obtained from https://github.com/facebookresearch/goliath/blob/main/DATASHEET.md

# HumanOLAT Dataset

<!-- TODO add brief summary here, bibtex -->


## Motivation

1. **For what purpose was the dataset created?** *(Was there a specific task in mind? Was there a specific gap that needed to be filled? Please provide a description.)*

    This dataset was created to ...



1. **Who created this dataset (e.g., which team, research group) and on behalf of which entity (e.g., company, institution, organization)?**

    The dataset was curated by the Visual Computing and Artificial Intelligence Department (D6) at the Max Planck Institute for informatics, Saarland Informatics Campus. 

1. **Who funded the creation of the dataset?** *(If there is an associated grant, please provide the name of the grantor and the grant name and number.)*

    NVIDIA


1. **Any other comments?**

    None.



## Composition


1. **What do the instances that comprise the dataset represent (e.g., documents, photos, people, countries)?** *(Are there multiple types of instances (e.g., movies, users, and ratings; people and interactions between them; nodes and edges)? Please provide a description.)*



    Each instance comprises three to four full-body captures of one subject (person):
    1. a capure with the person in A-pose
    2. a capure with the person two-three creative poses
    3. an empty background capture

    Each capture contains
    1. 1 white light illumination frame
    2. 2 gradient illumination frames
    3. 10 environment map captures
    4. 331 OLAT illuminations 
    collected over a total duration of ~10s.

    For each subject, we provide as well
    5. a camera calibration estimated with Metashape (calculated using the first white light fram of the A-pose capture)
    6. a mesh for each pose estimated with Metashape (calculated using the first white light frame)
    7. a segmentation for each pose estimated with Sapiens (calculated using the first white light frame)
    7. pose annotations for each pose estimated with OpenPose (calculated using the first white light frame)
    7. SMPL-X shape parameters for each pose estimated with EasyMocap (calculated using the OpenPose annotations)

    A comprehensive list of which captures belong to which subject can be found in TO_ADD.


2. **How many instances are there in total (of each type, if appropriate)?**

    Our dataset constains 21 subjects, each containing the capture types described above.


3. **Does the dataset contain all possible instances or is it a sample (not necessarily random) of instances from a larger set?** *(If the dataset is a sample, then what is the larger set? Is the sample representative of the larger set (e.g., geographic coverage)? If so, please describe how this representativeness was validated/verified. If it is not representative of the larger set, please describe why not (e.g., to cover a more diverse range of instances, because instances were withheld or unavailable).)*

    The captures contain fine-grained OLATs capturing the reflectance field of the full human body. Since a single recording takes around ~10s, we require the subjects to remain still for the duration of the capture.

    We note that the number of subjects (21) and associated poses (3-4) may not be sufficient for e.g. larg-scale training of generative priors. We aim to extend the size of the dataset in the future.


4. **What data does each instance consist of?** *(``Raw'' data (e.g., unprocessed text or images)or features? In either case, please provide a description.)*


    The processed dataset for direct use is structured as
    ```
    SUBJECT_{subject_id}
    ├── POSE_{pose_number}
    │   ├── images_processed
    │   │   ├── Cam{camera_number}
    │   │   └────── {capture_id}.{image_number}.avif
    │   ├── model
    │   │   ├── material.mtl
    │   │   ├── model.jpeg
    │   │   └── model.obj
    │   ├── segmentations
    │   │   ├── masks/000
    │   │   ├────── Cam{camera_number}.png
    │   │   ├── segmentations_np/000
    │   │   ├────── Cam{camera_number}.npy
    │   │   ├── segmentations_vis/000
    │   │   └────── Cam{camera_number}.jpg
    │   ├── openpose
    │   │   ├── {camera_number}
    │   │   └────── 000_keypoints.json
    │   └── smpl-x
    │       ├── 000000.jpg
    │       └── 000000.json
    └── shared
        ├── cameras.calib
        ├── LSX_light_positions_aligned.pc
        └── LSX3_light_z_spiral.mov
    ```

    There are a total of 21 subjects (`SUBJECT_{subject_id}`). Each of them has subfolders corresponding to the recorded poses (`POSE_{pose_number}`) as well as attributes shared between poses (`shared`). The subfolder `POSE_00` contains the A-pose, every other pose subfolder contains a creative pose. Each pose subfolder has subfolders containing captured and processed images (`images_processed`), the metashape mesh (`model`), sapiens segmentations (`segmentations`), openpose annotations (`openpose`) and smpl-x shape parameters (`smpl-x`). The `shared` subfolder contains the camera calibration (`cameras.calib`) and light metadata (`LSX_light_positions_aligned.pc` and `LSX3_light_z_spiral.txt`).

    The mesh is provided as a `.obj` with associated textures. For segmentations, `segmentations_np` contains the class-wise segmentation as generated by sapiens, (visualized in `segmentations_vis`) while `masks` contains the associated binary per-camera image masks. Pose annotations and SMPL-X parameters are provided as `.json` (containing the output of OpenPose and EasyMocap respectively). The `smpl-x` folder also contains a visualization (`000000.jpg`). In all of the cases, the number `000`/`000000` refers to the first white light frame, which has been undistorted before any further computation. 

    The images have been generated from the extracted `.avif` files (see below) by applying undistortion and. segmenting with the with the associtated sapiens mask. Moreover, all images with an `image_number` >= 14 have been motion corrected toward the first white light frame (frames with a lower `image_number` are considered to be close enough to this target frame already). Images are given at 1K resolution, with sizes `675x1280 (WxH)` (subjects `C003`, `C006` and `C010`) and `810x1440 (WxH)` (all other subjects) respectively. These `.avif` files are in a gamma corrected sRGB color space

    The data containing extracted .avifs with no masking and optical flow correction applied is structured as
    ```
    SUBJECT_{subject_id}
    ├── POSE_{pose_number}
    │   └── images_raw
    │       ├── Cam{camera_number}
    │       └────── {capture_id}.{image_number}.avif
    └── shared
        ├── bg_images_raw
        ├── Cam{camera_number}
        └────── {capture_id}.{image_number}.avif
    ```

    This contains the `.avif` images without any undistortion, masking and motion correction applied. They were obtained by extracting the raw `.RED` files to `.exr` (using an sRGB color space without gamma correction), which were subsequentally converted to `.avif` using ImageMagick's `convert` command with quality setting 99. 


    Further information regarding the raw RED will follow in the near future.
    
   



5. **Is there a label or target associated with each instance? If so, please provide a description.**

    No.


6. **Is any information missing from individual instances?** *(If so, please provide a description, explaining why this information is missing (e.g., because it was unavailable). This does not include intentionally removed information, but might include, e.g., redacted text.)*

    No.


7. **Are relationships between individual instances made explicit (e.g., users' movie ratings, social network links)?** *( If so, please describe how these relationships are made explicit.)*

    Yes; the fully processed `.avif` and extracted `.avif` images are stored under the same associated subfolder.


8. **Are there recommended data splits (e.g., training, development/validation, testing)?** *(If so, please provide a description of these splits, explaining the rationale behind them.)*

    We recommend withholding some cameras and OLAT illuminations for testing. We will provide a script to generate easily readable train and test `.json` in NeRF format.


9. **Are there any errors, sources of noise, or redundancies in the dataset?** *(If so, please provide a description.)*

    Assets are naturally noisy, since they are computed automatically. For example, segmentations might be imperfect.
    Cameras are also naturally subject to multiple sources of noise such as thermal noise, chromatic aberrations, lense deformations, and manufacturing defects. Moreover,  images provided `.avif` can exhibit quantization artifacts, especically in low luminance areas.

10. **Is the dataset self-contained, or does it link to or otherwise rely on external resources (e.g., websites, tweets, other datasets)?** *(If it links to or relies on external resources, a) are there guarantees that they will exist, and remain constant, over time; b) are there official archival versions of the complete dataset (i.e., including the external resources as they existed at the time the dataset was created); c) are there any restrictions (e.g., licenses, fees) associated with any of the external resources that might apply to a future user? Please provide descriptions of all external resources and any restrictions associated with them, as well as links or other access points, as appropriate.)*

    The dataset is self-contained.


11. **Does the dataset contain data that might be considered confidential (e.g., data that is protected by legal privilege or by doctor-patient confidentiality, data that includes the content of individuals' non-public communications)?** *(If so, please provide a description.)*

    No.


12. **Does the dataset contain data that, if viewed directly, might be offensive, insulting, threatening, or might otherwise cause anxiety?** *(If so, please describe why.)*

    No.


13. **Does the dataset relate to people?** *(If not, you may skip the remaining questions in this section.)*

    Yes, the dataset consists of captures of people.


14. **Does the dataset identify any subpopulations (e.g., by age, gender)?** *(If so, please describe how these subpopulations are identified and provide a description of their respective distributions within the dataset.)*

    No.


15. **Is it possible to identify individuals (i.e., one or more natural persons), either directly or indirectly (i.e., in combination with other data) from the dataset?** *(If so, please describe how.)*

    Yes, by looking at the provided images of the subjects.


16. **Does the dataset contain data that might be considered sensitive in any way (e.g., data that reveals racial or ethnic origins, sexual orientations, religious beliefs, political opinions or union memberships, or locations; financial or health data; biometric or genetic data; forms of government identification, such as social security numbers; criminal history)?** *(If so, please provide a description.)*

    No.

17. **Any other comments?**

    None.





## Collection Process


18. **How was the data associated with each instance acquired?** *(Was the data directly observable (e.g., raw text, movie ratings), reported by subjects (e.g., survey responses), or indirectly inferred/derived from other data (e.g., part-of-speech tags, model-based guesses for age or language)? If data was reported by subjects or indirectly inferred/derived from other data, was the data validated/verified? If so, please describe how.)*

    The subjects were captured in a light stage.


19. **What mechanisms or procedures were used to collect the data (e.g., hardware apparatus or sensor, manual human curation, software program, software API)?** *(How were these mechanisms or procedures validated?)*

    Our light stage is equipped with 40 RED Komodo 6K cameras and 331 individually controllable LEDs capable of emitting red, green, blue, amber, and white light (RGBAW). The cameras and lights are arranged 360◦ around the subject, enabling the capture of synchronized multi-illumination sequences at 30 FPS with a resolution of 5K.

    The subjects were instructed to remain as still as possible for the duration of the capture. 


20. **If the dataset is a sample from a larger set, what was the sampling strategy (e.g., deterministic, probabilistic with specific sampling probabilities)?**

    In this dataset we aim to sample densely the reflectance field of full-body humans. We achieve this by collecting 331 OLAT illuminations per capture, one for each LED in our subject.


21. **Who was involved in the data collection process (e.g., students, crowdworkers, contractors) and how were they compensated (e.g., how much were crowdworkers paid)?**

    Subjects were at least 18 years old at the time of capture and provided their informed consent in writing.

    The captures are lead by a research intern (Pulkit Gera) that prompted the subjects to remain as still as possible.
    A lot of custom software and hardware is involved in the process of data collection and asset generation. Please refer to the list of authors of our paper for a list of the people involved in this process.


22. **Over what timeframe was the data collected?** *(Does this timeframe match the creation timeframe of the data associated with the instances (e.g., recent crawl of old news articles)?  If not, please describe the timeframe in which the data associated with the instances was created.)*

    INFORMATION WILL BE ADDED SHORTLY


1. **Were any ethical review processes conducted (e.g., by an institutional review board)?** *(If so, please provide a description of these review processes, including the outcomes, as well as a link or other access point to any supporting documentation.)*

    We follow an internal research review process that includes, among other things, ethical considerations.


1. **Does the dataset relate to people?** *(If not, you may skip the remaining questions in this section.)*

    Yes; the dataset consists of captures of people.


1. **Did you collect the data from the individuals in question directly, or obtain it via third parties or other sources (e.g., websites)?**

    From the individuals directly.


1. **Were the individuals in question notified about the data collection?** *(If so, please describe (or show with screenshots or other information) how notice was provided, and provide a link or other access point to, or otherwise reproduce, the exact language of the notification itself.)*

    Yes; the subjects provided their informed written consent.


1. **Did the individuals in question consent to the collection and use of their data?** *(If so, please describe (or show with screenshots or other information) how consent was requested and provided, and provide a link or other access point to, or otherwise reproduce, the exact language to which the individuals consented.)*

    Yes; the individuals gave their informed consent in writing for both capture and distribution of the data.
    We are not making the agreements public at this time.


1. **If consent was obtained, were the consenting individuals provided with a mechanism to revoke their consent in the future or for certain uses?** *(If so, please provide a description, as well as a link or other access point to the mechanism (if appropriate).)*

    INFORMATION WILL BE ADDED SHORTLY


1. **Has an analysis of the potential impact of the dataset and its use on data subjects (e.g., a data protection impact analysis) been conducted?** *(If so, please provide a description of this analysis, including the outcomes, as well as a link or other access point to any supporting documentation.)*

    Yes, we internally reviewed the .


1. **Any other comments?**

    None.





## Preprocessing/cleaning/labeling


1. **Was any preprocessing/cleaning/labeling of the data done (e.g., discretization or bucketing, tokenization, part-of-speech tagging, SIFT feature extraction, removal of instances, processing of missing values)?** *(If so, please provide a description. If not, you may skip the remainder of the questions in this section.)*

    To reduce the storage requirements of the dataset, we did the following:

    * Images were downsampled to 1K resolution.
    Compressing the RGB images with lossy avif compression at quality level 99.
    * Masking out the background


1. **Was the "raw" data saved in addition to the preprocessed/cleaned/labeled data (e.g., to support unanticipated future uses)?** *(If so, please provide a link or other access point to the "raw" data.)*

    Yes; the raw data is stored internally at out department.
    The raw data along with porcessing instructions will be made publicly available, but requires some additional time due to the large amount of storage involved.


1. **Is the software used to preprocess/clean/label the instances available?** *(If so, please provide a link or other access point.)*

    Yes; the methods used to produce the segmentation, motion correction and pose/SMPL-X parameters will be made available shortly.


1. **Any other comments?**

    None.





## Uses


35. **Has the dataset been used for any tasks already?** *(If so, please provide a description.)*

    Yes, we evaluted various OLAT-based relighting and an illumination harmonization method on our dataset. Please see the paper for more details.


36. **Is there a repository that links to any or all papers or systems that use the dataset?** *(If so, please provide a link or other access point.)*

    Not yet, as publications use this dataset we will update the github repository.


37. **What (other) tasks could the dataset be used for?**

    INFORMATION TO ADD



38. **Is there anything about the composition of the dataset or the way it was collected and preprocessed/cleaned/labeled that might impact future uses?** *(For example, is there anything that a future user might need to know to avoid uses that could result in unfair treatment of individuals or groups (e.g., stereotyping, quality of service issues) or other undesirable harms (e.g., financial harms, legal risks)  If so, please provide a description. Is there anything a future user could do to mitigate these undesirable harms?)*

    None to our knowledge.


39. **Are there tasks for which the dataset should not be used?** *(If so, please provide a description.)*

    No.


40. **Any other comments?**

    None.




## Distribution


1. **Will the dataset be distributed to third parties outside of the entity (e.g., company, institution, organization) on behalf of which the dataset was created?** *(If so, please provide a description.)*

    Yes, the dataset is available under "LICENSE INFORMATION TO ADD".


1. **How will the dataset be distributed (e.g., tarball  on website, API, GitHub)?** *(Does the dataset have a digital object identifier (DOI)?)*

    Please visit  https://gvv-assets.mpi-inf.mpg.de/HumanOLAT/ to apply for and download the data. The data will be provided in the form of tarballs.
    MORE DETAILED INFORMATION TO ADD


1. **When will the dataset be distributed?**

    The dataset is available as of Wednesday August 1st, 2025.


1. **Will the dataset be distributed under a copyright or other intellectual property (IP) license, and/or under applicable terms of use (ToU)?** *(If so, please describe this license and/or ToU, and provide a link or other access point to, or otherwise reproduce, any relevant licensing terms or ToU, as well as any fees associated with these restrictions.)*

    The dataset is licensed under "LICENSE INFORMATION TO ADD".


1. **Have any third parties imposed IP-based or other restrictions on the data associated with the instances?** *(If so, please describe these restrictions, and provide a link or other access point to, or otherwise reproduce, any relevant licensing terms, as well as any fees associated with these restrictions.)*

    Not to our knowledge.


1. **Do any export controls or other regulatory restrictions apply to the dataset or to individual instances?** *(If so, please describe these restrictions, and provide a link or other access point to, or otherwise reproduce, any supporting documentation.)*

    Not to our knowledge.


1. **Any other comments?**

    None.



## Maintenance


1. **Who is supporting/hosting/maintaining the dataset?**

    INFORMATION TO ADD


1. **How can the owner/curator/manager of the dataset be contacted (e.g., email address)?**

    You may contact Timo Teufel via email at tteufel@mpi-inf.mpg.de.


1. **Is there an erratum?** *(If so, please provide a link or other access point.)*

    Currently, no. If we do encounter errors,  we will provide a list of issues on github as well as best practices to work around them.


1. **Will the dataset be updated (e.g., to correct labeling errors, add new instances, delete instances')?** *(If so, please describe how often, by whom, and how updates will be communicated to users (e.g., mailing list, GitHub)?)*

    Same as previous.


1. **If the dataset relates to people, are there applicable limits on the retention of the data associated with the instances (e.g., were individuals in question told that their data would be retained for a fixed period of time and then deleted)?** *(If so, please describe these limits and explain how they will be enforced.)*

    No.


1. **Will older versions of the dataset continue to be supported/hosted/maintained?** *(If so, please describe how. If not, please describe how its obsolescence will be communicated to users.)*

    INFORMATION TO ADD


1. **If others want to extend/augment/build on/contribute to the dataset, is there a mechanism for them to do so?** *(If so, please provide a description. Will these contributions be validated/verified? If so, please describe how. If not, why not? Is there a process for communicating/distributing these contributions to other users? If so, please provide a description.)*

    INFORMATION TO ADD


1. **Any other comments?**

    None.