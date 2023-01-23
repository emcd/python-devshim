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


''' Utilities for management of language installations. '''


import typing as _typ

# pylint: disable=unused-import
from abc import ABCMeta as ABCFactory, abstractmethod as abstract
from types import MappingProxyType as DictionaryProxy

from lockup import reclassify_module

from .. import base as __
from ..base import (
    create_immutable_namespace,
    create_invocable_dictionary,
    create_semelfactive_dictionary,
    create_semelfactive_namespace,
)
from ..exceptions import (
    create_abstract_invocation_error,
    create_argument_validation_error,
    create_data_validation_error,
    validate_argument_class,
)
from ..platforms.identity import calculate_platform_identifier
# pylint: enable=unused-import


# Note: Need to explicitly declare __getattr__-synthesized module attributes
#       to avoid issues with MyPy and Pylint.
locations: _typ.Any


# TODO: Class immutability.
class Language:
    ''' Model for language. '''

    __slots__ = ( 'name', 'title', 'descriptor_class', 'version_parser', )

    def __init__( self, name, title, version_parser ):
        # TODO: Validate arguments.
        self.name = name
        self.title = title
        self.version_parser = version_parser
        self.descriptor_class = type(
            'LanguageDescriptor',
            ( LanguageDescriptor, ),
            dict( language = self ) )
        register_language( self )

    def derive_actual_version( self, version ):
        ''' Derives comparable object for actual language version.

            The result is a comparable representation of a language version
            according to the standard scheme for versions of the language. '''
        return self.version_parser( version )

    def detect_default_descriptor( self ):
        ''' Detects default language descriptor.

            If in a virtual environment, then the language descriptor for that
            environment is returned. Else, the first available language
            descriptor from the project descriptors is returned. '''
        # TODO: Detect if in relevant virtual environment and infer descriptor.
        return next( iter( self.survey_descriptors( ).values( ) ) )

    def produce_descriptor( self, descriptor = None ):
        ''' Produces instance of language descriptor. '''
        if None is descriptor: return self.detect_default_descriptor( )
        return self.descriptor_class( descriptor )

    def survey_descriptors( self ):
        ''' Returns language descriptors which have relevant definitions. '''
        descriptor_class = self.descriptor_class
        definitions = _data.definitions[ self.name ]
        from os import environ as current_process_environment
        descriptor = current_process_environment.get(
            __.derive_environment_variable_name( self.name, 'descriptor' ) )
        if None is not descriptor:
            if descriptor in definitions:
                definitions = { descriptor: definitions[ descriptor ] }
            else:
                raise create_data_validation_error(
                    f"No descriptor {descriptor!r} in definitions "
                    f"for language {self.title}." )
        descriptors = { }
        for descriptor, definition in definitions.items( ):
            if not descriptor_class.is_supportable( definition ): continue
            descriptors[ descriptor ] = descriptor_class( descriptor )
        return DictionaryProxy( descriptors )

    def validate_descriptor( self, descriptor ):
        ''' Validates descriptor against available language descriptors. '''
        if descriptor not in self.survey_descriptors( ):
            raise create_argument_validation_error(
                'descriptor', self.validate_descriptor,
                f"defined {self.title} descriptor" )
        return descriptor


