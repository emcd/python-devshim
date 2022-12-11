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


''' Classes of exceptions emitted by the functionality of this package. '''


class Omniexception( BaseException ):
    ''' Base for all exceptions in the package. '''

    # TODO: Inject functionality from refactored 'lockup.exceptionality'.
    #       Possibly via class factory class.

    def __init__( self, *posargs, exception_labels = None, **nomargs ):
        from collections.abc import Mapping as AbstractDictionary
        from types import MappingProxyType as DictionaryProxy
        exception_labels = exception_labels or { }
        if not isinstance( exception_labels, AbstractDictionary ):
            raise provide_exception_factory( 'argument validation' )(
                'exception_labels', Omniexception.__init__, 'dictionary' )
        self.exception_labels = DictionaryProxy( exception_labels )
        super( ).__init__( *posargs, **nomargs )


def provide_exception_class( name ):
    ''' Provides exception class by name.

        Used by exception factories in :py:mod:`lockup.exceptionality`. '''
    if 'Omniexception' == name: return Omniexception
    specifier = _class_fusion_specifiers.get( name )
    if None is specifier:
        raise provide_exception_factory( 'inaccessible entity' )(
            name, 'name of available exception class' )
    # TODO: Replace when exception factories can create fusion classes.
    return _fuse_exception_classes( specifier )


def provide_exception_factory( name ):
    ''' Provides exception factory by name.

        Looks in this module first and then in :py:mod:`lockup.exceptionality`.
        Returns factory which is bound to use the exception class provider from
        this module. '''
    complete_name = f"create_{name}_exception".replace( ' ', '_' )
    from .packages import assert_python_packages
    assert_python_packages( ( 'lockup', ) )
    from lockup.exceptionality import our_factories as standard_factories
    if complete_name in globals( ):
        # nosemgrep: python.lang.security.dangerous-globals-use
        exception_factory = globals( )[ complete_name ]
    elif hasattr( standard_factories, complete_name ):
        exception_factory = getattr( standard_factories, complete_name )
    else:
        raise provide_exception_factory( 'inaccessible entity' )(
            complete_name, 'name of available exception factory' )
    from functools import partial as partial_function
    return partial_function( exception_factory, provide_exception_class )

_excfp = provide_exception_factory # Internal alias.


def create_invalid_data_exception(
    exception_class_provider, message, extra_data = None,
):
    ''' Creates error about invalid data. '''
    sui = create_invalid_data_exception
    from lockup.validators import validate_argument_class
    validate_argument_class( _excfp, message, str, 'message', sui )
    return _produce_exception(
        exception_class_provider, sui, 'IncorrectData', message, extra_data )


def _create_class_fusion_specifiers( ):
    from types import MappingProxyType as DictionaryProxy
    return DictionaryProxy( dict(
        AbsentImplementation = ( NotImplementedError, ),
        ImpermissibleAttributeOperation = ( AttributeError, TypeError, ),
        ImpermissibleOperation = ( TypeError, ),
        InaccessibleAttribute = ( AttributeError, ),
        IncorrectData = ( TypeError, ValueError, ),
        InvalidOperation = ( Exception, ),
        InvalidState = ( RuntimeError, ),
    ) )

_class_fusion_specifiers = _create_class_fusion_specifiers( )


def _create_exception_class_fuser( ):
    ''' Creates exception class fuser with cache of classes. '''
    cache = { }

    def fuse_exception_classes( classes ):
        ''' Fuses exceptions from outside of package with Omniexception. '''
        # TODO: Validate classes.
        # TODO: Validate package class.
        cache_index = "{package_class_name}.{classes_names}".format(
            package_class_name = Omniexception.__name__,
            classes_names = '__'.join( map(
                lambda class_: '_'.join( (
                    class_.__module__.replace( '.', '_' ),
                    class_.__qualname__.replace( '.', '_' ) ) ), classes ) ) )
        if cache_index not in cache:
            base_classes = ( Omniexception, *classes )
            # TODO? Create with different class factory.
            cache[ cache_index ] = type( cache_index, base_classes, { } )
        return cache[ cache_index ]

    return fuse_exception_classes

_fuse_exception_classes = _create_exception_class_fuser( )


def _produce_exception(
    exception_class_provider, invocation, name, message, extra_data
):
    ''' Produces exception by provider with message and failure class. '''
    # TODO: Use generalized 'produce_exception' when it is available.
    #       This is mostly a copy from 'lockup.exceptionality'.
    from lockup.exceptionality.general import (
        intercept_exception_class_provider,
    )
    exception_class_provider = intercept_exception_class_provider(
        exception_class_provider, invocation )
    from lockup.exceptionality.our_factories import ExtraData
    if None is extra_data: extra_data = ExtraData( )
    from lockup.validators import validate_argument_class
    validate_argument_class(
        _excfp, extra_data, ExtraData, 'extra_data', invocation )
    failure_class = ' '.join( invocation.__name__.split( '_' )[ 1 : -1 ] )
    return exception_class_provider( name )(
        message,
        *extra_data.positional_arguments,
        **_inject_exception_labels(
            extra_data, { 'failure class': failure_class } ) )


def _inject_exception_labels( extra_data, exception_labels ):
    ''' Injects exception labels into dictionary of nominative arguments.

        If the 'exception_labels' key already exists, does nothing.
        Also updates the 'exception_labels' entry with extra user-supplied
        exception labels. '''
    # TODO: Use generalized 'inject_exception_labels' when it is available.
    #       This is a copy from 'lockup.exceptionality'.
    extra_arguments = extra_data.nominative_arguments
    if 'exception_labels' in extra_arguments: return extra_arguments
    extra_arguments = extra_arguments.copy( )
    extra_arguments[ 'exception_labels' ] = exception_labels
    extra_arguments[ 'exception_labels' ].update( extra_data.exception_labels )
    return extra_arguments
