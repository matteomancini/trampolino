from nipype.interfaces import utility as util
from nipype.pipeline import engine as pe
from .interfaces import dsi_studio as dsi
import os.path


def create_pipeline(name="dsi_recon", opt=""):

    parameters = {'param0': 1.25,
                  'method': 4}

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

    dsi_src = pe.Node(dsi.GenSrc(), name='dsi_to_src')

    dsi_rec = pe.Node(dsi.ImageRecon(), name='dsi_recon')
    dsi_rec.inputs.method = int(parameters['method'])
    dsi_rec.inputs.param0 = float(parameters['param0'])

    workflow = pe.Workflow(name=name)
    workflow.base_output_dir = name

    workflow.connect([(inputnode, dsi_src, [('bvecs', 'bvec_file'),
                                           ('bvals', 'bval_file'),
                                           ('dwi', 'in_file')]),
                      (dsi_src, dsi_rec, [('out_file', 'in_file')])])



    output_fields = ["odf", "seed"]
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=output_fields),
        name="outputnode")

    workflow.connect([(dsi_rec, outputnode, [("out_file", "odf")])])

    return workflow
