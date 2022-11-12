# vim: set filetype=python fileencoding=utf-8:
# -*- coding: utf-8 -*-

#============================================================================#
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License");           #
#  you may not use this file except in compliance with the License.          #
#  You may obtain a copy of the License at                                   #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  Unless required by applicable law or agreed to in writing, software       #
#  distributed under the License is distributed on an "AS IS" BASIS,         #
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#  See the License for the specific language governing permissions and       #
#  limitations under the License.                                            #
#                                                                            #
#============================================================================#


''' Project package management. '''


from lockup import NamespaceClass as _NamespaceClass
class __( metaclass = _NamespaceClass ):

    from shlex import (
        quote as shell_quote,
    )
    from tempfile import NamedTemporaryFile

    from .base import (
        eprint, epprint,
        generate_pip_requirements_text,
        on_tty,
    )

    from lockup import reclassify_module


def install_python_packages( context, context_options, identifier = None ):
    ''' Installs required Python packages into virtual environment. '''
    raw, frozen, unpublished = __.generate_pip_requirements_text(
        identifier = identifier )
    context.run(
        'pip install --upgrade setuptools pip wheel',
        pty = __.on_tty, **context_options )
    if not identifier or not frozen:
        pip_options = [ ]
        if not identifier:
            pip_options.append( '--upgrade' )
            pip_options.append( '--upgrade-strategy eager' )
        execute_pip_with_requirements(
            context, context_options, 'install', raw,
            pip_options = pip_options )
    else:
        pip_options = [ '--require-hashes' ]
        execute_pip_with_requirements(
            context, context_options, 'install', frozen,
            pip_options = pip_options )
    if unpublished:
        execute_pip_with_requirements(
            context, context_options, 'install', unpublished )
    # Pip cannot currently mix editable and digest-bound requirements,
    # so we must install editable packages separately. (As of 2022-02-06.)
    # https://github.com/pypa/pip/issues/4995
    context.run(
        'pip install --editable .', pty = __.on_tty, **context_options )


def execute_pip_with_requirements(
    context, context_options, command, requirements, pip_options = None
):
    ''' Executes a Pip command with requirements. '''
    pip_options = pip_options or ( )
    # Unfortunately, Pip does not support reading requirements from stdin,
    # as of 2022-01-02. To workaround, we need to write and then read
    # a temporary file. More details: https://github.com/pypa/pip/issues/7822
    with __.NamedTemporaryFile( mode = 'w+' ) as requirements_file:
        requirements_file.write( requirements )
        requirements_file.flush( )
        context.run(
            "pip {command} {options} --requirement {requirements_file}".format(
                command = command,
                options = ' '.join( pip_options ),
                requirements_file = __.shell_quote( requirements_file.name ) ),
            pty = __.on_tty, **context_options )


__.reclassify_module( __name__ )
