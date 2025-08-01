# HumanOLAT (ICCV 2025)
Official repository for code, tools and information related to the HumanOLAT dataset, to be published at ICCV 2025. 
[[Project Page]](https://vcai.mpi-inf.mpg.de/projects/HumanOLAT/) [[Paper (Coming Soon)]](https://en.wikipedia.org/wiki/Coming_Soon) [[Data]](https://gvv-assets.mpi-inf.mpg.de/)

![img](assets/teaser.png)

**For any questions, please contact Timo Teufel [tteufel@mpi-inf.mpg.de] .**

## Contents
1. [Quick Start](#quick-start)
2. [Code and Tools](#code-and-tools)
3. [Processing Raw Data](#processing-raw-data)
4. [Citation](#citation)
5. [Acknowledgements](#acknowledgements)
6. [TODOs](#todos)

## Quick Start

To access the dataset, navigate to the authentication site by going to https://gvv-assets.mpi-inf.mpg.de/, searching for "HumanOLAT" and clicking on the button "Software". Afterwards, register a new account and supply the requested information. Please note that we require everyone who wishes to access to access the dataset to apply using an **institutional e-mail address** and **describe the intended usage in detail** (i.e. not just "research").

After your account has been approved, simply login and download the parts of the dataset which interest you. In general, we recommend downloading the `processed_data.tar` file (10GB), which contains the entire dataset stored using undistorted, masked and motion corrected 1K `.avif` files.

Due to large storage requirements, some `.tar` files are split into chunks of 100GB. Once you have downloaded all parts belowing to one `.tar`, you can extract the data using

```cat /PATH/TO/DOWNLOAD/{TAR_NAME}.tar.gz.part* | tar -xzvf - -C /PATH/TO/OUTPUT```

Please view the `DATASHEET.md` for detailed information on the contents of the dataset.  

## Code and Tools

(COMING SOON) Information on available code and tools will be added here

## Processing Raw Data

(COMING SOON) Information on how to process the raw .RED files will be added soon.

## Citation

If you find this dataset useful for your research, please consider staring this repo and citing
```
@inproceedings{teufelgera2025HumanOLAT,
  title = {HumanOLAT: A Large-Scale Dataset for Full-Body Human Relighting and Novel-View Synthesis},
  author = {Timo Teufel and Pulkit Gera and Xilong Zhou and Umar Iqbal and Pramod Rao and Jan Kautz and Vladislav Golyanik and Christian Theobalt},
  year = {2025},
  journal={International Conference on Computer Vision (ICCV)}
}
```

## Acknowledgements

This research was supported by NVIDIA.

## TODOs

- [x] Add information on how to access the dataset 
- [ ] Add sources for code and tools
- [ ] Add information on how to process raw data