# TODO: Class immutability.
class LanguageDescriptor( metaclass = ABCFactory ):
    ''' Abstract base for language descriptors. '''

    language: Language

    @classmethod
    def create_record( class_, name ):
        ''' Creates language descriptor record and persists it. '''
        definition = _data.definitions[ class_.language.name ][ name ]
        location = class_.infer_records_location( name )
        if not location.exists( ): records = { }
        else: records = dict( class_.summon_records( name ) )
        from operator import itemgetter
        record = next( iter( sorted(
            class_.survey_provider_support( definition ),
            key = itemgetter( 'implementation-version' ), reverse = True ) ) )
        records[ calculate_platform_identifier( ) ] = dict( record )
        class_.persist_records( name, records )
        return record

    @classmethod
    def infer_records_location( class_, descriptor = None ):
        ''' Infers location for language descriptor records.

            If descriptor is provided, then name of descriptor-specific
            file is appended to directory location. '''
        location = _data.locations.data.joinpath(
            f"{class_.language.name}/descriptors" )
        if None is not descriptor: return location / f"{descriptor}.toml"
        return location

    @classmethod
    def is_supportable( class_, definition, platform = None ):
        ''' Is language descriptor supportable by any of its providers?

            If platform is not supplied, then current platform is assumed. '''
        definition = class_.provide_definition( definition )
        # TODO: Consider explicit platform constraints.
        supports = class_.survey_provider_support(
            definition, platform = platform )
        if not supports: return False
        return True

    @classmethod
    def persist_records( class_, name, records ):
        ''' Persists language descriptor records. '''
        from tomli_w import dump as persist
        location = class_.infer_records_location( name )
        location.parent.mkdir( exist_ok = True, parents = True )
        records = {
            platform_name: {
                'implementation-version':
                    str( record[ 'implementation-version' ] ),
                'provider': record[ 'provider' ],
            } for platform_name, record in records.items( )
        }
        document = { 'format-version': 1, 'platforms': records }
        with location.open( 'wb' ) as file:
            # TODO: Write comment header to warn about machine-generated code.
            persist( document, file )

    @classmethod
    def provide_definition( class_, descriptor ):
        ''' Provides descriptor definition. '''
        if isinstance( descriptor, LanguageDescriptor ):
            return descriptor.definition
        if isinstance( descriptor, str ):
            return _data.definitions[ class_.language.name ][ descriptor ]
        return descriptor # TODO: Sanity-check definition.

    @classmethod
    def provide_feature_classes( class_ ):
        ''' Provides language installation feature classes. '''
        return survey_feature_classes( class_.language )

    @classmethod
    def provide_provider_classes( class_ ):
        ''' Provides language installation provider classes. '''
        return survey_provider_classes( class_.language )

    @classmethod
    def summon_records( class_, name ):
        ''' Summons records for language descriptor. '''
        location = class_.infer_records_location( name )
        if not location.exists( ): class_.create_record( name )
        from tomli import load as summon
        with location.open( 'rb' ) as file:
            # TODO: Check format version and update records format,
            #       if necessary.
            records = summon( file )[ 'platforms' ]
        records = {
            platform_name: DictionaryProxy( {
                'implementation-version':
                    class_.language.version_parser(
                        record[ 'implementation-version' ] ),
                'provider': record[ 'provider' ],
            } ) for platform_name, record in records.items( )
        }
        return DictionaryProxy( records )

    @classmethod
    def survey_provider_support( class_, definition, platform = None ):
        ''' Surveys all providers which support language descriptor. '''
        definition = class_.provide_definition( definition )
        provider_classes = class_.provide_provider_classes( )
        supports = [ ]
        for provider_class in provider_classes.values( ):
            if not provider_class.check_descriptor_support(
                definition, platform = platform
            ): continue
            supports.append( provider_class.form_version_record( definition ) )
        return supports

    def __init__( self, name ):
        # TODO: Validate name against definition keys.
        self.name = validate_argument_class( name, str, 'name', self.__init__ )
        self.definition = self._summon_definition( )
        self.record = self._summon_record( )
        self.features = self._instantiate_features( )
        self.providers = self._instantiate_providers( )

    def __str__( self ): return f"{self.language.title} {self.name}"

    def infer_executables_location( self, name = None ):
        ''' Infers installation location for executables.

            If a command name is given, then it is appended to the inferred
            executables location and returned. '''
        for provider in self.providers.values( ):
            location = provider.derive_executables_location( name = name )
            if not location.exists( ):
                __.scribe.debug(
                    f"Could not locate executables for {self} "
                    f"by {provider.name}." )
                continue
            return location
        # TODO: Use exception factory.
        raise LookupError

    def infer_installation_location( self ):
        ''' Infers installation location by provider. '''
        for provider in self.providers.values( ):
            location = provider.installation_location
            if not location.exists( ):
                __.scribe.debug(
                    f"Could not locate installation of {self} "
                    f"by {provider.name}." )
                continue
            return location
        # TODO: Use exception factory.
        raise LookupError

    def install( self, force = False ):
        ''' Installs with provider of record. '''
        provider = self.providers[ self.record[ 'provider' ] ]
        provider.install( force = force )

    def probe_feature_labels( self, labels ):
        ''' Tests if any features of descriptor have specific labels. '''
        if isinstance( labels, str ): labels = ( labels, )
        from itertools import chain
        return frozenset( labels ) & frozenset( chain.from_iterable(
            feature.labels for feature in self.features.values( ) ) )

    def update( self, install = True ):
        ''' Attempts to update with most relevant provider. '''
        status_quo = self.record[ 'implementation-version' ]
        for provider in self.providers.values( ):
            offer = provider.discover_current_version( self.definition )
            if offer < status_quo: continue
            try: record = provider.form_version_record( self )
            except Exception: # pylint: disable=broad-except
                __.scribe.exception(
                    f"Could not update {self.name} by {provider.name}." )
                continue
            if self.record != record:
                self.record = record
                self._update_record( )
                break
        if install: self.install( ) # Ensure installation.
        return self

    def _instantiate_features( self ):
        feature_classes = self.provide_feature_classes( )
        features = { }
        mutex_labels = frozenset( )
        for name in self.definition.get( 'features', ( ) ):
            feature_class = feature_classes[ name ]
            if not feature_class.check_descriptor_support( self.definition ):
                continue
            features[ name ] = feature = feature_class( self )
            # Sanity check for mutually-exclusive features.
            if mutex_labels & feature.mutex_labels:
                # TODO: Use exception factory.
                raise ValueError
            mutex_labels = mutex_labels | frozenset( feature.mutex_labels )
        return DictionaryProxy( features )

    def _instantiate_providers( self ):
        provider_classes = self.provide_provider_classes( )
        providers = { }
        for name in self.definition.get( 'providers', ( ) ):
            provider_class = provider_classes[ name ]
            if not provider_class.check_descriptor_support( self.definition ):
                continue
            providers[ name ] = provider_class( self )
        return DictionaryProxy( providers )

    def _summon_definition( self ):
        return DictionaryProxy(
            _data.definitions[ self.language.name ][ self.name ] )

    def _summon_record( self ):
        records = self.summon_records( self.name )
        platform_name = calculate_platform_identifier( )
        if platform_name not in records: return self.create_record( self.name )
        return records[ platform_name ]

    def _update_record( self ):
        records = dict( self.summon_records( self.name ) )
        records[ calculate_platform_identifier( ) ] = dict( self.record )
        self.persist_records( self.name, records )


