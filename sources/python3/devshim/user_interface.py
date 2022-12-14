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


''' Provides user interface for development support activity. '''


from . import base as __


def render_boxed_title( title, supplement = None ):
    ''' Renders box around title to diagnostic stream. '''
    if None is supplement: specific_title = title
    else: specific_title = f"{title} ({supplement})"
    __.eprint( format_boxed_title( specific_title ) )


def format_boxed_title( title ):
    ''' Formats box around title as string. '''
    columns_count = int( __.current_process_environment.get( 'COLUMNS', 79 ) )
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
    from .data import paths
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
    from os import name as os_name
    if 'posix' == os_name: return __.current_process_environment[ 'SHELL' ]
    if 'nt' == os_name: return __.current_process_environment[ 'COMSPEC' ]
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
