from nipype.interfaces.base import (TraitedSpec, File, traits, CommandLine, InputMultiPath,
                                    CommandLineInputSpec)
from nipype.utils.filemanip import copyfile
import os


class FiberTrackInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr='--source=%s',
        mandatory=True,
        position=-6,
        desc='input image')
    seed = File(
        exists=True,
        argstr='--seed=%s',
        mandatory=False,
        position=-5,
        desc='seed image')
    nos = traits.Int(5000,
        argstr='--fiber_count=%d',
        usedefault=True,
        position=-4,
        desc='number of streamlines')
    min_length = traits.Int(20,
        argstr='--min_length=%s',
        usedefault=True,
        position=-3,
        desc='minimum_length')
    angle_thres = traits.Int(60,
        argstr='--turning_angle=%d',
        usedefault=True,
        position=-2,
        desc='angular threshold')
    out_file = File("track.trk.gz",
        argstr='--output=%s',
        usedefault=True,
        position=-1,
        desc='output image')


class FiberTrackOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='output image in .trk format')


class FiberTrack(CommandLine):

    _cmd = 'dsi_studio --action=trk'
    input_spec = FiberTrackInputSpec
    output_spec = FiberTrackOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.join(os.path.dirname(self.inputs.in_file), self.inputs.out_file)
        return outputs