# TODO: Class immutability.
class LanguageFeature( metaclass = ABCFactory ):
    ''' Abstract base for language installation features. '''

    labels: _typ.FrozenSet[ str ]
    language: Language
    mutex_labels: _typ.FrozenSet[ str ]
    name: str

    @classmethod
    def check_descriptor_support( class_, descriptor, platform = None ):
        ''' Does feature support language descriptor? '''
        definition = (
            class_.language.descriptor_class.provide_definition( descriptor ) )
        if not class_.is_supportable_platform( platform = platform ):
            return False
        if not class_.is_supportable_base_version(
            definition[ 'base-version' ]
        ): return False
        if not class_.is_supportable_implementation(
            definition[ 'implementation' ]
        ): return False
        return True

    @classmethod
    @abstract
    def is_supportable_base_version( class_, version ):
        ''' Does feature support base version? '''
        raise create_abstract_invocation_error(
            # nosemgrep: python.lang.maintainability.is-function-without-parentheses
            class_.is_supportable_base_version )

    @classmethod
    @abstract
    def is_supportable_implementation( class_, implementation ):
        ''' Does feature support implementation? '''
        raise create_abstract_invocation_error(
            # nosemgrep: python.lang.maintainability.is-function-without-parentheses
            class_.is_supportable_implementation )

    @classmethod
    @abstract
    def is_supportable_platform( class_, platform = None ):
        ''' Does feature support platform? '''
        raise create_abstract_invocation_error(
            # nosemgrep: python.lang.maintainability.is-function-without-parentheses
            class_.is_supportable_platform )

    def __init__( self, descriptor ):
        self.descriptor = validate_argument_class(
            descriptor, LanguageDescriptor, 'descriptor', self.__init__ )

    @abstract
    def modify_installation( self, installation_location ):
        ''' Modifies language installation. '''
        # nosemgrep: python.lang.maintainability.is-function-without-parentheses
        raise create_abstract_invocation_error( self.modify_installation )

    @abstract
    def modify_provider_environment( self, environment ):
        ''' Modifies language installation provider environment. '''
        raise create_abstract_invocation_error(
            # nosemgrep: python.lang.maintainability.is-function-without-parentheses
            self.modify_provider_environment )


