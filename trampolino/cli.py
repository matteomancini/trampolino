# -*- coding: utf-8 -*-

"""Console script for trampolino."""
import sys
import os
import click
from importlib import import_module
import nipype.pipeline.engine as pe
from nipype.interfaces import utility as util
from nipype.interfaces.io import DataSink
from .get_example_data import grab_data
from .utils import get_parent


@click.group(chain=True)
@click.option('-w', '--working_dir', type=click.Path(exists=True, resolve_path=True),
              help='Working directory.')
@click.option('-n', '--name', type=str, help='Experiment name.')
@click.option('-r', '--results', type=str, help='Results directory.')
@click.option('-f', '--force', is_flag=True,
              help="""Forces following commands by downloading example data [~180MB] 
              and calculating required inputs.""")
@click.pass_context
def cli(ctx, working_dir, name, results, force):
    if not ctx.obj:
        ctx.obj = {}
    if not working_dir:
        ctx.obj['wdir'] = os.path.abspath('.')
    else:
        ctx.obj['wdir'] = click.format_filename(working_dir)
    if not results:
        ctx.obj['output'] = 'trampolino'
    else:
        ctx.obj['output'] = results
    datasink = pe.Node(DataSink(base_directory=ctx.obj['wdir'],
                                container=ctx.obj['output']),
                                name="datasink")
    if not name:
        name = 'meta'
    if force:
        ctx.obj['force'] = True
    else:
        ctx.obj['force'] = False
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

    Available workflows: mrtrix_msmt_csd, dtk_dtirecon, dsi_rec"""

    try:
        wf_mod = import_module('.workflows.' + workflow, package='trampolino')
    except SystemError:
        wf_mod = import_module('workflows.' + workflow)
    except ImportError as err:
        click.echo(workflow + ' is not a valid workflow.')
        sys.exit(1)
    wf = ctx.obj['workflow']
    wf_sub = wf_mod.create_pipeline(name='recon', opt=opt)
    if not in_file or not bvec or not bval:
        click.echo("No DWI data provided.")
        if ctx.obj['force']:
            click.echo("Downloading example data and initializing reconstruction.")
            dwi, bval, bvec = grab_data(ctx.obj['wdir'])
            wf_sub.inputs.inputnode.dwi = dwi
            wf_sub.inputs.inputnode.bvecs = bvec
            wf_sub.inputs.inputnode.bvals = bval
        else:
            click.echo("Aborting.")
            click.echo("Maybe you wanted to use --force? (\"Use the --force, Luke!\")")
            sys.exit(0)

    else:
        wf_sub.inputs.inputnode.dwi = click.format_filename(in_file)
        wf_sub.inputs.inputnode.bvecs = click.format_filename(bvec)
        wf_sub.inputs.inputnode.bvals = click.format_filename(bval)
    if anat:
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
@click.option('--min_length', type=str, help='Minimum streamline length(s).')
@click.option('--ensemble', type=str,
              help='Ensemble over one parameter (algorithm, angle, min_length).')
@click.option('--opt', type=str, help='Workflow-specific optional arguments.')
@click.pass_context
def odf_track(ctx, workflow, odf, seed, algorithm, angle, angle_range, min_length, ensemble, opt):
    """Reconstructs the streamlines.

    Available workflows: mrtrix_tckgen, dtk_dtitracker, dsi_trk"""

    try:
        wf_mod = import_module('.workflows.' + workflow, package='trampolino')
    except SystemError:
        wf_mod = import_module('workflows.' + workflow)
    except ImportError as err:
        click.echo(workflow + ' is not a valid workflow.')
        sys.exit(1)
    param = pe.Node(
        interface=util.IdentityInterface(fields=["angle", "algorithm", "min_length"]),
        name="param_node")
    param_dict = {}
    if angle or algorithm or min_length:
        param.iterables = []
    if angle:
        angles = angle.split(',')
        param_dict['angle'] = [int(a) for a in angles if a.isdigit()]
        if angle_range:
            param_dict['angle'] = range(param_dict['angle'][0], param_dict['angle'][-1])
        param.iterables.append(('angle', param_dict['angle']))
    if algorithm:
        param_dict['algorithm'] = algorithm.split(',')
        param.iterables.append(('algorithm', param_dict['algorithm']))
    if min_length:
        lengths = min_length.split(',')
        param_dict['min_length'] = [int(l) for l in lengths if l.isdigit()]
        param.iterables.append(('min_length', param_dict['min_length']))
    wf_sub = wf_mod.create_pipeline(name='tck', opt=opt, ensemble=ensemble)
    if ensemble:
        param.iterables.remove((ensemble, param_dict[ensemble]))
        setattr(wf_sub.inputs.inputnode, ensemble, param_dict[ensemble])
    wf = ctx.obj['workflow']
    if seed:
        wf_sub.inputs.inputnode.seed = click.format_filename(seed)
    if 'recon' not in ctx.obj:
        if odf:
            wf_sub.inputs.inputnode.odf = click.format_filename(odf)
            wf.add_nodes([wf_sub])
        else:
            click.echo("No odf provided.")

            if ctx.obj['force']:
                ctx.invoke(dw_recon, workflow=get_parent(workflow))
                wf.connect([(ctx.obj['recon'], wf_sub, [("outputnode.odf", "inputnode.odf")])])
                if not seed:
                    wf.connect([(ctx.obj['recon'], wf_sub, [("outputnode.seed", "inputnode.seed")])])
            else:
                click.echo("Aborting.")
                click.echo("Maybe you wanted to use --force? (\"Use the --force, Luke!\")")
                sys.exit(0)

    else:
        wf.add_nodes([wf_sub])
        wf.connect([(ctx.obj['recon'], wf_sub, [("outputnode.odf", "inputnode.odf")])])
        if not seed:
            wf.connect([(ctx.obj['recon'], wf_sub, [("outputnode.seed", "inputnode.seed")])])
    if param.iterables:
        for p in param.iterables:
            wf.connect([(param, wf_sub, [(p[0], "inputnode." + p[0])])])
    wf.connect([(wf_sub, ctx.obj['results'], [("outputnode.tck", "@tck")])])
    ctx.obj['track'] = wf_sub
    ctx.obj['param'] = param
    return workflow


@cli.command('filter')
@click.argument('workflow', required=True)
@click.option('-t', '--tck', type=click.Path(exists=True, resolve_path=True),
              help='Reconstructed streamlines.')
@click.option('-o', '--odf', type=click.Path(exists=True, resolve_path=True),
              help='Estimated fiber orientation distribution.')
@click.option('--opt', type=str, help='Workflow-specific optional arguments.')
@click.pass_context
def tck_filter(ctx, workflow, tck, odf, opt):
    """Filters the tracking result.

    Available workflows: mrtrix_tcksift, dtk_spline"""

    try:
        wf_mod = import_module('.workflows.' + workflow, package='trampolino')
    except SystemError:
        wf_mod = import_module('workflows.' + workflow)
    except ImportError as err:
        click.echo(workflow + ' is not a valid workflow.')
        sys.exit(1)
    wf_sub = wf_mod.create_pipeline(name='tck_post', opt=opt)
    wf = ctx.obj['workflow']
    if 'track' not in ctx.obj:
        if tck and odf:
            wf_sub.inputs.inputnode.tck = click.format_filename(tck)
            wf_sub.inputs.inputnode.odf = click.format_filename(odf)
            wf.add_nodes([wf_sub])
        else:
            click.echo("No tck provided.")

            if ctx.obj['force']:
                ctx.invoke(odf_track, workflow=get_parent(workflow))
                wf.connect([(ctx.obj['track'], wf_sub, [("outputnode.tck", "inputnode.tck")]),
                    (ctx.obj['track'], wf_sub, [("inputnode.odf", "inputnode.odf")])])

            else:
                click.echo("Aborting.")
                click.echo("Maybe you wanted to use --force? (\"Use the --force, Luke!\")")
                sys.exit(0)
    else:
        wf.add_nodes([wf_sub])
        wf.connect([(ctx.obj['track'], wf_sub, [("outputnode.tck", "inputnode.tck")]),
                    (ctx.obj['track'], wf_sub, [("inputnode.odf", "inputnode.odf")])])
    wf.connect([(wf_sub, ctx.obj['results'], [("outputnode.tck_post", "@tck_post")])])
    return workflow

@cli.command('convert')
@click.argument('workflow', required=True)
@click.option('-t', '--tck', type=click.Path(exists=True, resolve_path=True),
              help='Reconstructed streamlines.')
@click.option('-r', '--ref', type=click.Path(exists=True, resolve_path=True),
              help='Estimated fiber orientation distribution.')
@click.option('--opt', type=str, help='Workflow-specific optional arguments.')
@click.pass_context
def tck_convert(ctx, workflow, tck, ref, opt):
    """Convert tractograms.

    Available workflows: tck2tr, trk2tck"""

    try:
        wf_mod = import_module('.workflows.' + workflow, package='trampolino')
    except SystemError:
        wf_mod = import_module('workflows.' + workflow)
    except ImportError as err:
        click.echo(workflow + ' is not a valid workflow.')
        sys.exit(1)
    wf_sub = wf_mod.create_pipeline(name='tck_convert', opt=opt)
    wf = ctx.obj['workflow']
    if ref:
        wf_sub.inputs.inputnode.ref = click.format_filename(ref)
    if 'track' not in ctx.obj:
        wf_sub.inputs.inputnode.tck = click.format_filename(tck)
        wf.add_nodes([wf_sub])
    else:
        wf.add_nodes([wf_sub])
        wf.connect([(ctx.obj['track'], wf_sub, [("outputnode.tck", "inputnode.tck")])])
    wf.connect([(wf_sub, ctx.obj['results'], [("outputnode.trk", "@trk")])])
    return workflow

@cli.resultcallback()
def process_result(steps, working_dir, name, results, force):
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
