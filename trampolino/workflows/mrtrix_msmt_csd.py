from nipype.interfaces import utility as util
from nipype.pipeline import engine as pe
from nipype.interfaces import mrtrix3 as mrtrix3


def create_pipeline(name="dwi"):

    inputnode = pe.Node(
        interface=util.IdentityInterface(fields=["dwi", "bvecs", "bvals"]),
        name="inputnode")

    mrconvert = pe.Node(interface=mrtrix3.MRConvert(), name='convert')

    bias_correct = pe.Node(interface=mrtrix3.DWIBiasCorrect(), name='bias_correct')
    bias_correct.inputs.out_file = 'dwi_bias_corrected.mif'
    bias_correct.inputs.use_ants = True

    mask = pe.Node(interface=mrtrix3.BrainMask(), name='dwi_mask')

    resp = pe.Node(interface=mrtrix3.ResponseSD(), name='response')
    resp.inputs.algorithm = 'dhollander'
    resp.inputs.gm_file = 'gm.txt'
    resp.inputs.csf_file = 'csf.txt'

    dwi2fod = pe.Node(interface=mrtrix3.EstimateFOD(), name='FOD')
    dwi2fod.inputs.algorithm = 'msmt_csd'
    dwi2fod.inputs.gm_odf = 'gm.mif'
    dwi2fod.inputs.csf_odf = 'csf.mif'

    workflow = pe.Workflow(name=name)
    workflow.base_output_dir = name

    workflow.connect([(inputnode, mrconvert, [("bvecs", "in_bvec"),
                                              ("bvals", "in_bval")])])

    workflow.connect([
        (inputnode, mrconvert, [['dwi', 'in_file']]),
        (mrconvert, bias_correct, [['out_file', 'in_file']]),
        (bias_correct, mask, [['out_file', 'in_file']]),
        (bias_correct, resp, [['out_file', 'in_file']]),
        (bias_correct, dwi2fod, [['out_file', 'in_file']]),
        (mask, dwi2fod, [['out_file', 'mask_file']])
    ])

    workflow.connect([(resp, dwi2fod, [("wm_file", "wm_txt"),
                                       ("gm_file", "gm_txt"),
                                       ("csf_file", "csf_txt")])])


    output_fields = ["odf", "seed"]
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=output_fields),
        name="outputnode")

    workflow.connect([
        (dwi2fod, outputnode, [("wm_odf", "odf")]),
        (mask, outputnode, [("out_file", "seed")])
    ])

    return workflow