# TODO: Class immutability.
class LanguageProvider( metaclass = ABCFactory ):
    ''' Abstract base for language installation providers. '''

    language: Language
    name: str

    @classmethod
    def check_descriptor_support( class_, descriptor, platform = None ):
        ''' Does provider support language descriptor? '''
        definition = (
            class_.language.descriptor_class.provide_definition( descriptor ) )
        if not class_.is_supportable_platform( platform = platform ):
            return False
        if not class_.is_supportable_base_version(
            definition[ 'base-version' ]
        ): return False
        if not class_.is_supportable_implementation(
            definition[ 'implementation' ]
        ): return False
        if not all(
            class_.is_supportable_feature( feature_name )
            for feature_name in definition.get( 'features', ( ) )
        ): return False
        return True

    @classmethod
    @abstract
    def discover_current_version( class_, definition ):
        ''' Discovers latest implementation version for base version. '''
        raise create_abstract_invocation_error(
            class_.discover_current_version )

    @classmethod
    def form_version_record( class_, descriptor, version = None ): # pylint: disable=unused-argument
        ''' Forms version record. '''
        definition = (
            class_.language.descriptor_class.provide_definition( descriptor ) )
        # TODO: Handle version argument.
        return {
            'implementation-version':
                class_.discover_current_version( definition ),
            'provider': class_.name,
        }

    @classmethod
    @abstract
    def is_supportable_base_version( class_, version ):
        ''' Does provider support base version? '''
        raise create_abstract_invocation_error(
            # nosemgrep: python.lang.maintainability.is-function-without-parentheses
            class_.is_supportable_base_version )

    @classmethod
    @abstract
    def is_supportable_feature( class_, feature ):
        ''' Does provider support feature? '''
        # nosemgrep: python.lang.maintainability.is-function-without-parentheses
        raise create_abstract_invocation_error( class_.is_supportable_feature )

    @classmethod
    @abstract
    def is_supportable_implementation( class_, implementation ):
        ''' Does provider support implementation? '''
        raise create_abstract_invocation_error(
            # nosemgrep: python.lang.maintainability.is-function-without-parentheses
            class_.is_supportable_implementation )

    @classmethod
    @abstract
    def is_supportable_platform( class_, platform = None ):
        ''' Does provider support platform? '''
        raise create_abstract_invocation_error(
            # nosemgrep: python.lang.maintainability.is-function-without-parentheses
            class_.is_supportable_platform )

    def __init__( self, descriptor ):
        self.descriptor = validate_argument_class(
            descriptor, LanguageDescriptor, 'descriptor', self.__init__ )
        self.installation_name = self.calculate_installation_name( )
        self.installation_location = self.calculate_installation_location( )
        # TODO: Assert viability of features + implementation + platform.

    def calculate_installation_location( self ):
        ''' Calculates installation location from various factors. '''
        from ..data import user_directories
        return user_directories.installations.joinpath(
            self.language.name, self.name, self.installation_name )

    def calculate_installation_name( self ):
        ''' Calculates installation name from version and platform. '''
        definition = self.descriptor.definition
        feature_names = '+'.join( self.descriptor.features.keys( ) )
        # TODO? Calculate with relevant C library or language VM name.
        return '--'.join( filter( None, (
            "{implementation}-{base_version}".format(
                implementation = definition[ 'implementation' ],
                base_version = definition[ 'base-version' ] ),
            str( self.descriptor.record[ 'implementation-version' ] ),
            feature_names,
            calculate_platform_identifier( ) ) ) )

    @abstract
    def derive_executables_location( self, name = None ):
        ''' Derives location of executables for language installation.

            If name argument is given, then that is processed and appended to
            the executables location to result in the location of a particular
            executable within the installation. '''
        raise create_abstract_invocation_error(
            self.derive_executables_location )

    @abstract
    def install( self ):
        ''' Installs version of language. '''
        raise create_abstract_invocation_error( self.install )


