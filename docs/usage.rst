=====
Usage
=====

TRAMPOLINO is called directly from the command line::

    trampolino

Without any further arguments, this command is equivalent to `trampolino -help` and it shows the general help.

TRAMPOLINO has three subcommand, each of them specific to one of the steps to reconstruct tractography: `recon`, `track` and `filter`.
It is possible to show the help for the related subcommand::

    trampolino recon --help

One can provide just one or more of the subcommands depending on the desired results, e.g. just processing the diffusion data or also reconstructing the actual streamlines.
In the following paragraphs, some examples are showed for each of the three package interfaces implemented so far. For the sake of showing how detailed a command can be, some examples are quite long. For short-, to-the-point examples, you can have a look at the section about *using the Force!*


=======
MRtrix3
=======

Estimation of the ODF using the multi-tissue multi-shell spherical deconvolution approach (mtms-csd)::

    trampolino -n msmt_csd -r example_results recon -i sherbrooke_3shell/dwi.nii.gz -v sherbrooke_3shell/bvec.txt -b sherbrooke_3shell/bval.txt mrtrix_msmt_csd


Streamlines tracking using the iFOD2 probabilistic algorithm::

    trampolino -n msmt_csd -r example_results track -o wm.mif -s seed.mif mrtrix_tckgen


Both the steps combined::

    trampolino -n msmt_csd -r example_results recon -i sherbrooke_3shell/dwi.nii.gz -v sherbrooke_3shell/bvec.txt -b sherbrooke_3shell/bval.txt mrtrix_msmt_csd track mrtrix_tckgen

When the steps are combined, there is no need to specify the input of each step: the output from the `recon` step are automatically fed into the `track` step.

The previous steps plus the SIFT filtering::

    trampolino -n msmt_csd -r example_results recon -i sherbrooke_3shell/dwi.nii.gz -v sherbrooke_3shell/bvec.txt -b sherbrooke_3shell/bval.txt mrtrix_msmt_csd track mrtrix_tckgen filter mrtrix_tcksift


The whole workflow using three angular threshold and two different algorithms (multiple results are generated)::

    trampolino -n msmt_csd -r example_results recon -i sherbrooke_3shell/dwi.nii.gz -v sherbrooke_3shell/bvec.txt -b sherbrooke_3shell/bval.txt mrtrix_msmt_csd track --angle 30,45,60 --algorithm iFOD2,SD_Stream mrtrix_tckgen filter mrtrix_tcksift


The previous example but doing ensemble tractography over the angles::

    trampolino -n msmt_csd -r example_results recon -i sherbrooke_3shell/dwi.nii.gz -v sherbrooke_3shell/bvec.txt -b sherbrooke_3shell/bval.txt mrtrix_msmt_csd track --angle 30,45,60 --algorithm iFOD2,SD_Stream --ensemble angle mrtrix_tckgen filter mrtrix_tcksift


For the sake of simplicity, the examples for the other software packages directly show the combined commands, but it is in any case possible to run just one of the steps and use the parallel and ensemble features.

=================
Diffusion Toolkit
=================

Estimation of the tensor from the diffusion data, streamlines tracking and spline-based filtering::

    trampolino -n dtk_wf -r dti_results recon -i sherbrooke_3shell/dwi.nii.gz -v -v sherbrooke_3shell/bvec.txt -b sherbrooke_3shell/bval.txt dtk_dtirecon track dtk_dtitracker filter dtk_spline


==========
DSI Studio
==========

Processing the data using GQI and streamline tracking::

    trampolino -n dsi_wf -r dsi_results recon -i dwi.nii.gz -v bvec.txt -b bval.txt dsi_rec track dsi_trk


============
dMRI Trekker
============

Obtaining a simple tractogram from 10000 seeds using a FOD estimated with MRtrix3::

    trampolino -n trekker -r trekker_results track -o wm.mif -s mask.mif --opt seed_count:10000 trekker


==========
TractSeg
==========

Segmenting the corpus callosum with TractSeg given a FOD estimated with MRtrix3::

    trampolino -n tractseg -r tractseg_results track -o wm.mif -s mask.mif tractseg


The same case as before, but including the FOD estimation::

    trampolino -n tractseg -r tractseg_results recon -i sherbrooke_3shell/dwi.nii.gz -v sherbrooke_3shell/bvec.txt -b sherbrooke_3shell/bval.txt mrtrix_msmt_csd track tractseg



============
Force Mode
============

If you wish to try out different options for only one of the three stages without bothering too much about the other two or supplying your own data, you might want to use the --force functionality of trampolino. Let's say you just want to try out three different angular thresholds using iFOD2 of MRtrix3, the command you want to use looks as follows::

    trampolino --force track --angle 30,45,60 mrtrix_tckgen

Using the --force flag in your command, trampolino will download an example DWI dataset and produce all required input files, without the need of specifying them yourself. Depending on the interface you specify for the workflow, trampolino will do the required steps using the same interface. In the above case, trampolino will e.g. run the default reconstruction using MRtrix3.

Similar to this, if you only care about e.g. streamline filtering, the following is possible::

    trampolino --force filter dtk_spline

In this case, trampolino would download the example dataset, run the default reconstruction and streamline tractography using the Diffusion Toolkit, and finally execute the filtering options you provided.

This can be a useful tool to rapidly retrieve some sample results for exploration purposes. Consider this example with TractSeg, where a corpus callosum is obtained just launching::

    trampolino --force track tractseg


==========
Conversion
==========

TRAMPOLINO provides a conversion subcommand for tractography, so one is able to easily go from TRK to TCK and viceversa.
Converting from TRK to TCK is immediate::

    trampolino convert -t track.trk trk2tck
    
Converting from TCK to TRK requires a reference volume::

    trampolino convert -t track.tck -r meanb0.nii.gz tck2trk

Finally, the conversion subcommand can be concatenated as the others::

    trampolino track -o wm.mif -s brainmask.mif mrtrix_tckgen convert -r meanb0.nii.gz tck2trk
    

==========
Containers
==========

It is possible to directly run a given workflow in a container from TRAMPOLINO. This may be desirable in several scenarios, for example:

1. the desired software package is not installed;
2. the software package is not _installable_ (e.g. trekker on macOS);
3. there may be software conflicts on the host machine (!).

To run the workflows in a container, it is necessary to install both Docker (see [these instructions](https://docs.docker.com/get-docker/)) and the Docker API::

    pip install docker

Once you have installed it, you need an image for a suitable container. The one I created (the `Dockerimage` is available in the codebase, folder `containers`) can be pulled directly from DockerHub with::

    docker pull ingmatman/trampolino
    
Otherwise, you can build it locally::

    docker build -t ingmatman/trampolino $TRAMPOLINO_PATH/containers

Once you have built it, you can run for example::

    trampolino --container --force -n trekker-docker -r docker_results track trekker

This will start the workflow inside a container, and will save the results and the logs in the output folder.
To keep temporary files, you can add the option `--keep`. Also to use a custom image (i.e. with a different tag from `ingmatman/trampolino`), you can pass it with the `--image` option. An example of both these options::

    trampolino --container --name my_image --keep -n msmt_csd -r example_results track -o wm.mif -s seed.mif mrtrix_tckgen
    
So far, the `ingmatman/trampolino` includes MRtrix3 (`3.0.0`) and Trekker (`0.7`). More tools are coming soon!
