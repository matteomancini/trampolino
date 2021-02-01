from nipype.interfaces import utility as util
from nipype.pipeline import engine as pe
from .interfaces import dmri_trekker as trek
from .interfaces import mrtrix3 as mrtrix3
import os.path


def create_pipeline(name="trekker", opt="", ensemble=""):

    parameters = {'seed_count': 5000}

    ensemble_dict = {}

    inputnode = pe.Node(
        interface=util.IdentityInterface(
            fields=["odf", "seed", "seed_count"]),
            name="inputnode")

    if opt is not None:
        opt_list = opt.split(',')
        for o in opt_list:
            try:
                [key, value] = o.split(':')
                parameters[key] = value
            except ValueError:
                print(o+': irregular format, skipping')

    # to ensure that FOD and seed from MRtrix3 are in NIFTI format
    mrconvert_fod = pe.Node(mrtrix3.MRConvert(), name='convert_fod')
    mrconvert_fod.inputs.out_file = 'fod.nii.gz'
    mrconvert_seed = pe.Node(mrtrix3.MRConvert(), name='convert_seed')
    mrconvert_seed.inputs.out_file = 'seed.nii.gz'

    tckgen = pe.Node(trek.Trekker(), name='track')
    tckgen.inputs.count = int(parameters['seed_count'])

    output_fields = ["tck"]
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=output_fields),
        name="outputnode")

    workflow = pe.Workflow(name=name)
    workflow.base_output_dir = name

    workflow.connect([(inputnode, mrconvert_fod, [("odf", "in_file")])])

    workflow.connect([(mrconvert_fod, tckgen, [("out_file", "in_file")])])

    workflow.connect([(inputnode, mrconvert_seed, [("seed", "in_file")])])

    workflow.connect([(mrconvert_seed, tckgen, [("out_file", "seed")])])

    workflow.connect([(tckgen, outputnode, [("out_file", "tck")])])

    return workflow


def get_parent():
    return "mrtrix_msmt_csd"
