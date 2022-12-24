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
from contextlib import contextmanager as context_manager
from functools import partial as partial_function
from types import (
    MappingProxyType as DictionaryProxy,
    SimpleNamespace,
)
# pylint: enable=unused-import


def module_introduce_accretive_cache( calculators_provider ):
    ''' Produces module __getattr__ which computes and caches values.

        The ``calculators_provider`` argument must return a dictionary of cache
        entry names with nullary invocables as the correspondent values. Each
        invocable is a calculator which produces a value to populate the cache.
        Any attribute name not in the dictionary results in an
        :py:exc:`AttributeError`. '''
    cache = { }
    # TODO: Validate calculators provider.
    calculators = DictionaryProxy( calculators_provider( ) )

    def module_getattr( name ):
        ''' Computes values on demand and caches them. '''
        if name not in calculators: raise AttributeError
        if name not in cache: cache[ name ] = calculators[ name ]( )
        return cache[ name ]

    return module_getattr


def produce_accretive_cacher( calculators_provider ):
    ''' Produces object which computes computes and caches values.

        The ``calculators_provider`` argument must return a dictionary of cache
        entry names with nullary invocables as the correspondent values. Each
        invocable is a calculator which produces a value to populate the cache.
        Any attribute name not in the dictionary results in an
        :py:exc:`AttributeError`. '''
    cache = { }
    # TODO: Validate calculators provider.
    calculators = DictionaryProxy( calculators_provider( ) )

    # TODO: Class immutability.
    class AccretiveCacher:
        ''' Computes values on demand and caches them. '''

        __slots__ = ( )

        def __getattr__( self, name ):
            if name not in calculators: raise AttributeError
            if name not in cache: cache[ name ] = calculators[ name ]( )
            return cache[ name ]

        # TODO: Override __setattr__ and __delattr__ for object immutability.

    return AccretiveCacher( )


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


# TODO: Provide appropriate logging handler.


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
    # TODO? Handle pseudo-TTY requests with 'ptyprocess.PtyProcess'.
    # TODO? Intercept 'subprocess.SubprocessError'.
    scribe.debug( f"Executing {command_specification!r} with {options!r}." )
    # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
    return run( command_specification, check = True, **options ) # nosec B603


def _enumerate_exit_codes( ):
    # Standardized on recommended BSD exit codes across all platforms.
    # Windows seems to have no standard for application exit codes
    # and its list of system error codes is massive. (And error codes are not
    # necessarily exit codes.) Cannot rely on "constants" from Python standard
    # library 'os' modules as they are mostly not cross-platform.
    # Can also use custom codes between 1 and 63 for failures, as necessary.
    # References:
    #   https://docs.python.org/3/library/os.html#os.EX_OK
    #   https://www.freebsd.org/cgi/man.cgi?query=sysexits&apropos=0&sektion=0&manpath=FreeBSD+4.3-RELEASE&format=html
    #   https://tldp.org/LDP/abs/html/exitcodes.html
    #   https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes?redirectedfrom=MSDN#system-error-codes
    return {
        'general failure':      1,
        'invalid data':         65, # EX_DATAERR
        'invalid state':        70, # EX_SOFTWARE
        'invalid usage':        64, # EX_USAGE
        'success':              0,  # EX_OK
    }

_exit_codes = _enumerate_exit_codes( )


def expire( exit_specifier, message ) -> _typ.NoReturn:
    # Preferred name would be 'exit' or 'quit' but those are Python builtins.
    # Could have named it 'die', which is short, sweet, and old school,
    # but other function names are Latin-based whereas 'die' is Germanic.
    # Pet peeve about linguistic consistency....
    ''' Logs message and exits current process. '''
    from numbers import Integral
    if isinstance( exit_specifier, Integral ):
        exit_code = int( exit_specifier )
    elif exit_specifier not in _exit_codes:
        scribe.warning( f"Invalid exit code name {exit_specifier!r}." )
        exit_code = _exit_codes[ 'general failure' ]
    else: exit_code = _exit_codes[ exit_specifier ]
    message = str( message )
    if 0 == exit_code: scribe.info( message )
    # TODO: Python 3.8: stacklevel = 2
    else: scribe.critical( message, stack_info = True )
    raise SystemExit( exit_code )


def _configure( ):
    ''' Configures development support. '''
    from pathlib import Path
    auxiliary_path = Path( __file__ ).parent.parent.parent.parent.resolve( )
    from os import environ as current_process_environment
    configuration_ = DictionaryProxy( dict(
        auxiliary_path = auxiliary_path,
        project_path = Path( current_process_environment.get(
            '_DEVSHIM_PROJECT_PATH', auxiliary_path ) ).resolve( ),
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
        '_DEVSHIM_RECORD_LEVEL', INFO ) )
    return scribe_

configuration = _configure( )
scribe = configuration[ 'scribe' ]


def assert_sanity( ):
    ''' Assert that operational environment is sane. '''
    # TODO: Implement.
