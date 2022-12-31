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


''' Fundamental constants and utilities for development support. '''

import typing as _typ

# pylint: disable=unused-import
from collections.abc import (
    Mapping as AbstractDictionary,
    Sequence as AbstractSequence,
)
from contextlib import contextmanager as context_manager
from functools import partial as partial_function
from types import (
    MappingProxyType as DictionaryProxy,
    SimpleNamespace,
)
# pylint: enable=unused-import


environment_variable_prefix = __package__.upper( )


def naively_parse_version( version ):
    ''' Naively splits version on periods and converts parts to integers.

        Leaves non-convertible parts as strings. '''
    # TODO: Validate version.
    return tuple( map(
        lambda part: int( part ) if part.isdigit( ) else part,
        version.split( '.' ) ) )


def compare_version( left, right, parser = naively_parse_version ):
    ''' Properly compares two version strings.

        I.e., 3.10 < 3.7 if comparison is lexicographic.
        But, 3.10 > 3.7 with this version comparison.

        If left > right, then returns 1.
        If left == right, then returns 0.
        If left < right, then returns -1. '''
    # TODO: Validate parser.
    left = parser( left )
    right = parser( right )
    if left == right: return 0
    return 1 if left > right else -1


def create_immutable_namespace( source ):
    ''' Creates immutable namespace from dictionary or simple namespace. '''
    from inspect import isfunction as is_function
    # TODO: Validate source.
    if isinstance( source, SimpleNamespace ): source = source.__dict__
    namespace = { }
    for name, value in source.items( ):
        # TODO: Assert valid Python public identifiers.
        if is_function( value ):
            namespace[ name ] = staticmethod( value )
        elif isinstance( value, ( AbstractDictionary, SimpleNamespace, ) ):
            namespace[ name ] = create_immutable_namespace( value )
        else: namespace[ name ] = value
    namespace[ '__slots__' ] = ( )
    class_ = type( 'Namespace', ( ), namespace )
    return class_( )


def create_registrar( validator ):
    ''' Creates registar for functionality extensions. '''
    # TODO: Validate validator.
    registry = { }

    # TODO: Immutable class.
    class Registrar( AbstractDictionary ):
        ''' Registrar for functionality extensions. '''

        def __getitem__( self, name ): return registry[ name ]

        def __init__( self ): self.visor = DictionaryProxy( registry )

        def __iter__( self ): return iter( self.visor )

        def __len__( self ): return len( registry )

        def __setitem__( self, name, value ):
            if name in registry:
                # TODO: Properly handle error case.
                raise ValueError
            registry[ name ] = validator( value )

        def survey_registry( self ):
            ''' Returns immutable view upon registry. '''
            return self.visor

    return Registrar( )


def module_introduce_accretive_cache( calculators_provider ):
    ''' Produces module __getattr__ which computes and caches values.

        The ``calculators_provider`` argument must return a dictionary of cache
        entry names with nullary invocables as the correspondent values. Each
        invocable is a calculator which produces a value to populate the cache.
        Any attribute name not in the dictionary results in an
        :py:exc:`AttributeError`. '''
    cache = { }
    from .develop import validate_calculators_provider
    validate_calculators_provider( calculators_provider )
    calculators = DictionaryProxy( calculators_provider( ) )

    def module_getattr( name ):
        ''' Computes values on demand and caches them. '''
        if name not in calculators: raise AttributeError
        if name not in cache: cache[ name ] = calculators[ name ]( )
        return cache[ name ]

    return module_getattr


def produce_accretive_cacher( calculators_provider ):
    ''' Produces object which computes and caches values. '''
    from .develop import produce_accretive_cacher as producer
    # TODO: Immutability on producer class.
    # TODO: Interception of exceptions.
    return producer( calculators_provider )


@context_manager
def springy_chdir( new_path ):
    ''' Changes directory, restoring original directory on context exit. '''
    from os import chdir, getcwd
    old_path = getcwd( )
    chdir( new_path )
    yield new_path
    chdir( old_path )


def _detect_ci_environment( ):
    ''' Returns name of current continuous integration environment.

        If none is detected, returns empty string.

        This is not inteded to be used to Volkswagen test results. '''
    from os import environ as current_process_environment
    if 'CI' in current_process_environment: return 'Github Actions'
    return ''

#: Detected CI environment. Empty string if none detected.
ci_environment = _detect_ci_environment( )


def _select_narration_target( ):
    ''' Selects which stream is target for narration and diagnostics. '''
    # Note: Until we have a good reason to use stdout,
    #       we always choose stderr.
    from sys import stderr
    return stderr

