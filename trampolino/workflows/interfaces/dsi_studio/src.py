from nipype.interfaces.base import (TraitedSpec, File, traits, CommandLine, InputMultiPath,
                                    CommandLineInputSpec)
import os


class GenSrcInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr='--source=%s',
        mandatory=True,
        position=-4,
        desc='input image')
    bval_file = File(
        exists=True,
        argstr='--bval=%s',
        mandatory=True,
        position=-3,
        desc='bval data')
    bvec_file = File(
        exists=True,
        argstr='--bvec=%s',
        mandatory=True,
        position=-2,
        desc='bvec data')
    out_file = File("dwi.src",
        argstr='--output=%s',
        usedefault=True,
        position=-1,
        desc='output image')


class GenSrcOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='output image in .src format')


class GenSrc(CommandLine):

    _cmd = 'dsi_studio --action=src'
    input_spec = GenSrcInputSpec
    output_spec = GenSrcOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.join(os.path.dirname(self.inputs.in_file), self.inputs.out_file)
        return outputs
