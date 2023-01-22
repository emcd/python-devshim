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


# pylint: disable=unused-import
from collections.abc import (
    Iterable as AbstractIterable,
    Mapping as AbstractDictionary,
    Sequence as AbstractSequence,
)
from contextlib import contextmanager as context_manager
from functools import partial as partial_function
from os import environ as current_process_environment, name as os_class
from pathlib import Path
from types import (
    MappingProxyType as DictionaryProxy,
    SimpleNamespace,
)

from lockup import Class, reclassify_module
# pylint: enable=unused-import


import typing as _typ

eprint: _typ.Callable
epprint: _typ.Callable
scribe: _typ.Any


def create_accretive_dictionary( validator ):
    ''' Creates dictionary which can only add entries.

        Existing entries cannot be updated or deleted.

        Useful for immutable registries. '''
    # TODO: Use exception factory.
    if not callable( validator ): # TODO: Assert unary invocable.
        raise ValueError(
            f"Cannot create accretive dictionary "
            f"which has noninvocable validator. " )
    dictionary = { }

    # TODO: Immutable class.
    class AccretiveDictionary( AbstractDictionary ):
        ''' Adds entries which thereafter cannot be updated or deleted. '''

        __slots__ = ( )

        def __getitem__( self, name ): return dictionary[ name ]

        def __iter__( self ): return iter( dictionary )

        def __len__( self ): return len( dictionary )

        def __setitem__( self, name, value ):
            if name in dictionary:
                # TODO: Use exception factory.
                raise ValueError(
                    f"Cannot replace existing entry {name!r} "
                    f"in accretive dictionary." )
            dictionary[ name ] = validator( value )

        def items( self ): return dictionary.items( )

        def values( self ): return dictionary.values( )

    return AccretiveDictionary( )


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


def create_invocable_dictionary( *iterables, **dictionary_nomargs ): # pylint: disable=too-complex
    ''' Creates dictionary whose values can be invoked by name.

        Each value must be invocable. '''
    dictionary = { }
    normalized_iterables = [ ]
    for iterable in iterables:
        if not isinstance( iterable, AbstractIterable ):
            # TODO: Use exception factory.
            raise ValueError(
                f"Cannot create dictionary from noniterable source." )
        if not isinstance( iterable, AbstractDictionary ):
            try: normalized_iterables.append( dict( iterable ) )
            except TypeError as exc:
                raise ValueError(
                    f"Cannot create dictionary from incompatible iterable."
                ) from exc
        else: normalized_iterables.append( iterable )
    from itertools import chain
    for index, value in chain( *map(
        lambda it: it.items( ), ( *normalized_iterables, dictionary_nomargs )
    ) ):
        if not callable( value ):
            # TODO: Use exception factory.
            raise ValueError(
                f"Cannot create invocable dictionary from noninvocable value "
                f"associated with index {index!r}." )
        dictionary[ index ] = value

    # TODO: Immutable class.
    class InvocableDictionary( AbstractDictionary ):
        ''' Dictionary with invocable entries. '''

        __slots__ = ( )

        # TODO: Python 3.8: Make 'name' positional-only argument.
        def __call__( self, name, *posargs, **nomargs ):
            return dictionary[ name ]( *posargs, **nomargs )

        def __getitem__( self, name ): return dictionary[ name ]

        def __iter__( self ): return iter( dictionary )

        def __len__( self ): return len( dictionary )

        def items( self ): return dictionary.items( )

        def values( self ): return dictionary.values( )

    return InvocableDictionary( )


def create_semelfactive_dictionary( factory ):
    ''' Create dictionary which produces and retains values on access.

        A value is produced exactly once, upon initial access. Thereafter, the
        value remains in cache and is immutable.

        The factory must take one argument, the name of the entry, and use that
        to produce a value. '''
    if not callable( factory ): # TODO: Assert unary invocable.
        # TODO: Use exception factory.
        raise ValueError(
            f"Cannot create semelfactive dictionary "
            f"which has noninvocable factory." )
    dictionary = { }

    # TODO: Class immutability.
    class SemelfactiveDictionary( AbstractDictionary ):
        ''' Produces values on access and retains them. '''

        def __getitem__( self, name ):
            if name not in dictionary:
                try: dictionary[ name ] = factory( name )
                except Exception as exc:
                    # TODO: Use exception factory.
                    raise KeyError(
                        f"Cannot produce entry for {name!r}." ) from exc
            return dictionary[ name ]

        def __iter__( self ): return iter( dictionary )

        def __len__( self ): return len( dictionary )

        def items( self ): return dictionary.items( )

        def values( self ): return dictionary.values( )

    return SemelfactiveDictionary( )


