from nipype.interfaces.base import (TraitedSpec, File, traits, CommandLine, Directory,
                                    CommandLineInputSpec)
from nipype.utils.filemanip import copyfile
import os


class TractSegInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr='-i %s',
        mandatory=True,
        desc='Input peaks image')

    out_dir = Directory(
        'output',
        argstr='-o %s',
        mandatory=True,
        usedefault=True,
        desc='output folder containing segmentations')

    output_type = traits.Enum(
        'tract_segmentation',
        'endings_segmentation',
        'TOM',
        'dm_regression',
        usedefault=True,
        argstr='--output_type %s',
        desc='desired type of output')


class TractSegOutputSpec(TraitedSpec):
    out_dir = Directory(exists=True, desc='output folder containing segmentations')
    CC = File(exists=True)


class TractSeg(CommandLine):

    _cmd = 'TractSeg'
    input_spec = TractSegInputSpec
    output_spec = TractSegOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        output_type = self.inputs.output_type
        if output_type == 'tract_segmentation':
            output_type = 'bundle_segmentations'
        outputs['out_dir'] = os.path.abspath(self.inputs.out_dir)
        outputs["CC"] = os.path.abspath(
            os.path.join(self.inputs.out_dir, output_type, 'CC.nii.gz')
        )
        return outputs
