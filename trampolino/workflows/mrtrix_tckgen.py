from nipype.interfaces import utility as util
from nipype.pipeline import engine as pe
from .interfaces import mrtrix3 as mrtrix3
import os.path


def create_pipeline(name="tckgen", opt="", ensemble=""):

    parameters = {'nos': 5000,
                  'include': None,
                  'exclude': None}

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
        tckgen = pe.MapNode(mrtrix3.Tractography(),
                         name='track', iterfield=ensemble)
    else:
        tckgen = pe.Node(mrtrix3.Tractography(),
                         name='track')
    tckgen.inputs.select = int(parameters['nos'])
    if parameters['include'] is not None:
        tckgen.inputs.roi_incl = os.path.abspath(parameters['include'])

    if parameters['exclude'] is not None:
        tckgen.inputs.roi_excl = os.path.abspath(parameters['exclude'])

    tckmerge = pe.Node(interface=mrtrix3.TckEdit(), name="merge")

    output_fields = ["tck"]
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=output_fields),
        name="outputnode")

    workflow = pe.Workflow(name=name)
    workflow.base_output_dir = name

    workflow.connect([(inputnode, tckgen, [("odf", "in_file"),
                                           ("seed", "seed_image"),
                                           ("algorithm", "algorithm"),
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
