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
In the following paragraphs, some examples are showed for each of the three package interfaces implemented so far.


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
Force Mode
============

If you wish to try out different options for only one of the three stages without bothering too much about the other two or supplying your own data, you might want to use the --force functionality of trampolino. Let's say you just want to try out three different angular thresholds using iFOD2 of MRtrix3, the command you want to use looks as follows::

    trampolino --force track --angle 30,45,60 mrtrix_tckgen

Using the --force flag in your command, trampolino will download an example DWI dataset and produce all required input files, without the need of specifying them yourself. Depending on the interface you specify for the workflow, trampolino will do the required steps using the same interface. In the above case, trampolino will e.g. run the default reconstruction using MRtrix3.

Similar to this, if you only care about e.g. streamline filtering, the following is possible::

    trampolino --force filter dtk_spline

In this case, trampolino would download the example dataset, run the default reconstruction and streamline tractography using the Diffusion Toolkit, and finally execute the filtering options you provided.

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
    
