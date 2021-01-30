from nipype.interfaces import utility as util
from nipype.pipeline import engine as pe
from .interfaces import nibabel as nba
import os.path


def create_pipeline(name="tck2trk", opt=""):

    parameters = {}

    inputnode = pe.Node(
        interface=util.IdentityInterface(fields=["tck", "ref"]),
        name="inputnode")

    if opt is not None:
        opt_list = opt.split(',')
        for o in opt_list:
            try:
                [key, value] = o.split(':')
                parameters[key] = value
            except ValueError:
                print(o+': irregular format, skipping')

    conversion = pe.Node(nba.conversion.Tck2Trk(), name='tck2trk')

    output_fields = ["trk"]
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=output_fields),
        name="outputnode")

    workflow = pe.Workflow(name=name)
    workflow.base_output_dir = name

    workflow.connect([
        (inputnode, conversion, [("tck", "input_tck"),
                                 ("ref", "input_ref")])
    ])

    workflow.connect([
        (conversion, outputnode, [("output_trk", "trk")])
    ])

    return workflow
