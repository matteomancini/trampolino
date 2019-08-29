# -*- coding: utf-8 -*-

"""Console script for trampolino."""
import sys
import os.path
import click
from importlib import import_module
import nipype.pipeline.engine as pe
from nipype.interfaces import utility as util
from nipype.interfaces.io import DataSink


@click.group(chain=True)
@click.option('-w', '--working_dir', type=str)
@click.option('-n', '--name', type=str)
@click.pass_context
def cli(ctx, working_dir, name):
    if working_dir is None:
        ctx.obj['wdir'] = os.path.abspath('.')
    else:
        ctx.obj['wdir'] = os.path.abspath(working_dir)
    if name is None:
        ctx.obj['name'] = 'trampolino'
    else:
        ctx.obj['name'] = name
    datasink = pe.Node(DataSink(base_directory=ctx.obj['wdir'],
                                container=ctx.obj['name']),
                                name="datasink")
    wf = pe.Workflow(name='meta', base_dir=working_dir)
    wf.add_nodes([datasink])
    ctx.obj['workflow'] = wf
    ctx.obj['results'] = datasink


@cli.command('recon')
@click.argument('workflow', required=True)
@click.option('-i', '--in_file', type=str)
@click.option('-v', '--bvec', type=str)
@click.option('-b', '--bval', type=str)
@click.option('-a', '--anat', type=str)
@click.pass_context
def dw_recon(ctx, workflow, in_file, bvec, bval, anat):
    try:
        wf_mod = import_module('workflows.'+workflow)
    except ImportError as err:
        click.echo(workflow+' is not a valid workflow.')
        sys.exit(1)
    wf = ctx.obj['workflow']
    wf_sub = wf_mod.create_pipeline(name='recon')
    wf_sub.inputs.inputnode.dwi = in_file
    wf_sub.inputs.inputnode.bvecs = bvec
    wf_sub.inputs.inputnode.bvals = bval
    wf.add_nodes([wf_sub])
    wf.connect([(wf_sub, ctx.obj['results'], [
        ("outputnode.odf","@odf"),
        ("outputnode.seed","@seed")])])
    ctx.obj['recon'] = wf_sub
    return workflow


@cli.command('track')
@click.argument('workflow', required=True)
@click.option('-o', '--odf', type=str)
@click.option('-s', '--seed', type=str)
@click.option('--angle', type=str)
@click.pass_context
def odf_track(ctx, workflow, odf, seed, angle):
    try:
        wf_mod = import_module('workflows.'+workflow)
    except ImportError as err:
        click.echo(workflow+' is not a valid workflow.')
        sys.exit(1)
    wf_sub = wf_mod.create_pipeline(name='tck')
    param = pe.Node(
        interface=util.IdentityInterface(fields=["angle"]),
        name="param_node")
    if angle is not None:
        angle_thres = angle.split(',')
        angle_thres = [float(a) for a in angle_thres if a.isdigit()]
        param.iterables = ('angle', angle_thres)
    wf = ctx.obj['workflow']
    if 'recon' not in ctx.obj:
        wf_sub.inputs.inputnode.odf = odf
        wf_sub.inputs.inputnode.seed = seed
        wf.add_nodes([wf_sub])
    else:
        wf.add_nodes([wf_sub])
        wf.connect([(ctx.obj['recon'], wf_sub, [("outputnode.odf", "inputnode.odf"),
                                                ("outputnode.seed", "inputnode.seed")])])
    wf.connect([(param, wf_sub, [("angle", "inputnode.angle")]),
                (wf_sub, ctx.obj['results'], [("outputnode.tck", "@tck")])])
    ctx.obj['track'] = wf_sub
    return workflow


@cli.command('filter')
@click.argument('workflow', required=True)
@click.option('-t', '--tck', type=str)
@click.option('-o', '--odf', type=str)
@click.pass_context
def tck_filter(ctx, workflow, tck, odf):
    try:
        wf_mod = import_module('workflows.'+workflow)
    except ImportError as err:
        click.echo(workflow+' is not a valid workflow.')
        sys.exit(1)
    wf_sub = wf_mod.create_pipeline(name='tck_post')
    wf = ctx.obj['workflow']
    if 'track' not in ctx.obj:
        wf_sub.inputs.inputnode.tck = tck
        wf_sub.inputs.inputnode.odf = odf
        wf.add_nodes([wf_sub])
    else:
        wf = ctx.obj['workflow']
        wf.add_nodes([wf_sub])
        wf.connect([(ctx.obj['track'], wf_sub, [("outputnode.tck", "inputnode.tck"),
                                                ("inputnode.odf", "inputnode.odf")])])
    wf.connect([(wf_sub, ctx.obj['results'], [("outputnode.tck_post", "@tck_post")])])
    return workflow


@cli.resultcallback()
def process_result(steps, working_dir, name):
    for n, s in enumerate(steps):
        click.echo('Step {}: {}'.format(n+1, s))
    ctx = click.get_current_context()
    wf = ctx.obj['workflow']
    wf.write_graph(graph2use='colored')
    click.echo('Workflow graph generated.')
    click.echo('Workflow about to be executed. Fasten your seatbelt!')
    wf.run()


if __name__ == "__main__":
    sys.exit(cli(obj={}))
