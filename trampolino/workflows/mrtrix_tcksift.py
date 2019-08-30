from nipype.interfaces import utility as util
from nipype.pipeline import engine as pe
from .interfaces import mrtrix3 as mrtrix3


def create_pipeline(name="tcksift", opt=""):

    inputnode = pe.Node(
        interface=util.IdentityInterface(fields=["tck", "odf"]),
        name="inputnode")

    tcksift = pe.Node(mrtrix3.TckSIFT(), name='SIFT')

    output_fields = ["tck_post"]
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=output_fields),
        name="outputnode")

    workflow = pe.Workflow(name=name)
    workflow.base_output_dir = name

    workflow.connect([(inputnode, tcksift, [("tck", "in_file"),
                                           ("odf", "in_fod")])])

    workflow.connect([
        (tcksift, outputnode, [("out_file", "tck_post")])
    ])

    return workflow