def create_semelfactive_namespace( factory ):
    ''' Creates namespace which produces and retains values on access.

        A value is produced exactly once, upon initial access. Thereafter, the
        value remains in cache and is immutable.

        The factory must take one argument, the name of the entry, and use that
        to produce a value. '''
    # NOTE: Similar implementation exists in 'develop.py'.
    #       Improvements should be reflected in both places.
    if not callable( factory ): # TODO: Assert unary invocable.
        # TODO: Use exception factory.
        raise ValueError(
            f"Cannot create semelfactive namespace "
            f"which has noninvocable factory." )
    cache = { }

    # TODO: Class immutability.
    class SemelfactiveNamespace:
        ''' Produces values on access and retains them. '''

        __slots__ = ( )

        def __getattr__( self, name ):
            if name not in cache:
                try: cache[ name ] = factory( name )
                except Exception as exc:
                    raise AttributeError(
                        f"Cannot produce attribute for {name!r}." ) from exc
            return cache[ name ]

        def __setattr__( self, name, value ):
            # TODO: Use exception factory.
            raise AttributeError(
                "Cannot assign attribute to semelfactive namespace." )

        def __delattr__( self, name ):
            # TODO: Use exception factory.
            raise AttributeError(
                "Cannot remove attribute from semelfactive namespace." )

    return SemelfactiveNamespace( )


def derive_class_fqname( class_ ):
    ''' Derives fully-qualified class name from class object. '''
    # NOTE: Similar implementation exists in 'develop.py'.
    #       Improvements should be reflected in both places.
    from inspect import isclass as is_class
    if not is_class( class_ ):
        # TODO: Use exception factory.
        raise ValueError(
            f"Cannot fully-qualified class name for non-class {class_!r}." )
    return '.'.join( ( class_.__module__, class_.__qualname__ ) )


def derive_environment_variable_name( *parts ):
    ''' Derives environment variable name from parts and package name. '''
    # NOTE: Similar implementation exists in 'develop.py'.
    #       Improvements should be reflected in both places.
    # TODO: Validate parts with 'str.isalnum'.
    return '_'.join( map( str.upper, ( __package__, *parts ) ) )


# TODO: Absorb improvements from 'develop.py'.
def execute_subprocess( command_specification, **nomargs ):
    ''' Executes command in subprocess.

        Raises exception on non-zero exit code. '''
    # NOTE: Similar implementation exists in 'develop.py'.
    #       Improvements should be reflected in both places.
    command_specification = _normalize_command_specification(
        command_specification )
    options = dict( text = True )
    from subprocess import run # nosec B404
    from sys import stdout, stderr
    options.update( nomargs )
    if not options.get( 'capture_output', False ):
        if stdout is _data.narration_target: options[ 'stderr' ] = stdout
        else: options[ 'stdout' ] = stderr
    if { 'stdout', 'stderr' } & options.keys( ):
        options.pop( 'capture_output', None )
    options.pop( 'check', None )
    # TODO? Handle pseudo-TTY requests with 'ptyprocess.PtyProcess'.
    # TODO? Intercept 'subprocess.SubprocessError'.
    _data.scribe.debug(
        f"Executing {command_specification!r} with {options!r}." )
    # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
    return run( command_specification, check = True, **options ) # nosec B603

# TODO: Remove this alias and use thereof.
execute_external = execute_subprocess

def _normalize_command_specification( command_specification ):
    # NOTE: Similar implementation exists in 'develop.py'.
    #       Improvements should be reflected in both places.
    if isinstance( command_specification, str ):
        return split_command( command_specification )
    # Ensure strings are being passed as arguments.
    # Although 'subprocess.run' can accept path-like objects on all platforms,
    # as of Python 3.8, there may be non-path-like objects as arguments that
    # need to be converted to strings. So, we always convert.
    if isinstance( command_specification, AbstractSequence ):
        return tuple( map( str, command_specification ) )
    # TODO: Use exception factory.
    raise ValueError(
        f"Invalid command specification {command_specification!r}" )


def split_command( command_specification ):
    ''' Splits command-line string into arguments in platform-aware manner. '''
    # NOTE: Similar implementation exists in 'develop.py'.
    #       Improvements should be reflected in both places.
    # https://github.com/python/cpython/issues/44990
    if 'nt' == os_class: return _windows_split_command( command_specification )
    from shlex import split as posix_split_command
    return posix_split_command( command_specification )

