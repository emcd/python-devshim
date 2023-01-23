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

''' Constants, imports, and utilities for project maintenance tasks. '''


# Common Imports
# pylint: disable=unused-import
from abc import (
    ABCMeta as ABCFactory, abstractmethod as abstract_function,
)

from invoke import Collection as TaskCollection, call
from lockup import reclassify_module

from ..base import execute_external, scribe
from ..data import paths, project_name
from ..environments import derive_venv_variables
from ..project import discover_version as discover_project_version
# pylint: enable=unused-import

from .. import base as __


def project_execute_external(
    command_specification, venv_specification = None, **nomargs
):
    ''' Executes command in subprocess from project directory.

        Sets the process environment according to ``venv_specification``,
        if supplied.

        Raises exception on non-zero exit code. '''
    if None is venv_specification:
        return execute_external(
            command_specification, cwd = paths.project, **nomargs )
    from ..environments import venv_execute_external
    return venv_execute_external(
        command_specification,
        cwd = paths.project,
        venv_specification = venv_specification,
        **nomargs )


def task( # pylint: disable=too-complex
    title = '', *,
    multiplexer = None,
    task_nomargs = None,
):
    ''' Produces decorator for the handling of assorted banalities.

        Banalities include:
        * Rendering a title box.
        * Iterative execution over multiple platform versions. '''
    from functools import wraps
    from ._invoke import Task
    from ..user_interface import render_boxed_title

    def decorator( invocable ):
        ''' Produces invoker for the handling of assorted banalities. '''
        if None is not multiplexer:
            # TODO: Validate argument multiplexer.
            multiplexer.augment_docstring( invocable )

        # nosemgrep: python.lang.maintainability.useless-inner-function
        @wraps( invocable )
        def invoker( context, *posargs, **nomargs ): # pylint: disable=unused-argument
            ''' Handles assorted banalities. '''
            if None is not multiplexer:
                for value, re_posargs, re_nomargs in multiplexer.multiplex(
                    invocable, posargs, nomargs
                ):
                    if title: render_boxed_title( title, supplement = value )
                    _invoke_task_invocable( invocable, re_posargs, re_nomargs )
            else:
                if title: render_boxed_title( title )
                _invoke_task_invocable( invocable, posargs, nomargs )
                return

        return Task( invoker, **( task_nomargs or { } ) )

    return decorator


class ArgumentMultiplexer( metaclass = ABCFactory ):
    ''' Multiplexes values for argument across invocations. '''

    def __init__( self, argument_name, subject ):
        # TODO: Validate arguments.
        self.argument_name = argument_name
        self.subject = subject

    @abstract_function
    def augment_docstring( self, invocable ):
        ''' Augments docstring of invocable to describe multiplexer effect. '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @abstract_function
    def multiplex( self, invocable, posargs, nomargs ):
        ''' Yields adjusted arguments for each multiplexed invocation. '''
        # TODO: Use exception factory.
        raise NotImplementedError


class PythonVersionMultiplexer( ArgumentMultiplexer ):
    ''' Multiplexes Python version argument across invocations. '''

    def __init__( self,
        argument_name = 'version',
        subject = 'declared Python versions',
        enable_default = True,
    ):
        super( ).__init__( argument_name = argument_name, subject = subject )
        self.enable_default = enable_default

    def augment_docstring( self, invocable ):
        # TODO: Validate argument.
        invocable.__doc__ = '\n\n'.join( (
            invocable.__doc__,
            f"If argument {self.argument_name!r} is 'ALL', "
            f"then the task affects all {self.subject}." ) )

    def multiplex( self, invocable, posargs, nomargs ):
        # TODO: Validate arguments.
        from inspect import signature as scan_signature
        binder = scan_signature( invocable ).bind( *posargs, **nomargs )
        binder.apply_defaults( )
        argument = binder.arguments[ self.argument_name ]
        from ..languages.python import language
        if None is argument and self.enable_default:
            versions = ( language.detect_default_descriptor( ).name, )
        elif 'ALL' == argument:
            versions = language.survey_descriptors( ).keys( )
        else: versions = ( language.validate_descriptor( argument ), )
        for version in versions:
            binder.arguments.update( { self.argument_name: version } )
            yield version, binder.args, binder.kwargs


def invoke_task( task_, *posargs, **nomargs ):
    ''' Invokes task with context. '''
    # Invoke with fake context until we remove dependency on Invoke.
    from invoke import Context
    return task_( Context( ), *posargs, **nomargs )


def _invoke_task_invocable( invocable, posargs, nomargs ):
    from subprocess import CalledProcessError as SubprocessFailure # nosec B404
    try: invocable( *posargs, **nomargs )
    except SubprocessFailure as exc:
        excc = type( exc )
        __.scribe.error( f"{excc.__module__}.{excc.__qualname__}: {exc}" )
        raise SystemExit( exc.returncode ) from exc


__.reclassify_module( __name__ )
