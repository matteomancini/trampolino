==========
TRAMPOLINO
==========


.. image:: https://img.shields.io/pypi/v/trampolino.svg
        :target: https://pypi.python.org/pypi/trampolino

.. image:: https://img.shields.io/travis/matteomancini/trampolino.svg
        :target: https://travis-ci.org/matteomancini/trampolino

.. image:: https://readthedocs.org/projects/trampolino/badge/?version=latest
        :target: https://trampolino.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status




TRAMPOLINO (TRActography Meta-Pipeline cOmmand LINe tOol) is a command line interface tool
for brain tractography. It leverages the Nipype Python package to offer an immediate way to
reconstruct an orientation distribution function, use it to track the streamlines and
eventually filter them, all using existing software toolboxes.

At the moment it is under active development and support mainly MRtrix but the plan
is to include as many software alternatives as possible.


* Free software: MIT license
* Documentation: https://trampolino.readthedocs.io.


Features
========

* Composable command line interfaces built using the Click Python package;
* One-command generation of multiple results using different parameters (e.g. angular thresholds, tracking algorithm);
* Ensemble tractography implementation;

Requirements
============

TRAMPOLINO requires the GraphViz_ visualization software and the MRtrix3_ tool.



Installing TRAMPOLINO
=====================
TRAMPOLINO can be easily installed using pip::

    pip install trampolino

Running TRAMPOLINO
==================
To try TRAMPOLINO, you can download some example data using this script::

    get_example_data

It will download the Sherbrooke multi-shell dataset from DiPy_. Then you can run::

    trampolino -n msmt_csd -r example_results recon -i sherbrooke_3shell/dwi.nii.gz -v sherbrooke_3shell/bvec.txt -b sherbrooke_3shell/bval.txt mrtrix_msmt_csd track --angle 30,45 --algorithm iFOD2,SD_Stream mrtrix_tckgen

And you have your first results!

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _GraphViz: http://www.graphviz.org
.. _MRtrix3: https://github.com/MRtrix3/mrtrix3
.. _DiPy: https://github.com/nipy/dipy
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
