# -*- coding: utf-8 -*-

"""Console script for trampolino."""
import sys
import os.path
import click
from importlib import import_module
import nipype.pipeline.engine as pe
from nipype.interfaces import utility as util
from nipype.interfaces.io import DataSink
from .workflows.interfaces.mrtrix3 import TckEdit


@click.group(chain=True)
@click.option('-w', '--working_dir', type=click.Path(exists=True, resolve_path=True),
              help='Working directory.')
@click.option('-n', '--name', type=str, help='Experiment name.')
@click.option('-r', '--results', type=str, help='Results directory.')
@click.pass_context
def cli(ctx, working_dir, name, results):
    if ctx.obj is None:
        ctx.obj = {}
    if working_dir is None:
        ctx.obj['wdir'] = os.path.abspath('.')
    else:
        ctx.obj['wdir'] = click.format_filename(working_dir)
    if results is None:
        ctx.obj['output'] = 'trampolino'
    else:
        ctx.obj['output'] = results
    datasink = pe.Node(DataSink(base_directory=ctx.obj['wdir'],
                                container=ctx.obj['output']),
                                name="datasink")
    if name is None:
        name = 'meta'
    wf = pe.Workflow(name=name, base_dir=ctx.obj['wdir'])
    wf.add_nodes([datasink])
    ctx.obj['workflow'] = wf
    ctx.obj['results'] = datasink


@cli.command('recon')
@click.argument('workflow', required=True)
@click.option('-i', '--in_file', type=click.Path(exists=True, resolve_path=True),
              help='Input diffusion-weighted data.')
@click.option('-v', '--bvec', type=click.Path(exists=True, resolve_path=True),
              help='Text file containing the b-vectors.')
@click.option('-b', '--bval', type=click.Path(exists=True, resolve_path=True),
              help='Text file containing the b-values.')
@click.option('-a', '--anat', type=click.Path(resolve_path=True),
              help='Optional T1-weighted data.')
@click.option('--opt', type=str, help='Workflow-specific optional arguments.')
@click.pass_context
def dw_recon(ctx, workflow, in_file, bvec, bval, anat, opt):
    """Estimates the fiber orientation distribution.

    Available workflows: mrtrix_msmt_csd"""

    try:
        wf_mod = import_module('.workflows.' + workflow, package='trampolino')
    except ImportError as err:
        click.echo(workflow + ' is not a valid workflow.')
        sys.exit(1)
    wf = ctx.obj['workflow']
    wf_sub = wf_mod.create_pipeline(name='recon', opt=opt)
    wf_sub.inputs.inputnode.dwi = click.format_filename(in_file)
    wf_sub.inputs.inputnode.bvecs = click.format_filename(bvec)
    wf_sub.inputs.inputnode.bvals = click.format_filename(bval)
    if anat is not None:
        wf_sub.inputs.inputnode.t1_dw = click.format_filename(anat)
    wf.add_nodes([wf_sub])
    wf.connect([(wf_sub, ctx.obj['results'], [
        ("outputnode.odf", "@odf"),
        ("outputnode.seed", "@seed")])])
    ctx.obj['recon'] = wf_sub
    return workflow


@cli.command('track')
@click.argument('workflow', required=True)
@click.option('-o', '--odf', type=click.Path(exists=True, resolve_path=True),
              help='Estimated fiber orientation distribution.')
@click.option('-s', '--seed', type=click.Path(exists=True, resolve_path=True),
              help='Sees image for tractography.')
@click.option('--algorithm', type=str, help='Tracking algorithm(s).')
@click.option('--angle', type=str, help='Angular threshold(s).')
@click.option('--angle_range/--angle_values', default=False,
              help='Select a range of angles or the provided values.')
