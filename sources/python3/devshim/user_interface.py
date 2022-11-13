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


''' Provides shell functions to facilitate use of development shim. '''


from lockup import NamespaceClass as _NamespaceClass
class __( metaclass = _NamespaceClass ):

    from types import MappingProxyType as DictionaryProxy

    from lockup import reclassify_module


def render_boxed_title( title, supplement = None ):
    ''' Renders box around title to diagnostic stream. '''
    if None is supplement: specific_title = title
    else: specific_title = f"{title} ({supplement})"
    from .base import eprint
    eprint( format_boxed_title( specific_title ) )


def format_boxed_title( title ):
    ''' Formats box around title as string. '''
    from os import environ as current_process_environment
    columns_count = int( current_process_environment.get( 'COLUMNS', 79 ) )
    icolumns_count = columns_count - 2
    content_template = (
        '\N{BOX DRAWINGS DOUBLE VERTICAL}{fill}'
        '\N{BOX DRAWINGS DOUBLE VERTICAL}' )
    return '\n'.join( (
        '',
        '\N{BOX DRAWINGS DOUBLE DOWN AND RIGHT}{fill}'
        '\N{BOX DRAWINGS DOUBLE DOWN AND LEFT}'.format(
            fill = '\N{BOX DRAWINGS DOUBLE HORIZONTAL}' * icolumns_count ),
        content_template.format( fill = ' ' * icolumns_count ),
        content_template.format( fill = title.center( icolumns_count ) ),
        content_template.format( fill = ' ' * icolumns_count ),
        '\N{BOX DRAWINGS DOUBLE UP AND RIGHT}{fill}'
        '\N{BOX DRAWINGS DOUBLE UP AND LEFT}'.format(
            fill = '\N{BOX DRAWINGS DOUBLE HORIZONTAL}' * icolumns_count ),
        '', ) )


def assert_gpg_tty( ):
    ''' Ensures the the 'GPG_TTY' environment variable is set. '''
    from os import environ as current_process_environment
    if 'GPG_TTY' in current_process_environment: return
    # TODO: Check for cached passphrase as an alternative.
    # TODO: Use 'expire' instead of raising 'invoke.Exit'.
    from invoke import Exit
    raise Exit(
        "ERROR: Environment variable 'GPG_TTY' is not set. "
        "Task cannot prompt for GPG secret key passphrase." )


def generate_cli_functions( shell_name, function_name, with_completions ):
    ''' Generates CLI functions for use of development shim.

        Includes an invocation function and, if available,
        a completion function. '''
    if not shell_name:
        from shellingham import ShellDetectionFailure, detect_shell
        try: shell_name = detect_shell( )[ 0 ]
        except ShellDetectionFailure:
            shell_name = _provide_default_shell_name( )
    from inspect import cleandoc
    from sys import executable as active_python_path
    from .locations import paths
    invocation_code = cleandoc(
        invocation_code_table[ shell_name ].format(
            python_path = active_python_path,
            shim_path = ( paths.project / 'develop.py' ).resolve( ),
            function_name = function_name ) )
    if with_completions and shell_name in completion_code_table:
        completion_code = cleandoc(
            completion_code_table[ shell_name ].format(
                function_name = function_name ) )
    else: completion_code = None
    return '\n\n'.join( filter( None, ( invocation_code, completion_code ) ) )


def _provide_default_shell_name( ):
    ''' Attempt reasonable inference of shell name from environment. '''
    from os import environ as active_process_environment, name as os_name
    if 'posix' == os_name: return active_process_environment[ 'SHELL' ]
    if 'nt' == os_name: return active_process_environment[ 'COMSPEC' ]
    raise NotImplementedError( f"OS {os_name!r} support not available." )


# TODO? Detect when outside of the project directory tree.
invocation_code_table = __.DictionaryProxy( {
    'bash': '''
        function {function_name} {{
            "{python_path}" "{shim_path}" "$@"
        }}''',
    'fish': '''
		function {function_name}
            "{python_path}" "{shim_path}" $argv
        end''',
    'zsh': '''
        function {function_name} {{
            "{python_path}" "{shim_path}" "$@"
        }}''',
} )

completion_code_table = __.DictionaryProxy( {
    # TODO: Implement.
} )

# TODO? direnv configuration snippets to allow devshim to operate
#       in any supported directory.


__.reclassify_module( __name__ )