def _validate_feature_class( class_ ):
    from inspect import isclass as is_class
    if not is_class( class_ ) or not issubclass( class_, LanguageFeature ):
        raise create_argument_validation_error(
            'class_', _validate_feature_class,
            "sublcass of class 'LanguageFeature'" )
    return class_


def _validate_language( language ):
    if not isinstance( language, Language ):
        raise create_argument_validation_error(
            'language', _validate_language, "instance of class 'Language'" )
    return language


def _validate_provider_class( class_ ):
    from inspect import isclass as is_class
    if not is_class( class_ ) or not issubclass( class_, LanguageProvider ):
        raise create_argument_validation_error(
            'class_', _validate_provider_class,
            "subclass of class 'LanguageProvider'" )
    return class_


def _create_registration_interface( ): # pylint: disable=too-complex
    from ..base import create_accretive_dictionary
    languages = create_accretive_dictionary( _validate_language )
    feature_classes = create_accretive_dictionary( lambda object_: object_ )
    provider_classes = create_accretive_dictionary( lambda object_: object_ )

    def register_feature_class_( feature_class ):
        ''' Registers language installation feature class. '''
        _validate_feature_class( feature_class )
        language_name = _validate_language( feature_class.language ).name
        if language_name not in languages:
            # TODO: Use exception factory.
            raise ValueError
        feature_name = feature_class.name
        feature_classes[ language_name ][ feature_name ] = feature_class

    def register_language_(
        language,
        feature_class_validator = _validate_feature_class,
        provider_class_validator = _validate_provider_class,
    ):
        ''' Registers language. '''
        # TODO: Validate the validators. ;)
        # TODO: Wrap custom validators with default validators for extra
        #       safety.
        name = _validate_language( language ).name
        languages[ name ] = language
        feature_classes[ name ] = create_accretive_dictionary(
            feature_class_validator )
        provider_classes[ name ] = create_accretive_dictionary(
            provider_class_validator )

    def register_provider_class_( provider_class ):
        ''' Registers language installation provider class. '''
        _validate_provider_class( provider_class )
        language_name = _validate_language( provider_class.language ).name
        if language_name not in languages:
            # TODO: Use exception factory.
            raise ValueError
        provider_name = provider_class.name
        provider_classes[ language_name ][ provider_name ] = provider_class

    def survey_feature_classes_( language ):
        ''' Returns immutable view upon features registry for language. '''
        if isinstance( language, Language ): language = language.name
        return feature_classes[ language ]

    def survey_languages_( ):
        ''' Returns immutable view upon languages registry. '''
        return languages

    def survey_provider_classes_( language ):
        ''' Returns immutable view upon providers registry for language. '''
        if isinstance( language, Language ): language = language.name
        return provider_classes[ language ]

    return (
        register_language_,
        register_feature_class_, register_provider_class_,
        survey_languages_,
        survey_feature_classes_, survey_provider_classes_ )

( register_language, register_feature_class, register_provider_class,
  survey_languages, survey_feature_classes, survey_provider_classes ) = (
      _create_registration_interface( ) )


def _calculate_locations( ):
    from ..data import locations as base_locations
    return create_immutable_namespace( dict(
        configuration = base_locations.configuration.DEV.SELF / 'languages',
        data = base_locations.data.DEV.SELF / 'languages',
    ) )


def _summon_definitions( name ):
    ''' Summons definitions for language descriptors. '''
    # TODO? Use 'importlib-resources' to access default definitions.
    location = _data.locations.configuration / f"{name}.toml"
    from tomli import load as summon
    with location.open( 'rb' ) as file: document = summon( file )
    # TODO: Check format version and dispatch accordingly.
    return DictionaryProxy( document.get( 'descriptors', { } ) )


_data = create_semelfactive_namespace( create_invocable_dictionary(
    definitions = (
        lambda: create_semelfactive_dictionary( _summon_definitions ) ),
    locations = _calculate_locations,
) )
__getattr__ = _data.__getattr__


reclassify_module( __name__ )
