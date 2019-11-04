from nipype.interfaces import utility as util
from nipype.pipeline import engine as pe
import nipype.interfaces.diffusion_toolkit as dtk
import os.path


def create_pipeline(name="spline", opt=""):

    parameters = {'step_length': '0.5'}

    inputnode = pe.Node(
        interface=util.IdentityInterface(fields=["tck", "odf"]),
        name="inputnode")

    if opt is not None:
        opt_list = opt.split(',')
        for o in opt_list:
            try:
                [key, value] = o.split(':')
                parameters[key] = value
            except ValueError:
                print(o+': irregular format, skipping')

    spline_filter = pe.Node(dtk.SplineFilter(), name='spline_filt')
    spline_filter.inputs.step_length = float(parameters['step_length'])

    output_fields = ["tck_post"]
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=output_fields),
        name="outputnode")

    workflow = pe.Workflow(name=name)
    workflow.base_output_dir = name

    workflow.connect([
        (inputnode, spline_filter, [("tck", "track_file")])
    ])

    workflow.connect([
        (spline_filter, outputnode, [("smoothed_track_file", "tck_post")])
    ])

    return workflow
