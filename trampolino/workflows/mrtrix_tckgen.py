from nipype.interfaces import utility as util
from nipype.pipeline import engine as pe
from .interfaces import mrtrix3 as mrtrix3


def create_pipeline(name="tckgen", opt=""):

    inputnode = pe.Node(
        interface=util.IdentityInterface(fields=["odf", "seed", "angle", "algorithm"]),
        name="inputnode")

    tckgen = pe.Node(mrtrix3.Tractography(), name='track')
    if opt is not None:
        opt_list = opt.split(',')
        tckgen.inputs.select = int(opt_list[0])
        if len(opt_list) > 1:
            tckgen.inputs.roi_incl = opt_list[1]

    output_fields = ["tck"]
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=output_fields),
        name="outputnode")

    workflow = pe.Workflow(name=name)
    workflow.base_output_dir = name

    workflow.connect([(inputnode, tckgen, [("odf", "in_file"),
                                           ("seed", "seed_image"),
                                           ("algorithm", "algorithm"),
                                           ("angle", "angle")])])

    workflow.connect([
        (tckgen, outputnode, [("out_file", "tck")])
    ])

    return workflow
