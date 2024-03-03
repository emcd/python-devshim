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


# RULES:
# * Nothing in this module may depend on any module that is not part of the
#   Python standard library for the baseline version of Python.
# * Nothing in this module may depend on any other module in this package.



# pylint: disable=unused-import
from abc import ABCMeta as ABCFactory
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
# pylint: enable=unused-import

import typing as _typ


version = '1.0a202403031735'


eprint: _typ.Callable
epprint: _typ.Callable
narration_target: _typ.Any
scribe: _typ.Any


tv_error = ( TypeError, ValueError )


class Class( ABCFactory ):
    ''' Factory for all classes in the package.

        Ensures class attributes are immutable and indelible.

        Compatible with classes produced by :py:class:`abc.ABCMeta`. '''

    __slots__ = ( )

    def __setattr__( class_, name, value ):
        if '__abstractmethods__' == name or name.startswith( '_abc_' ):
            return super( ).__setattr__( name, value )
        raise fuse_exception_classes( ( AttributeError, ) )(
            "Cannot assign attribute to immutable class '{name}'.".format(
                name = derive_class_fqname( class_ ) ) )

    def __delattr__( class_, name ):
        raise fuse_exception_classes( ( AttributeError, ) )(
            "Cannot remove attribute from immutable class '{name}'.".format(
                name = derive_class_fqname( class_ ) ) )


class Omniexception( BaseException, metaclass = Class ):
    ''' Base for all exceptions in the package. '''

    def __init__( self, *posargs, exception_labels = None, **nomargs ):
        exception_labels = exception_labels or { }
        if not isinstance( exception_labels, AbstractDictionary ):
            raise fuse_exception_classes( tv_error )(
                "Invalid argument 'exception_labels' to initializer "
                f"for instance of class '{__package__}.Omniexception'; "
                "must be dictionary." )
        self.exception_labels = DictionaryProxy( exception_labels )
        super( ).__init__( *posargs, **nomargs )


def create_accretive_dictionary( validator ):
    ''' Creates dictionary which can only add entries.

        Existing entries cannot be updated or deleted.

        Useful for immutable registries. '''
    if not callable( validator ): # TODO: Assert unary invocable.
        raise fuse_exception_classes( tv_error )(
            "Cannot create accretive dictionary "
            "which has noninvocable validator." )
    dictionary = { }

    class AccretiveDictionary( AbstractDictionary, metaclass = Class ):
        ''' Adds entries which thereafter cannot be updated or deleted. '''

        __slots__ = ( )

        def __getitem__( self, name ): return dictionary[ name ]

        def __iter__( self ): return iter( dictionary )

        def __len__( self ): return len( dictionary )

        def __setitem__( self, name, value ):
            if name in dictionary:
                raise fuse_exception_classes( ( ValueError, ) )(
                    f"Cannot replace existing entry {name!r} "
                    "in accretive dictionary." )
            dictionary[ name ] = validator( value )

        def items( self ): return dictionary.items( )

        def values( self ): return dictionary.values( )

    return AccretiveDictionary( )


def create_class_fuser( primary_class ):
    ''' Creates class fuser with cache of classes. '''
    from inspect import isclass as is_class
    if not is_class( primary_class ):
        raise fuse_exception_classes( tv_error )(
            f"Primary class cannot be {primary_class!r}; must be a class." )
    cache = { }

    def fuse_classes( classes ):
        ''' Fuses additional classes to primary class. '''
        for class_ in classes:
            if not is_class( class_ ):
                raise fuse_exception_classes( tv_error )(
                    f"Additional base class cannot be {class_!r}; "
                    "must be a class." )
        cache_index = "{primary_class_name}.{classes_names}".format(
            primary_class_name = primary_class.__qualname__,
            classes_names = '__'.join( map(
                lambda class_: '_'.join( (
                    class_.__module__.replace( '.', '_' ),
                    class_.__qualname__.replace( '.', '_' ) ) ), classes ) ) )
        if cache_index not in cache:
            base_classes = ( primary_class, *classes )
            # pylint: disable=undefined-variable
            cache[ cache_index ] = Class.__new__(
                Class, cache_index, base_classes, { } )
            # pylint: enable=undefined-variable
        return cache[ cache_index ]

    return fuse_classes


