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


def enhance_ultimate_scribe( ):
    ''' Enhances root logger as desired. '''
    from logging import getLogger as acquire_scribe
    from sys import stderr
    from rich.console import Console
    from rich.logging import RichHandler
    from .base import narration_target
    scribe = acquire_scribe( )
    for handler in scribe.handlers: scribe.removeHandler( handler )
    # TODO: Alter log format.
    scribe.addHandler( RichHandler(
        console = Console( stderr = stderr == narration_target ),
        rich_tracebacks = True,
        show_time = False ) )
    scribe.debug(
        "Rich logging enabled. "
        "Toto, I've a feeling we're not in Kansas anymore." )


def render_boxed_title( title, supplement = None ):
    ''' Renders box around title to diagnostic stream. '''
    if None is supplement: specific_title = title
    else: specific_title = f"{title} ({supplement})"
    __.eprint( format_boxed_title( specific_title ) )


def format_boxed_title( title, gravity = 2 ):
    ''' Formats box around title as string. '''
    columns_count = int( __.current_process_environment.get( 'COLUMNS', 79 ) )
    icolumns_count = columns_count - 2
    table = _acquire_rectangle_construction_characters( gravity )
    content_template = '{vertical}{fill}{vertical}'
    return '\n'.join( (
        '',
        '{suprasinistral}{fill}{supradextral}'.format(
            fill = table[ 'horizontal' ] * icolumns_count, **table ),
        content_template.format( fill = ' ' * icolumns_count, **table ),
        content_template.format(
            fill = title.center( icolumns_count ), **table ),
        content_template.format( fill = ' ' * icolumns_count, **table ),
        '{infrasinistral}{fill}{infradextral}'.format(
            fill = table[ 'horizontal' ] * icolumns_count, **table ),
        '', ) )


_ascii_rectangular_elements_single = __.DictionaryProxy( dict(
    horizontal      = '-',
    vertical        = '|',
    infrasinistral  = '+',
    infradextral    = '+',
    suprasinistral  = '+',
    supradextral    = '+',
) )
_ascii_rectangular_elements_double = __.DictionaryProxy( dict(
    horizontal      = '=',
    vertical        = '|',
    infrasinistral  = '+',
    infradextral    = '+',
    suprasinistral  = '+',
    supradextral    = '+',
) )
_unicode_rectangular_elements_single = __.DictionaryProxy( dict(
    horizontal      = '\N{BOX DRAWINGS LIGHT HORIZONTAL}',
    vertical        = '\N{BOX DRAWINGS LIGHT VERTICAL}',
    infrasinistral  = '\N{BOX DRAWINGS LIGHT UP AND RIGHT}',
    infradextral    = '\N{BOX DRAWINGS LIGHT UP AND LEFT}',
    suprasinistral  = '\N{BOX DRAWINGS LIGHT DOWN AND RIGHT}',
    supradextral    = '\N{BOX DRAWINGS LIGHT DOWN AND LEFT}',
) )
_unicode_rectangular_elements_double = __.DictionaryProxy( dict(
    horizontal      = '\N{BOX DRAWINGS DOUBLE HORIZONTAL}',
    vertical        = '\N{BOX DRAWINGS DOUBLE VERTICAL}',
    infrasinistral  = '\N{BOX DRAWINGS DOUBLE UP AND RIGHT}',
    infradextral    = '\N{BOX DRAWINGS DOUBLE UP AND LEFT}',
    suprasinistral  = '\N{BOX DRAWINGS DOUBLE DOWN AND RIGHT}',
    supradextral    = '\N{BOX DRAWINGS DOUBLE DOWN AND LEFT}',
) )


def _acquire_rectangle_construction_characters( gravity ):
    ''' Returns dictionary of characters for rectangle construction. '''
    # TODO: Validate gravity argument. Should maybe be an enumeration.
    from os import name as os_class
    # Detecting whether a terminal can support and properly render Unicode code
    # points that have been encoded as UTF-8 is a mess on Windows. For example,
    # see these Winpty issues:
    #   https://github.com/rprichard/winpty/issues/38
    #   https://github.com/rprichard/winpty/issues/105
    # So, we always default to ASCII facsimiles, assuming that we do not wish
    # to try using Windows code page 850 (or similar), as that is likely not
    # the assigned character set.
    # TODO: Detect other cases, such as 'LC_' variables which indicate an
    #       encoding other than UTF-8.
    if 'nt' == os_class:
        if 1 == gravity: return _ascii_rectangular_elements_single
        return _ascii_rectangular_elements_double
    if 1 == gravity: return _unicode_rectangular_elements_single
    return _unicode_rectangular_elements_double


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
