from nipype.interfaces import utility as util
from nipype.pipeline import engine as pe
from .interfaces import mrtrix3 as mrtrix3


def create_pipeline(name="tckgen"):

    inputnode = pe.Node(
        interface=util.IdentityInterface(fields=["odf", "seed", "angle"]),
        name="inputnode")

    tckgen = pe.Node(mrtrix3.Tractography(), name='track')

    output_fields = ["tck"]
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=output_fields),
        name="outputnode")

    workflow = pe.Workflow(name=name)
    workflow.base_output_dir = name

    workflow.connect([(inputnode, tckgen, [("odf", "in_file"),
                                           ("seed", "seed_image"),
                                           ("angle", "angle")])])

    workflow.connect([
        (tckgen, outputnode, [("out_file", "tck")])
    ])

    return workflow
