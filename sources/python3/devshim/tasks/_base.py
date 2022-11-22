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

''' Constants and utilities for project maintenance tasks. '''


def task(
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
        def invoker( *posargs, **nomargs ):
            ''' Handles assorted banalities. '''
            if version_expansion:
                from ..platforms import calculate_python_versions
                versions = calculate_python_versions(
                    nomargs.get( 'version' ) )
                for version in versions:
                    if title: render_boxed_title( title, supplement = version )
                    re_posargs, re_nomargs = _replace_arguments(
                        invocable, posargs, nomargs,
                        dict( version = version ) )
                    invocable( *re_posargs, **re_nomargs )
            else:
                if title: render_boxed_title( title )
                invocable( *posargs, **nomargs )

        return Task( invoker, **( task_nomargs or { } ) )

    return decorator


def _replace_arguments( invocable, posargs, nomargs, replacements ):
    from inspect import signature as scan_signature
    binder = scan_signature( invocable ).bind( *posargs, **nomargs )
    binder.arguments.update( replacements )
    binder.apply_defaults( )
    return binder.args, binder.kwargs