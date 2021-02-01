# -*- coding: utf-8 -*-

"""Console script for trampolino."""
import sys
import os
import click
import shutil
import tempfile
import time
from importlib import import_module
from importlib.util import find_spec
import nipype.pipeline.engine as pe
from nipype.interfaces import utility as util
from nipype.interfaces.io import DataSink
from distutils.dir_util import copy_tree
from .utils.get_example_data import grab_data
from .utils.containers import set_inputs


@click.group(chain=True)
@click.option('-w', '--working_dir', type=click.Path(exists=True, resolve_path=True),
              default='.', help='Working directory.')
@click.option('-n', '--name', type=str, default='meta', help='Experiment name.')
@click.option('-r', '--results', type=str, default='trampolino', help='Results directory.')
@click.option('--save', is_flag=True, help='Export workflow as a Python script.')
@click.option('--container', is_flag=True, help='Execute the workflow in a container (it requires docker).')
@click.option('--image', type=str, default='ingmatman/trampolino', help='Use specific container image (requires "--container")')
@click.option('--keep', is_flag=True, help='Keep the container temporary files (requires "--container")')
@click.option('-f', '--force', is_flag=True,
              help="""Forces following commands by downloading example data [~180MB] 
              and calculating required inputs.""")
@click.pass_context
def cli(ctx, working_dir, name, results, save, container, image, keep, force):
    if not ctx.obj:
        ctx.obj = {}

    ctx.obj['save'] = save
    ctx.obj['container'] = container
    ctx.obj['wdir'] = click.format_filename(working_dir)
    ctx.obj['output'] = results
    ctx.obj['force'] = force
    ctx.obj['temp'] = ''
    ctx.obj['container_dir'] = ''

    if not ctx.obj['container']:
        datasink = pe.Node(DataSink(base_directory=ctx.obj['wdir'],
                                    container=ctx.obj['output']),
                                    name="datasink")
        wf = pe.Workflow(name=name, base_dir=ctx.obj['wdir'])
    else:
        if find_spec("docker") is None:
            click.echo('The --container option was specified but the docker package is not installed.')
            sys.exit(1)

        ctx.obj['save'] = True
        ctx.obj['temp'] = tempfile.mkdtemp(dir=ctx.obj['wdir'])
        ctx.obj['container_dir'] = '/tmp'
        datasink = pe.Node(DataSink(base_directory=ctx.obj['container_dir'],
                                    container=os.path.join(ctx.obj['container_dir'], 'output')),
                                    name="datasink")
        wf = pe.Workflow(name=name, base_dir=ctx.obj['temp'])

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

    inputs = []
    if in_file:
        inputs.append(click.format_filename(in_file))
        inputs.append(click.format_filename(bvec))
        inputs.append(click.format_filename(bval))
        if anat:
            inputs.append(click.format_filename(anat))
    else:
        click.echo("No DWI data provided.")
        if ctx.obj['force']:
            click.echo("Downloading example data and initializing reconstruction.")
            inputs = list(grab_data(ctx.obj['wdir']))
        else:
            click.echo("Aborting.")
            click.echo("Maybe you wanted to use --force? (\"Use the --force, Luke!\")")
            sys.exit(0)

    wf_sub.inputs.inputnode.dwi, \
        wf_sub.inputs.inputnode.bvecs,\
        wf_sub.inputs.inputnode.bvals, *anat = \
        set_inputs(ctx.obj['container'], inputs, ctx.obj['container_dir'], ctx.obj['temp'])
    if anat:
        wf_sub.inputs.inputnode.t1_dw = anat[0]

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

    Available workflows: mrtrix_tckgen, dtk_dtitracker, dsi_trk, trekker, tractseg"""

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

    if 'recon' not in ctx.obj:
        if odf:
            inputs = [click.format_filename(odf)]
            if seed:
                inputs.append(click.format_filename(seed))
            wf_sub.inputs.inputnode.odf, \
                *seed = \
                set_inputs(ctx.obj['container'], inputs, ctx.obj['container_dir'], ctx.obj['temp'])
            if seed:
                wf_sub.inputs.inputnode.seed = seed[0]
            wf.add_nodes([wf_sub])
        else:
            click.echo("No odf provided.")

            if ctx.obj['force']:
                ctx.invoke(dw_recon, workflow=wf_mod.get_parent())
                wf.connect([(ctx.obj['recon'], wf_sub, [("outputnode.odf", "inputnode.odf")])])
                wf.connect([(ctx.obj['recon'], wf_sub, [("outputnode.seed", "inputnode.seed")])])
            else:
                click.echo("Aborting.")
                click.echo("Maybe you wanted to use --force? (\"Use the --force, Luke!\")")
                sys.exit(0)

    else:
        wf.add_nodes([wf_sub])
        wf.connect([(ctx.obj['recon'], wf_sub, [("outputnode.odf", "inputnode.odf")])])
        if seed:
            wf_sub.inputs.inputnode.odf = click.format_filename(seed)
        else:
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
        if tck:
            inputs = [click.format_filename(tck)]
            if odf:
                inputs.append(click.format_filename(odf))
            wf_sub.inputs.inputnode.tck, \
                *odf = \
                set_inputs(ctx.obj['container'], inputs, ctx.obj['container_dir'], ctx.obj['temp'])
            if odf:
                wf_sub.inputs.inputnode.odf = odf[0]
            wf.add_nodes([wf_sub])
        else:
            click.echo("No tck provided.")

            if ctx.obj['force']:
                ctx.invoke(odf_track, workflow=wf_mod.get_parent())
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
def process_result(steps, working_dir, name, results, save, container, image, keep, force):
    for n, s in enumerate(steps):
        click.echo('Step {}: {}'.format(n + 1, s))
    ctx = click.get_current_context()
    wf = ctx.obj['workflow']
    wf.write_graph(graph2use='colored')
    click.echo('Workflow graph generated.')
    if ctx.obj['save']:
        wf.export(name+'.py')
    if not ctx.obj['container']:
        click.echo('Workflow about to be executed. Fasten your seatbelt!')
        wf.run()
    else:
        click.echo('Containers enabled, about to go into the cyberspace!')
        docker = import_module('docker')
        shutil.copyfile(name+'.py', os.path.join(ctx.obj['temp'], name+'.py'))
        with open(os.path.join(ctx.obj['temp'], name+'.py'), 'a') as file:
            file.write('\n' + name + '.run()\n')
        client = docker.from_env()
        cmd = 'python3 ' + os.path.join(os.path.join(ctx.obj['container_dir']), name+'.py')
        container_obj = client.containers.run(image, cmd,
                              volumes={ctx.obj['temp']: {'bind': ctx.obj['container_dir'], 'mode': 'rw'}},
                              detach=True)
        status = ''
        while container_obj.status != "exited" and container_obj.status != "dead":
            container_obj.reload()
            if container_obj.status != status:
                status = container_obj.status
                print("The current status of the container is: "+status)
            time.sleep(1)
        with open(os.path.join(ctx.obj['output'], name + "_logs.txt"), "wb") as log_file:
            log_file.write(container_obj.logs())
        copy_tree(os.path.join(ctx.obj['temp'], 'output'), ctx.obj['output'])
        if not keep:
            shutil.rmtree(ctx.obj['temp'])


if __name__ == "__main__":
    sys.exit(cli(obj={}))

