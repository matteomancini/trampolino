# -*- coding: utf-8 -*-

"""Console script for trampolino."""
import sys
import os.path
import click
from importlib import import_module
import nipype.pipeline.engine as pe
from nipype.interfaces.io import DataSink


@click.group(chain=True)
@click.option('-w', '--working_dir', type=str)
@click.option('-n ', '--name', type=str)
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
@click.pass_context
def odf_track(ctx, workflow, odf, seed):
    try:
        wf_mod = import_module('workflows.'+workflow)
    except ImportError as err:
        click.echo(workflow+' is not a valid workflow.')
        sys.exit(1)
    wf_sub = wf_mod.create_pipeline(name='tck')
    if ctx.obj['workflow'] is None:
        wf = pe.workflow(name='meta')
        wf_sub.inputs.inputnode.odf = odf
        wf_sub.inputs.inputnode.seed = seed
        wf.add_nodes([wf_sub])
    else:
        wf = ctx.obj['workflow']
        wf.add_nodes([wf_sub])
        wf.connect([(ctx.obj['recon'], wf_sub, [("outputnode.odf", "inputnode.odf"),
                                                ("outputnode.seed", "inputnode.seed")])])
    wf.connect([(wf_sub, ctx.obj['results'], [("outputnode.tck", "@tck")])])
    return workflow


@cli.command('filter')
@click.argument('workflow', required=True)
@click.option('-t', '--tck', type=str)
@click.pass_context
def tck_filter(ctx, workflow, tck):
    try:
        wf_mod = import_module('workflows.'+workflow)
    except ImportError as err:
        click.echo(workflow+' is not a valid workflow.')
        sys.exit(1)
    click.echo(workflow)
    wf_mod = import_module('workflows.' + workflow)
    wf_sub = wf_mod.create_pipeline(name='post')
#    wf_sub.inputs.inputnode.tck = ctx.obj['tck']
    wf_tck = ctx.obj['workflow']
    wf = pe.Workflow(name='filter')
    wf.connect([(wf_sub, ctx.obj['results'], [("outputnode.tck_post", "@tck_post")])])
    return workflow


@cli.resultcallback()
def process_result(steps, working_dir, name):
    for n,s in enumerate(steps):
        click.echo('Step {}: {}'.format(n+1, s))
    ctx = click.get_current_context()
    wf = ctx.obj['workflow']
    wf.write_graph(graph2use='hierarchical')
    click.echo('Workflow graph generated.')
    click.echo('Workflow about to be executed. Fasten your seatbelt!')
    wf.run()


if __name__ == "__main__":
    sys.exit(cli(obj={}))