@click.option('--opt', type=str, help='Workflow-specific optional arguments.')
@click.pass_context
def odf_track(ctx, workflow, odf, seed, algorithm, angle, angle_range, opt):
    """Reconstructs the streamlines.

    Available workflows: mrtrix_tckgen"""

    try:
        wf_mod = import_module('.workflows.' + workflow, package='trampolino')
    except ImportError as err:
        click.echo(workflow + ' is not a valid workflow.')
        sys.exit(1)
    wf_sub = wf_mod.create_pipeline(name='tck', opt=opt)
    param = pe.Node(
        interface=util.IdentityInterface(fields=["angle", "algorithm"]),
        name="param_node")
    if angle is not None or algorithm is not None:
        param.iterables = []
    if angle is not None:
        angle_thres = angle.split(',')
        angle_thres = [int(a) for a in angle_thres if a.isdigit()]
        if angle_range:
            angle_thres = range(angle_thres[0], angle_thres[-1])
        param.iterables.append(('angle', angle_thres))
    if algorithm is not None:
        algs = algorithm.split(',')
        param.iterables.append(('algorithm', algs))
    wf = ctx.obj['workflow']
    if seed is not None:
        wf_sub.inputs.inputnode.seed = click.format_filename(seed)
    if 'recon' not in ctx.obj:
        wf_sub.inputs.inputnode.odf = click.format_filename(odf)
        wf.add_nodes([wf_sub])
    else:
        wf.add_nodes([wf_sub])
        wf.connect([(ctx.obj['recon'], wf_sub, [("outputnode.odf", "inputnode.odf")])])
        if seed is None:
            wf.connect([(ctx.obj['recon'], wf_sub, [("outputnode.seed", "inputnode.seed")])])
    wf.connect([(param, wf_sub, [("angle", "inputnode.angle")]),
                (param, wf_sub, [("algorithm", "inputnode.algorithm")]),
                (wf_sub, ctx.obj['results'], [("outputnode.tck", "@tck")])])
    ctx.obj['track'] = wf_sub
    ctx.obj['param'] = param
    return workflow


@cli.command('filter')
@click.argument('workflow', required=True)
@click.option('-t', '--tck', type=click.Path(exists=True, resolve_path=True),
              help='Reconstructed streamlines.')
@click.option('-o', '--odf', type=click.Path(exists=True, resolve_path=True),
              help='Estimated fiber orientation distribution.')
@click.option('--ensemble/--parallel', default=False,
              help='Allow to combine multiple tracking results.')
@click.pass_context
def tck_filter(ctx, workflow, tck, odf, ensemble):
    """Filters the tracking result.

    Available workflows: mrtrix_tcksift"""

    try:
        wf_mod = import_module('.workflows.' + workflow, package='trampolino')
    except ImportError as err:
        click.echo(workflow + ' is not a valid workflow.')
        sys.exit(1)
    wf_sub = wf_mod.create_pipeline(name='tck_post')
    wf = ctx.obj['workflow']
    if 'track' not in ctx.obj:
        wf_sub.inputs.inputnode.tck = click.format_filename(tck)
        wf_sub.inputs.inputnode.odf = click.format_filename(odf)
        wf.add_nodes([wf_sub])
    else:
        wf = ctx.obj['workflow']
        wf.add_nodes([wf_sub])
        if ensemble:
            tck_merged = pe.JoinNode(interface=TckEdit(), joinsource=ctx.obj['param'],
                                     joinfield=["in_files"], name="merge")
            wf.connect([(ctx.obj['track'], tck_merged, [("outputnode.tck", "in_files")]),
                        (tck_merged, wf_sub, [("out_file", "inputnode.tck")]),
                        (tck_merged, ctx.obj['results'], [("out_file", "@tck_merged")])])
        else:
            wf.connect([(ctx.obj['track'], wf_sub, [("outputnode.tck", "inputnode.tck")])])
        wf.connect([(ctx.obj['track'], wf_sub, [("inputnode.odf", "inputnode.odf")])])
    wf.connect([(wf_sub, ctx.obj['results'], [("outputnode.tck_post", "@tck_post")])])
    return workflow


@cli.resultcallback()
def process_result(steps, working_dir, name, results):
    for n, s in enumerate(steps):
        click.echo('Step {}: {}'.format(n + 1, s))
    ctx = click.get_current_context()
    wf = ctx.obj['workflow']
    wf.write_graph(graph2use='colored')
    click.echo('Workflow graph generated.')
    click.echo('Workflow about to be executed. Fasten your seatbelt!')
    wf.run()


if __name__ == "__main__":
    sys.exit(cli(obj={}))
