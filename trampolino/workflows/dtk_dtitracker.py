from nipype.interfaces import utility as util
from nipype.pipeline import engine as pe
import nipype.interfaces.diffusion_toolkit as dtk
import os.path


def create_pipeline(name="dtitracker", opt="", ensemble=""):

    parameters = {'mask2': None,
                  'mask2_thr': None}

    inputnode = pe.Node(
        interface=util.IdentityInterface(
            fields=["odf", "seed", "angle", "min_length"]),
            name="inputnode")

    if opt is not None:
        opt_list = opt.split(',')
        for o in opt_list:
            try:
                [key, value] = o.split(':')
                parameters[key] = value
            except ValueError:
                print(o+': irregular format, skipping')

    if ensemble:
        tckgen = pe.MapNode(dtk.DTITracker(),
                         name='track', iterfield=ensemble)
    else:
        tckgen = pe.Node(dtk.DTITracker(),
                         name='track')

    tckmerge = pe.Node(interface=dtk.TrackMerge(), name="merge")

    output_fields = ["tck"]
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=output_fields),
        name="outputnode")

    workflow = pe.Workflow(name=name)
    workflow.base_output_dir = name

    workflow.connect([(inputnode, tckgen, [("odf", "in_file"),
                                           ("seed", "seed_image"),
                                           ("angle", "angle"),
                                           ("min_length", "min_length")])])

    if ensemble:
        workflow.connect([
            (tckgen, tckmerge, [("out_file", "in_files")]),
            (tckmerge, outputnode, [("out_file", "tck")])
        ])
    else:
        workflow.connect([(tckgen, outputnode, [("out_file", "tck")])])

    return workflow
