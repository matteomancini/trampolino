from nipype.interfaces import utility as util
from nipype.pipeline import engine as pe
from .interfaces import tractseg as ts
from .interfaces import mrtrix3 as mrtrix3
import os.path


def create_pipeline(name="trekker", opt="", ensemble=""):

    parameters = {'bundle': 'CC'}

    ensemble_dict = {}

    inputnode = pe.Node(
        interface=util.IdentityInterface(
            fields=["odf", "seed"]),
            name="inputnode")

    if opt is not None:
        opt_list = opt.split(',')
        for o in opt_list:
            try:
                [key, value] = o.split(':')
                parameters[key] = value
            except ValueError:
                print(o+': irregular format, skipping')

    sh2peaks = pe.Node(mrtrix3.Sh2Peaks(), name='sh2peaks')
    sh2peaks.inputs.out_file = "peaks.nii.gz"

    seg_mask = pe.Node(ts.TractSeg(), name='tractseg_mask')

    seg_tom = pe.Node(ts.TractSeg(), name='tractseg_tom')
    seg_tom.inputs.output_type = 'TOM'

    tckgen = pe.Node(mrtrix3.Tractography(), name='track')
    tckgen.inputs.algorithm = 'FACT'

    output_fields = ["tck"]
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=output_fields),
        name="outputnode")

    workflow = pe.Workflow(name=name)
    workflow.base_output_dir = name

    workflow.connect([(inputnode, sh2peaks, [("odf", "in_file")])])

    workflow.connect([(sh2peaks, seg_mask, [("out_file", "in_file")])])

    workflow.connect([(seg_mask, seg_tom, [("out_dir", "out_dir")])])
    workflow.connect([(sh2peaks, seg_tom, [("out_file", "in_file")])])

    workflow.connect([(inputnode, tckgen, [("seed", "seed_image")])])
    workflow.connect([(seg_tom, tckgen, [("CC", "in_file")])])

    workflow.connect([(tckgen, outputnode, [("out_file", "tck")])])

    return workflow


def get_parent():
    return "mrtrix_msmt_csd"
