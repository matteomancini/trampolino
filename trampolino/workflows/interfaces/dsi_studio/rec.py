from nipype.interfaces.base import (TraitedSpec, File, traits, CommandLine, InputMultiPath,
                                    CommandLineInputSpec)
from nipype.utils.filemanip import fname_presuffix
import os


class ImageReconInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr='--source=%s',
        mandatory=True,
        position=-4,
        desc='input .src file')
    method = traits.Int(
        exists=True,
        argstr='--method=%d',
        mandatory=True,
        position=-3,
        desc='Method index')
    param0 = traits.Float(
        exists=True,
        argstr='--param0=%f',
        mandatory=True,
        position=-2,
        desc='Parameters')


class ImageReconOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='output data in .fib format')


class ImageRecon(CommandLine):

    _cmd = 'dsi_studio --action=rec'
    input_spec = ImageReconInputSpec
    output_spec = ImageReconOutputSpec

    def _list_outputs(self):
        in_prefix = self.inputs.in_file
        in_param = str(self.inputs.param0)

        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(
            fname_presuffix(
                "", prefix=in_prefix, suffix='.odf8.f5.rdi.gqi.'+in_param+'.fib.gz'))

        return outputs
