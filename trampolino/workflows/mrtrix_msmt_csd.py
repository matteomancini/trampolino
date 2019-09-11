from nipype.interfaces import utility as util
from nipype.pipeline import engine as pe
from .interfaces import mrtrix3 as mrtrix3
import os.path


def create_pipeline(name="msmt_csd", opt=""):

    parameters = {'algorithm': 'dhollander',
                  'no_bias': False,
                  'preproc': False,
                  'bthres': False,
                  'mask': 'dwi2mask'}

    inputnode = pe.Node(
        interface=util.IdentityInterface(fields=["dwi", "bvecs", "bvals", "t1_dw"]),
        name="inputnode")

    if opt is not None:
        opt_list = opt.split(',')
        for o in opt_list:
            try:
                [key, value] = o.split(':')
                parameters[key] = value
            except ValueError:
                print(o+': irregular format, skipping')

    mrconvert = pe.Node(interface=mrtrix3.MRConvert(), name='convert')

    bias_correct = pe.Node(interface=mrtrix3.DWIBiasCorrect(), name='bias_correct')
    bias_correct.inputs.out_file = 'dwi_bias_corrected.mif'
    bias_correct.inputs.use_ants = True

    mask = pe.Node(interface=mrtrix3.BrainMask(), name='dwi_mask')

    gen5tt = pe.Node(interface=mrtrix3.Generate5tt(), name='gen5tt')
    gen5tt.inputs.algorithm = 'fsl'
    gen5tt.inputs.out_file = '5tt.mif'

    dwiextract = pe.Node(interface=mrtrix3.DWIExtract(), name='dwiextract')
    dwiextract.inputs.out_file = 'dwi_nobzero.mif'

    bval = pe.Node(name='bval', interface=util.Function(
        input_names=['bval_file', 'thres'], output_names=['bval_list'],
        function=generate_bval_list))

    resp = pe.Node(interface=mrtrix3.ResponseSD(), name='response')
    resp.inputs.algorithm = parameters['algorithm']
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

    if parameters['algorithm'] == 'msmt_5tt':
        workflow.connect([
            (inputnode, gen5tt, [['t1_dw', 'in_file']]),
            (gen5tt, resp, [['out_file', 'mtt_file']])
        ])

    if int(parameters['bthres']) > 0:
        bval.inputs.thres = float(parameters['bthres'])
        workflow.connect([(inputnode, bval, [("bvals", "bval_file")]),
                          (bval, dwiextract, [("bval_list", "shell")])
                          ])

    workflow.connect([
        (inputnode, mrconvert, [['dwi', 'in_file']])])

    if parameters['no_bias'] and parameters['bthres']:
        workflow.connect([
            (mrconvert, dwiextract, [['out_file', 'in_file']]),
            (mrconvert, mask, [['out_file', 'in_file']]),
            (dwiextract, resp, [['out_file', 'in_file']]),
            (dwiextract, dwi2fod, [['out_file', 'in_file']])
        ])
    elif parameters['bthres']:
        workflow.connect([
            (mrconvert, bias_correct, [['out_file', 'in_file']]),
            (bias_correct, dwiextract, [['out_file', 'in_file']]),
            (bias_correct, mask, [['out_file', 'in_file']]),
            (dwiextract, resp, [['out_file', 'in_file']]),
            (dwiextract, dwi2fod, [['out_file', 'in_file']])
        ])
    elif parameters['no_bias']:
        workflow.connect([
            (mrconvert, bias_correct, [['out_file', 'in_file']]),
            (bias_correct, mask, [['out_file', 'in_file']]),
            (bias_correct, resp, [['out_file', 'in_file']]),
            (bias_correct, dwi2fod, [['out_file', 'in_file']])
        ])
    else:
        workflow.connect([
            (mrconvert, mask, [['out_file', 'in_file']]),
            (mrconvert, resp, [['out_file', 'in_file']]),
            (mrconvert, dwi2fod, [['out_file', 'in_file']])
        ])

    if parameters['mask'] == 'dwi2mask':
        workflow.connect([
            (mask, dwi2fod, [['out_file', 'mask_file']])])
    else:
        dwi2fod.inputs.mask_file = os.path.abspath(parameters['mask'])

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


def generate_bval_list(bval_file, thres):

    with open(bval_file) as file:
        bvals = file.read()
    b = bvals.split()
    blist = []
    try:
        blist = [int(float(hb)) for hb in b if float(hb) > thres]
    except ValueError:
        print("Error: the b-value file does not contain numbers.")

    return list(set(blist))
