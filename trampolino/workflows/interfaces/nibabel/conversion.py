from nipype.interfaces.base import (TraitedSpec, BaseInterface, File,
                                    BaseInterfaceInputSpec)
import nibabel as nib
import os

class Tck2TrkInputSpec(BaseInterfaceInputSpec):
    input_tck = File(
        exists=True,
        mandatory=True,
        desc="Input file in .tck"
    )
    input_ref = File(
        exists=True,
        mandatory=True,
        desc="Input reference file (e.g. T1-weighted volume)"
    )
    output_trk = File(
        'track.trk',
        usedefault=True,
        desc=(
            "Output file in .trk"
        )
    )


class Tck2TrkOutputSpec(TraitedSpec):
    output_trk = File(exists=True)


class Tck2Trk(BaseInterface):
    input_spec = Tck2TrkInputSpec
    output_spec = Tck2TrkOutputSpec

    def _run_interface(self, runtime):
        from nibabel.streamlines import Field
        from nibabel.orientations import aff2axcodes

        tck = nib.streamlines.load(self.inputs.input_tck)

        nii = nib.load(self.inputs.input_ref)

        header = {}
        header[Field.VOXEL_TO_RASMM] = nii.affine.copy()
        header[Field.VOXEL_SIZES] = nii.header.get_zooms()[:3]
        header[Field.DIMENSIONS] = nii.shape[:3]
        header[Field.VOXEL_ORDER] = "".join(aff2axcodes(nii.affine))

        self._tractogram = tck.tractogram
        self._header = header

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_trk'] = os.path.abspath(self.inputs.output_trk)
        nib.streamlines.save(self._tractogram, outputs['output_trk'], header=self._header)
        return outputs


class Trk2TckInputSpec(BaseInterfaceInputSpec):
    input_trk = File(
        exists=True,
        mandatory=True,
        desc="Input file in .trk"
    )
    output_tck = File(
        'track.tck',
        usedefault=True,
        desc=(
            "Output file in .tck"
        )
    )


class Trk2TckOutputSpec(TraitedSpec):
    output_tck = File(exists=True)


class Trk2Tck(BaseInterface):
    input_spec = Trk2TckInputSpec
    output_spec = Trk2TckOutputSpec

    def _run_interface(self, runtime):
        trk = nib.streamlines.load(self.inputs.input_trk)

        self._tractogram = trk.tractogram

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_tck'] = os.path.abspath(self.inputs.output_tck)
        nib.streamlines.save(self._tractogram, outputs['output_tck'])
        return outputs
