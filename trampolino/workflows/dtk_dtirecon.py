from nipype.interfaces import utility as util
from nipype.pipeline import engine as pe
import nipype.interfaces.diffusion_toolkit as dtk
import os.path


def create_pipeline(name="dtirecon", opt=""):

    parameters = {'b0_threshold': 0}

    inputnode = pe.Node(
        interface=util.IdentityInterface(fields=["dwi", "bvecs", "bvals"]),
        name="inputnode")

    if opt is not None:
        opt_list = opt.split(',')
        for o in opt_list:
            try:
                [key, value] = o.split(':')
                parameters[key] = value
            except ValueError:
                print(o+': irregular format, skipping')

    dtirec = pe.Node(dtk.DTIRecon(), name='tensorfit')
    if parameters['b0_threshold']:
        dtirec.inputs.b0_threshold = parameters['b0_threshold']

    workflow = pe.Workflow(name=name)
    workflow.base_output_dir = name

    workflow.connect([(inputnode, dtirec, [('bvecs', 'bvecs'),
                                           ('bvals', 'bvals'),
                                           ('dwi', 'DWI')])])

    output_fields = ["odf", "seed"]
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=output_fields),
        name="outputnode")

    workflow.connect([(dtirec, outputnode, [("tensor", "odf"),
                                          ("FA", "seed")])])

    return workflow
