from nipype.interfaces import utility as util
from nipype.pipeline import engine as pe
import nipype.interfaces.diffusion_toolkit as dtk
import os.path


def create_pipeline(name="dtitracker", opt="", ensemble=""):

    parameters = {'mask2': None,
                  'mask2_thr': None}

    ensemble_dict = {'angle': 'angle_threshold'}

    inputnode = pe.Node(
        interface=util.IdentityInterface(
            fields=["odf", "seed", "angle", "algorithm", "min_length"]),
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
                         name='track', iterfield=ensemble_dict[ensemble])
    else:
        tckgen = pe.Node(dtk.DTITracker(), name='track')
    tckgen.inputs.mask1_threshold = 0.1

    tckmerge = pe.Node(interface=dtk.TrackMerge(), name="merge")

    output_fields = ["tck"]
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=output_fields),
        name="outputnode")

    workflow = pe.Workflow(name=name)
    workflow.base_output_dir = name

    workflow.connect([(inputnode, tckgen, [("odf", "tensor_file"),
                                           ("seed", "mask1_file"),
                                           ("angle", "angle_threshold")])])

    if ensemble:
        workflow.connect([
            (tckgen, tckmerge, [("track_file", "track_files")]),
            (tckmerge, outputnode, [("track_file", "tck")])
        ])
    else:
        workflow.connect([(tckgen, outputnode, [("track_file", "tck")])])

    return workflow
