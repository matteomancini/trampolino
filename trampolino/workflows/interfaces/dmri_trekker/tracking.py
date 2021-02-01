from nipype.interfaces.base import (TraitedSpec, File, traits, CommandLine, InputMultiPath,
                                    CommandLineInputSpec)
from nipype.utils.filemanip import copyfile
import os


class TrekkerInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr='-fod %s',
        mandatory=True,
        desc='Input FOD image')

    seed = File(
        exists=True,
        argstr='-seed_image %s',
        mandatory=True,
        desc='Input seed image')

    out_file = File(
        'output.vtk',
        argstr='-output %s',
        mandatory=True,
        usedefault=True,
        desc='output file containing tracks')

    count = traits.Int(
        1000,
        argstr='-seed_count %d',
        mandatory=True,
        usedefault=True,
        desc='Number of random seeds to generate')

    require_entry = File(
        exists=True,
        argstr='-pathway=require_entry %s')
    stop_at_entry = File(
        exists=True,
        argstr='-pathway=stop_at_entry %s')
    require_exit = File(
        exists=True,
        argstr='-pathway=require_exit %s')
    stop_at_exit = File(
        exists=True,
        argstr='-pathway=stop_at_exit %s')
    discard_if_enters = File(
        exists=True,
        argstr='-pathway=discard_if_enters %s')
    discard_if_exits = File(
        exists=True,
        argstr='-pathway=discard_if_exits %s')
    discard_if_ends_inside = File(
        exists=True,
        argstr='-pathway=discard_if_ends_inside %s')


class TrekkerOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='the output tracks')


class Trekker(CommandLine):

    _cmd = 'trekker'
    input_spec = TrekkerInputSpec
    output_spec = TrekkerOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = os.path.abspath(self.inputs.out_file)
        return outputs
