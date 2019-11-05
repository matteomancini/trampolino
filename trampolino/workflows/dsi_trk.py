from nipype.interfaces import utility as util
from nipype.pipeline import engine as pe
from .interfaces import dsi_studio as dsi
import nipype.interfaces.diffusion_toolkit as dtk
from nipype.algorithms.misc import Gunzip
import os.path


def create_pipeline(name="dsi_track", opt="", ensemble=""):
    parameters = {'nos': 5000}

    ensemble_dict = {'angle': 'angle_thres',
                     'min_length': 'min_length'}

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
                print(o + ': irregular format, skipping')

    if ensemble:
        tckgen = pe.MapNode(dsi.FiberTrack(),
                            name='track', iterfield=ensemble_dict[ensemble])
        gunzip = pe.MapNode(interface=Gunzip(), name="gunzip",
                            iterfield='in_file')
    else:
        tckgen = pe.Node(dsi.FiberTrack(), name='track')
        gunzip = pe.Node(interface=Gunzip(), name="gunzip")
    tckgen.inputs.nos = int(parameters['nos'])

    tckmerge = pe.Node(interface=dtk.TrackMerge(), name="merge")

    output_fields = ["tck"]
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=output_fields),
        name="outputnode")

    workflow = pe.Workflow(name=name)
    workflow.base_output_dir = name

    workflow.connect([(inputnode, tckgen, [("odf", "in_file"),
                                           ("angle", "angle_thres"),
                                           ("min_length", "min_length")]),
                      (tckgen, gunzip, [("out_file", "in_file")])])

    if inputnode.inputs.seed:
        workflow.connect([(inputnode, tckgen, [("seed", "seed_image")])])

    if ensemble:
        workflow.connect([
            (gunzip, tckmerge, [("out_file", "track_files")]),
            (tckmerge, outputnode, [("track_file", "tck")])
        ])
    else:
        workflow.connect([(gunzip, outputnode, [("out_file", "tck")])])

    return workflow