#: Target stream for narration and diagnostics.
narration_target = _select_narration_target( )


def _probe_tty( ):
    ''' Detects if current process attached to a TTY.

        Boolean result can be used to decide whether to suppress the use of
        ANSI SGR codes for some programs, for example. '''
    return narration_target.isatty( )

#: Is current process attached to a TTY?
on_tty = _probe_tty( )


def _select_narrative_functions( ):
    ''' Selects which functions to use for narration and diagnostics. '''
    from pprint import pprint
    from sys import stderr
    if stderr is not narration_target: return print, pprint
    return (
        partial_function( print, file = stderr ),
        partial_function( pprint, stream = stderr ),
    )

eprint, epprint = _select_narrative_functions( )


def _acquire_driver_module( ): # pylint: disable=inconsistent-return-statements
    from sys import modules
    from . import develop as develop_
    if '__main__' in modules:
        module = modules[ '__main__' ]
        # If we are being run by our own driver, then access it directly.
        if develop_.package_name == getattr( module, 'package_name', None ):
            return module
    return

driver_module = _acquire_driver_module( )


def _enhance_narration( ):
    ''' Enhances narrative functions as desired. '''
    if None is driver_module: return
    from logging import getLogger as acquire_scribe
    from sys import stderr
    from rich.console import Console
    from rich.logging import RichHandler
    scribe_ = acquire_scribe( )
    for handler in scribe_.handlers: scribe_.removeHandler( handler )
    # TODO: Alter log format.
    scribe_.addHandler( RichHandler(
        console = Console( stderr = stderr == narration_target ),
        rich_tracebacks = True,
        show_time = False ) )
    scribe_.debug( 'Rich logging enabled.' )

_enhance_narration( )


# TODO: Replace with 'develop.execute_subprocess' once narration target has
#       received proper consideration.
def execute_external( command_specification, **nomargs ):
    ''' Executes command in subprocess.

        Raises exception on non-zero exit code. '''
    options = dict( text = True )
    from subprocess import run # nosec B404
    from sys import stdout, stderr
    options.update( nomargs )
    if not options.get( 'capture_output', False ):
        if stdout is narration_target: options[ 'stderr' ] = stdout
        else: options[ 'stdout' ] = stderr
    if { 'stdout', 'stderr' } & options.keys( ):
        options.pop( 'capture_output', None )
    options.pop( 'check', None )
    if isinstance( command_specification, str ):
        from shlex import split as split_command
        command_specification = split_command( command_specification )
    # TODO: Python 3.8: Remove. Has support for WindowsPath.
    elif isinstance( command_specification, AbstractSequence ):
        command_specification = tuple( map( str, command_specification ) )
    # TODO? Handle pseudo-TTY requests with 'ptyprocess.PtyProcess'.
    # TODO? Intercept 'subprocess.SubprocessError'.
    scribe.debug( f"Executing {command_specification!r} with {options!r}." )
    # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
    return run( command_specification, check = True, **options ) # nosec B603


# TODO: Use exception factories instead of 'expire' function.
#       Exception factory dependencies will be guaranteed,
#       so no more special "early" initialization.
def expire( exit_specifier, message ) -> _typ.NoReturn:
    # Preferred name would be 'exit' or 'quit' but those are Python builtins.
    # Could have named it 'die', which is short, sweet, and old school,
    # but other function names are Latin-based whereas 'die' is Germanic.
    # Pet peeve about linguistic consistency....
    ''' Logs message and exits current process. '''
    from .develop import Exit
    raise Exit( exit_specifier, message )


def _configure( ):
    ''' Configures development support. '''
    from pathlib import Path
    auxiliary_path = Path( __file__ ).parent.parent.parent.parent.resolve( )
    from os import environ as current_process_environment
    configuration_ = DictionaryProxy( dict(
        auxiliary_path = auxiliary_path,
        project_path = Path( current_process_environment.get(
            'DEVSHIM_PROJECT_LOCATION', auxiliary_path ) ).resolve( ),
        scribe = _create_scribe( ),
    ) )
    return configuration_

def _create_scribe( ):
    ''' Initializes logger for package. '''
    from logging import INFO, NullHandler, getLogger as get_logger
    scribe_ = get_logger( __package__ )
    # https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
    scribe_.addHandler( NullHandler( ) )
    from os import environ as current_process_environment
    scribe_.setLevel( current_process_environment.get(
        'DEVSHIM_RECORD_LEVEL', INFO ) )
    return scribe_

configuration = _configure( )
scribe = configuration[ 'scribe' ]


def assert_sanity( ):
    ''' Assert that operational environment is sane. '''
    # TODO: Implement.
