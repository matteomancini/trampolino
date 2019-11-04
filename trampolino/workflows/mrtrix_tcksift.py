from nipype.interfaces import utility as util
from nipype.pipeline import engine as pe
from .interfaces import mrtrix3 as mrtrix3


def create_pipeline(name="tcksift", opt=""):

    parameters = {'term_n': None}

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

    tcksift = pe.Node(mrtrix3.TckSIFT(), name='SIFT')
    if parameters['term_n'] is not None:
        tcksift.inputs.term_number = int(parameters['term_n'])

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
