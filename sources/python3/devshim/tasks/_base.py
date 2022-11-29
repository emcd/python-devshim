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
from invoke import Collection as TaskCollection, call

from ..base import execute_external
from ..data import paths, project_name
from ..environments import derive_venv_variables
from ..project import discover_version as discover_project_version
# pylint: enable=unused-import


def task( # pylint: disable=too-complex
    title = '',
    task_nomargs = None,
    version_expansion = '',
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
        if version_expansion:
            invocable.__doc__ = '\n\n'.join( (
                invocable.__doc__,
                "If version is 'ALL', "
                f"then the task affects all {version_expansion}." ) )

        # nosemgrep: scm-modules.semgrep-rules.python.lang.maintainability.useless-inner-function
        @wraps( invocable )
        def invoker( context, *posargs, **nomargs ): # pylint: disable=unused-argument
            ''' Handles assorted banalities. '''
            if version_expansion:
                from ..platforms import calculate_python_versions
                versions = calculate_python_versions(
                    nomargs.get( 'version' ) )
            else: versions = ( None, )
            for version in versions:
                if title: render_boxed_title( title, supplement = version )
                re_posargs, re_nomargs = _replace_arguments(
                    invocable, posargs, nomargs,
                    dict( version = version ) )
                _invoke_task_invocable( invocable, re_posargs, re_nomargs )

        return Task( invoker, **( task_nomargs or { } ) )

    return decorator


def invoke_task( task_, *posargs, **nomargs ):
    ''' Invokes task with context. '''
    # Invoke with fake context until we remove dependency on Invoke.
    from invoke import Context
    return task_( Context( ), *posargs, **nomargs )


def _replace_arguments( invocable, posargs, nomargs, replacements ):
    from inspect import signature as scan_signature
    binder = scan_signature( invocable ).bind( *posargs, **nomargs )
    binder.arguments.update( replacements )
    binder.apply_defaults( )
    return binder.args, binder.kwargs


def _invoke_task_invocable( invocable, posargs, nomargs ):
    from invoke import Exit
    allowable_exceptions = _calculate_allowable_exceptions( ) # TODO? Cache.
    try: invocable( *posargs, **nomargs )
    except allowable_exceptions: raise # pylint: disable=catching-non-exception,try-except-raise
    except SystemExit as exc: raise Exit( code = exc.code ) from exc
    except BaseException as exc: raise Exit( message = str( exc ) ) from exc


def _calculate_allowable_exceptions( ):
    import invoke.exceptions
    return tuple(
        attribute for attribute in vars( invoke.exceptions ).values( )
        if isinstance( attribute, BaseException ) )