def create_immutable_namespace( source ):
    ''' Creates immutable namespace from dictionary or simple namespace. '''
    from inspect import isfunction as is_function
    if isinstance( source, SimpleNamespace ): source = source.__dict__
    if not isinstance( source, AbstractDictionary ):
        raise fuse_exception_classes( tv_error )(
            "Namespace source must be dictionary or 'types.SimpleNamespace'." )
    namespace = { }
    for name, value in source.items( ):
        if not probe_valid_public_identifier( name ):
            raise fuse_exception_classes( tv_error )(
                f"Invalid namespace source key {name!r}. "
                "Must be strings which is valid Python public identifier." )
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
            raise fuse_exception_classes( tv_error )(
                "Cannot create dictionary from noniterable source "
                f"{iterable!r}." )
        if not isinstance( iterable, AbstractDictionary ):
            try: normalized_iterables.append( dict( iterable ) )
            except TypeError as exc:
                raise fuse_exception_classes( tv_error )(
                    "Cannot create dictionary from incompatible iterable."
                ) from exc
        else: normalized_iterables.append( iterable )
    from itertools import chain
    for index, value in chain( *map(
        lambda it: it.items( ), ( *normalized_iterables, dictionary_nomargs )
    ) ):
        if not callable( value ):
            raise fuse_exception_classes( tv_error )(
                "Cannot create invocable dictionary from noninvocable value "
                f"associated with index {index!r}." )
        dictionary[ index ] = value

    class InvocableDictionary( AbstractDictionary, metaclass = Class ):
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
        raise fuse_exception_classes( tv_error )(
            "Cannot create semelfactive dictionary "
            f"which has noninvocable factory {factory!r}." )
    dictionary = { }

    class SemelfactiveDictionary( AbstractDictionary, metaclass = Class ):
        ''' Produces values on access and retains them. '''

        def __getitem__( self, name ):
            if name not in dictionary:
                try: dictionary[ name ] = factory( name )
                except Exception as exc:
                    raise fuse_exception_classes( KeyError, )(
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
        raise fuse_exception_classes( tv_error )(
            "Cannot create semelfactive namespace "
            f"which has noninvocable factory {factory!r}." )
    cache = { }

    class SemelfactiveNamespace( metaclass = Class ):
        ''' Produces values on access and retains them. '''

        __slots__ = ( )

        def __getattr__( self, name ):
            if name not in cache:
                try: cache[ name ] = factory( name )
                except Exception as exc:
                    raise fuse_exception_classes( ( AttributeError, ) )(
                        f"Cannot produce attribute for {name!r}." ) from exc
            return cache[ name ]

        def __setattr__( self, name, value ):
            raise fuse_exception_classes( ( AttributeError, ) )(
                "Cannot assign attribute to semelfactive namespace." )

        def __delattr__( self, name ):
            raise fuse_exception_classes( ( AttributeError, ) )(
                "Cannot remove attribute from semelfactive namespace." )

    return SemelfactiveNamespace( )


def derive_class_fqname( class_ ):
    ''' Derives fully-qualified class name from class object. '''
    from inspect import isclass as is_class
    if not is_class( class_ ):
        raise fuse_exception_classes( tv_error )(
            "Cannot derive fully-qualified class name "
            f"for non-class {class_!r}." )
    return '.'.join( ( class_.__module__, class_.__qualname__ ) )


def derive_environment_entry_name( *parts ):
    ''' Derives environment entry name from package name and parts. '''
    for part in parts:
        if not (
            isinstance( part, str ) and part.isascii( ) and part.isalnum( )
        ):
            raise fuse_exception_classes( tv_error )(
                f"Name part {part!r} must be an ASCII, alphanumeric string "
                "to derive environment variable name." )
    return '_'.join( map( str.upper, ( __package__, *parts ) ) )


def execute_subprocess( command_specification, **nomargs ):
    ''' Executes command in subprocess.

        Raises exception on non-zero exit code. '''
    command_specification = (
        normalize_command_specification( command_specification ) )
    from subprocess import run # nosec B404
    from sys import stdout, stderr
    options = dict( text = True )
    options.update( nomargs )
    # Sanitize options.
    for option in ( 'check', ): nomargs.pop( option, None )
    if not options.get( 'capture_output', False ):
        if stdout is _data.narration_target:
            options.setdefault( 'stderr', stdout )
        else: options.setdefault( 'stdout', stderr )
    if { 'stdout', 'stderr' } & options.keys( ):
        options.pop( 'capture_output', None )
    # TODO? Handle pseudo-TTY requests with 'ptyprocess.PtyProcess'.
    # TODO? Intercept 'subprocess.SubprocessError'.
    _data.scribe.debug(
        f"Executing {command_specification!r} with {options!r}." )
    # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
    return run( command_specification, check = True, **options ) # nosec B603

# TODO: Remove this alias and use thereof.
execute_external = execute_subprocess


fuse_exception_classes = create_class_fuser( Omniexception )


def normalize_command_specification( command_specification ):
    ''' Normalizes command specification for subprocess execution.

        Strings are split into argument vectors according to platform-specific
        rules (POSIX or Windows). All elements of argument vectors are
        converted into strings. '''
    if isinstance( command_specification, str ):
        return split_command( command_specification )
    # Ensure strings are being passed as arguments.
    # Although 'subprocess.run' can accept path-like objects on all platforms,
    # as of Python 3.8, there may be non-path-like objects as arguments that
    # need to be converted to strings. So, we always convert.
    if isinstance( command_specification, AbstractSequence ):
        return tuple( map( str, command_specification ) )
    raise fuse_exception_classes( ( ValueError, ) )(
        f"Invalid command specification {command_specification!r}" )


def probe_valid_public_identifier( object_ ):
    ''' Checks if object is valid Python public identifier. '''
    from keyword import iskeyword
    return (
        isinstance( object_, str )
        and not object_.startswith( '_' )
        and object_.isidentifier( )
        and not iskeyword( object_ ) )


def split_command( command_specification ):
    ''' Splits command-line string into arguments in platform-aware manner. '''
    # https://github.com/python/cpython/issues/44990
    if 'nt' == os_class: return _windows_split_command( command_specification )
    from shlex import split as posix_split_command
    return posix_split_command( command_specification )

def _windows_split_command( command_specification ):
    ''' Splits command-line string into arguments by Windows rules. '''
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
    if ctypes.windll.kernel32.LocalFree( lpargs ):
        raise fuse_exception_classes( ( RuntimeError, ) )(
            "Could not free command arguments buffer from Windows." )
    return arguments


@context_manager
def springy_chdir( new_path ):
    ''' Changes directory, restoring original directory on context exit. '''
    from os import chdir, getcwd
    old_path = getcwd( )
    chdir( new_path )
    yield new_path
    chdir( old_path )


def view_environment_entry( parts, default = None ):
    ''' Views entry in current process environment.

        Entry name is derived from package name and supplied parts. '''
    name = derive_environment_entry_name( *parts )
    return current_process_environment.get( name, default )


# TODO: Rework to get rid of auxiliary path.
def _configure( ):
    ''' Configures development support. '''
    auxiliary_path = Path( __file__ ).parent.parent.parent.parent.resolve( )
    configuration = DictionaryProxy( dict(
        auxiliary_path = auxiliary_path,
        project_path = (
            Path( view_environment_entry(
                ( 'project', 'location' ), auxiliary_path ) )
            .resolve( strict = True ) )
    ) )
    return configuration


def _create_scribe( ):
    ''' Initializes logger for package. '''
    from logging import NullHandler, getLogger as acquire_scribe
    scribe = acquire_scribe( __package__ ) # pylint: disable=redefined-outer-name
    # https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
    scribe.addHandler( NullHandler( ) )
    scribe.setLevel( view_environment_entry( ( 'record', 'level' ), 'INFO' ) )
    return scribe


def _detect_ci_environment( ):
    ''' Returns name of current continuous integration environment.

        If none is detected, returns empty string.

        This is not inteded to be used to Volkswagen test results. '''
    if 'CI' in current_process_environment: return 'Github Actions'
    return ''


def _discover_virtual_environment_name( ):
    ''' Is execution within virtual environment of our creation?

        If yes, returns name of environment. Else, returns empty string. '''
    return view_environment_entry( ( 'venv', 'name' ), '' )


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
    narration_target = _select_narration_target,
    on_tty = _probe_tty,
    scribe = _create_scribe,
    virtual_environment_name = _discover_virtual_environment_name,
) )
__getattr__ = _data.__getattr__