def _windows_split_command( command_specification ):
    ''' Splits command-line string into arguments by Windows rules. '''
    # NOTE: Similar implementation exists in 'develop.py'.
    #       Improvements should be reflected in both places.
    # https://stackoverflow.com/a/35900070/14833542
    # https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-commandlinetoargvw
    import ctypes
    arguments_count = ctypes.c_int( )
    ctypes.windll.shell32.CommandLineToArgvW.restype = (
        ctypes.POINTER( ctypes.c_wchar_p ) )
    lpargs = (
        ctypes.windll.shell32.CommandLineToArgvW(
            command_specification, ctypes.byref( arguments_count ) ) )
    arguments = [ lpargs[ i ] for i in range( arguments_count.value ) ]
    # TODO: Use exception factory.
    if ctypes.windll.kernel32.LocalFree( lpargs ): raise AssertionError
    return arguments


@context_manager
def springy_chdir( new_path ):
    ''' Changes directory, restoring original directory on context exit. '''
    from os import chdir, getcwd
    old_path = getcwd( )
    chdir( new_path )
    yield new_path
    chdir( old_path )


def _configure( ):
    ''' Configures development support. '''
    auxiliary_path = Path( __file__ ).parent.parent.parent.parent.resolve( )
    configuration = DictionaryProxy( dict(
        auxiliary_path = auxiliary_path,
        project_path = Path( current_process_environment.get(
            derive_environment_variable_name( 'project', 'location' ),
            auxiliary_path ) ).resolve( ),
    ) )
    return configuration


def _create_scribe( ):
    ''' Initializes logger for package. '''
    if _data.main_module_compatibility: _enhance_ultimate_scribe( )
    from logging import INFO, NullHandler, getLogger as acquire_scribe
    scribe = acquire_scribe( __package__ ) # pylint: disable=redefined-outer-name
    # https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
    scribe.addHandler( NullHandler( ) )
    scribe.setLevel( current_process_environment.get(
        derive_environment_variable_name( 'record', 'level' ), INFO ) )
    return scribe

def _enhance_ultimate_scribe( ):
    ''' Enhances root logger as desired. '''
    from logging import getLogger as acquire_scribe
    from sys import stderr
    from rich.console import Console
    from rich.logging import RichHandler
    scribe = acquire_scribe( ) # pylint: disable=redefined-outer-name
    for handler in scribe.handlers: scribe.removeHandler( handler )
    # TODO: Alter log format.
    scribe.addHandler( RichHandler(
        console = Console( stderr = stderr == _data.narration_target ),
        rich_tracebacks = True,
        show_time = False ) )
    scribe.debug( "Rich logging enabled. We're not in Kansas anymore." )


def _check_main_module_compatibility( ):
    from sys import modules
    if '__main__' in modules:
        module = modules[ '__main__' ]
        # TODO? Check version compatibility.
        return __package__ == getattr( module, 'package_name', None )
    return False


def _detect_ci_environment( ):
    ''' Returns name of current continuous integration environment.

        If none is detected, returns empty string.

        This is not inteded to be used to Volkswagen test results. '''
    if 'CI' in current_process_environment: return 'Github Actions'
    return ''


def _discover_virtual_environment_name( ):
    ''' Is execution within virtual environment of our creation?

        If yes, returns name of environment. Else, returns empty string. '''
    return current_process_environment.get(
        derive_environment_variable_name( 'venv', 'name' ), '' )


def _probe_tty( ):
    ''' Detects if current process attached to a TTY.

        Boolean result can be used to decide whether to suppress the use of
        ANSI SGR codes for some programs, for example. '''
    return _data.narration_target.isatty( )


def _provide_simple_narrative_function( ):
    ''' Provides function to use for simple narration and diagnostics. '''
    return partial_function( print, file = _data.narration_target )


def _provide_structural_narrative_function( ):
    ''' Provides function to use for structural narration and diagnostics. '''
    from pprint import pprint
    return partial_function( pprint, stream = _data.narration_target )


def _select_narration_target( ):
    ''' Selects which stream is target for narration and diagnostics. '''
    # Note: Until we have a good reason to use stdout,
    #       we always choose stderr.
    from sys import stderr
    return stderr


_data = create_semelfactive_namespace( create_invocable_dictionary(
    ci_environment = _detect_ci_environment,
    configuration = _configure,
    epprint = _provide_structural_narrative_function,
    eprint = _provide_simple_narrative_function,
    main_module_compatibility = _check_main_module_compatibility,
    narration_target = _select_narration_target,
    on_tty = _probe_tty,
    scribe = _create_scribe,
    virtual_environment_name = _discover_virtual_environment_name,
) )
__getattr__ = _data.__getattr__


reclassify_module( __name__ )
