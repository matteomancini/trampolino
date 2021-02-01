TRAMPOLINO
==========

[![image](https://img.shields.io/pypi/v/trampolino.svg)](https://pypi.python.org/pypi/trampolino) [![Documentation Status](https://readthedocs.org/projects/trampolino/badge/?version=latest)](https://trampolino.readthedocs.io/en/latest/?badge=latest)

TRAMPOLINO (TRActography Meta-Pipeline cOmmand LINe tOol) is a command
line interface tool for brain tractography, written in Python. It leverages the Nipype
Python package to offer an immediate way to reconstruct an orientation
distribution function, use it to track the streamlines and eventually
filter them, all using existing software toolboxes.

At the moment it is under active development but supports already several
software packages and the plan is to include as many software alternatives as possible.

-   Free software: MIT license
-   Documentation: <https://trampolino.readthedocs.io>.


Features
========

-   Composable command line interfaces built using the Click Python
    package;
-   One-command generation of multiple results using different
    parameters (e.g. angular thresholds, tracking algorithm);
-   Ensemble tractography implementation;
-   Short-cut workflows to rapidly generate results from sample data;
-   Native support to containers (through the Docker API);


Requirements
============

TRAMPOLINO requires Python 3 and the [GraphViz](http://www.graphviz.org)
visualization software. The Python packages required are listed in the
[requirements.txt]{.title-ref} file.

At the moment, TRAMPOLINO can be used to run the following tools:

-   [MRtrix3](https://github.com/MRtrix3/mrtrix3)
-   [DiffusionToolkit](http://trackvis.org/dtk/)
-   [DSI\_Studio](http://dsi-studio.labsolver.org)
-   [dMRI Trekker](https://dmritrekker.github.io/)
-   [TractSeg](https://github.com/MIC-DKFZ/TractSeg)

The current container image supports MRtrix3 (`3.0.0`) and Trekker (`0.7`).
To run those workflows directly in a container, you need to install the Docker API:

    pip install docker



Installing TRAMPOLINO
=====================

TRAMPOLINO can be easily installed using pip:

    pip install trampolino


Running TRAMPOLINO
==================

To try TRAMPOLINO, you can download some example data using this script:

    get_example_data

It will download the Sherbrooke multi-shell dataset from
[dipy](https://github.com/nipy/dipy). Then you can run:

    trampolino -n msmt_csd -r example_results recon -i sherbrooke_3shell/dwi.nii.gz -v sherbrooke_3shell/bvec.txt -b sherbrooke_3shell/bval.txt mrtrix_msmt_csd track --angle 30,45 --algorithm iFOD2,SD_Stream mrtrix_tckgen

And you have your first results!


Contributors
------------

Matteo Mancini

Bastian David - <https://github.com/bastiandavid>

Want to contribute? Have suggestions/crazy ideas/evil plans? [Get in touch](mailto:ingmatteomancini@gmail.com)!


Credits
-------

TRAMPOLINO is built on top of the amazing [Nipype](https://nipype.readthedocs.io/en/latest/) toolkit. At the moment, some of the interfaces already available in Nipype are included in order to fix and/or add features for the sake of compatibility with modern tools. This is only temporary, and once those features are merge in Nipype, TRAMPOLINO will use directly the native interfaces. Other important tools for TRAMPOLINO are [nibabel](https://nipy.org/nibabel/) and [dipy](https://dipy.org), currently used respectively for conversion and fetching data. Be sure to check them out!

TRAMPOLINO has started its life during [Brainhack School](https://brainhackmtl.github.io/school2019/index.html) (Montreal, August 2019) and has been first extended during the [OHBM Brainhack](https://ohbm.github.io/hackathon2020/) in 2020 (virtual event). Therefore, TRAMPOLINO would not exist if it wasn't for [Brainhack](https://brainhack.org)!

This package was created with
[Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage)
project template.
