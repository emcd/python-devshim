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

from .. import base as __
from ..base import (
    create_immutable_namespace,
    module_introduce_accretive_cache,
)
from ..exceptions import (
    create_abstract_invocation_error,
    create_argument_validation_error,
    create_data_validation_error,
    validate_argument_class,
)
# pylint: enable=unused-import


# Note: Need to explicitly declare __getattr__-synthesized module attributes
#       to avoid issues with MyPy and Pylint.
locations: _typ.Any


class Language( metaclass = ABCFactory ):
    ''' Abstract base for languages. '''
    # Note: The 'Language' class is effectively a singleton. We would use a
    #       module rather than a class, except for the fact that we want
    #       to guarantee a common interface and provide some standard behaviors
    #       behind portions of that interface. Only class-level attributes
    #       should appear on this class and its descendants.

    name: str
    title: str

    @classmethod
    def calculate_version_selector_name( class_ ):
        ''' Calculates name of environment variable for language version. '''
        return "{package_name}_{language_name}_VERSION".format(
            package_name = __.__package__.upper( ),
            language_name = class_.name.upper( ) )

    @classmethod
    def detect_default_version( class_ ):
        ''' Detects default language version.

            If in a virtual environment, then the language version for that
            environment is returned. Else, the first available language version
            from the project version definitions is returned. '''
        # TODO: Detect if in relevant virtual environment and infer version.
        return next( iter( class_.survey_versions( ).values( ) ) )

    @classmethod
    def produce_version( class_, version = None ):
        ''' Produces instance of language version manager. '''
        if None is version: return class_.detect_default_version( )
        return class_.provide_version_class( )( version )

    @classmethod
    @abstract
    def provide_version_class( class_ ):
        ''' Provides version class associated with language. '''
        raise create_abstract_invocation_error( class_.provide_version_class )

    @classmethod
    def survey_versions( class_ ):
        ''' Returns language versions which have relevant definitions. '''
        version_class = class_.provide_version_class( )
        definitions = version_class.summon_definitions( )
        from os import environ as current_process_environment
        version = current_process_environment.get(
            class_.calculate_version_selector_name( ) )
        if None is not version:
            if version in definitions:
                definitions = { version: definitions[ version ] }
            else:
                raise create_data_validation_error(
                    f"No version {version!r} in definitions "
                    f"for language {class_.title}." )
        versions = { }
        for version, definition in definitions.items( ):
            if not version_class.is_supportable( definition ): continue
            versions[ version ] = version_class( version )
        return DictionaryProxy( versions )

    @classmethod
    def validate_version( class_, version ):
        ''' Validates version against available language versions. '''
        if version not in class_.survey_versions( ):
            raise create_argument_validation_error(
                'version', class_.validate_version,
                f"defined {class_.title} version" )
        return version

    # TODO: Either prevent instantiation or else use the Borg pattern.


# TODO: Class immutability.
class LanguageVersion( metaclass = ABCFactory ):
    ''' Abstract base for language versions. '''

    language: _typ.Type[ Language ]

    @classmethod
    def create_record( class_, name ):
        ''' Creates languge version record and persists it. '''
        definitions = class_.summon_definitions( )
        versions = dict( class_.summon_records( ) )
        definition = definitions[ name ]
        # TODO: Sort records by version descending.
        record = next( iter( class_.survey_provider_support( definition ) ) )
        versions[ name ] = record
        class_.persist_records( versions )
        return record

    @classmethod
    def create_records( class_ ):
        ''' Creates language version records and persists them. '''
        definitions = class_.summon_definitions( )
        versions = { }
        for name, definition in definitions.items( ):
            # TODO: Sort records by version descending.
            record = next( iter( class_.survey_provider_support(
                definition ) ) )
            versions[ name ] = record
        class_.persist_records( versions )
        return class_

    @classmethod
    def extract_definition( class_, version ):
        ''' Extracts definition from version if necessary. '''
        if isinstance( version, LanguageVersion ): return version.definition
        if isinstance( version, str ):
            return class_.summon_definitions( )[ version ]
        return version # TODO: Sanity-check definition.

    @classmethod
    def is_supportable( class_, definition, platform = None ):
        ''' Is language version supportable on platform with its providers? '''
        definition = class_.extract_definition( definition )
        # TODO: Consider explicit platform constraints.
        supports = class_.survey_provider_support(
            definition, platform = platform )
        if not supports: return False
        return True

    @classmethod
    def persist_records( class_, versions ):
        ''' Persists language version records to data store. '''
        from ..packages import ensure_import_package
        tomli_w = ensure_import_package( 'tomli-w' )
        location = class_.provide_records_location( )
        location.parent.mkdir( exist_ok = True, parents = True )
        document = { 'format-version': 1, 'versions': dict( versions ) }
        with location.open( 'wb' ) as file:
            # TODO: Write comment header to warn about machine-generated code.
            tomli_w.dump( document, file )

    @classmethod
    def provide_feature_classes_registry( class_ ):
        ''' Provides language installation feature classes registry. '''
        return survey_feature_classes( class_.language )

    @classmethod
    def provide_provider_classes_registry( class_ ):
        ''' Provides language version provider classes registry. '''
        return survey_provider_classes( class_.language )

    @classmethod
    @abstract
    def provide_records_location( class_ ):
        ''' Provides location of language version records. '''
        raise create_abstract_invocation_error(
            class_.provide_records_location )

    @classmethod
    @abstract
    def summon_definitions( class_ ):
        ''' Summons definitions for language versions. '''
        raise create_abstract_invocation_error( class_.summon_definitions )

    @classmethod
    def summon_records( class_ ):
        ''' Summons records for language versions. '''
        location = class_.provide_records_location( )
        if not location.exists( ): class_.create_records( )
        from ..packages import ensure_import_package
        tomllib = ensure_import_package( 'tomllib' )
        with location.open( 'rb' ) as file:
            # TODO: Check format version and update records format,
            #       if necessary.
            return DictionaryProxy( tomllib.load( file )[ 'versions' ] )

    @classmethod
    def survey_provider_support( class_, definition, platform = None ):
        ''' Surveys all providers which support language version. '''
        # TODO: Extract definition if version provided.
        provider_classes_registry = class_.provide_provider_classes_registry( )
        supports = [ ]
        for provider_class in provider_classes_registry.values( ):
            if not provider_class.check_version_support(
                definition, platform = platform
            ): continue
            supports.append( {
                'implementation-version':
                    provider_class.discover_current_version( definition ),
                'provider': provider_class.name,
            } )
        return supports

    def __init__( self, name ):
        # TODO: Validate version against defined versions.
        self.name = validate_argument_class(
            name, str, 'name', self.__init__ )
        self.definition = self._summon_definition( )
        self.record = self._summon_record( )
        self.features = self._instantiate_features( )
        self.providers = self._instantiate_providers( )

    def __str__( self ): return f"{self.language.title} {self.name}"

    def infer_executable_location( self, name = None ):
        ''' Infers executables location for language by version.

            If a command name is given, then it is appended to the inferred
            executables location and returned. '''
        location = self.infer_installation_location( ) / 'bin'
        if None is not name: return location / name
        return location

    def infer_installation_location( self ):
        ''' Infers installation location for language by version. '''
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

    def install( self ):
        ''' Installs version with provider of record. '''
        provider = self.providers[ self.record[ 'provider' ] ]
        provider.install( )

    def probe_feature_labels( self, labels ):
        ''' Tests if any features of version have specific labels. '''
        if isinstance( labels, str ): labels = ( labels, )
        from itertools import chain
        return frozenset( labels ) & frozenset( chain.from_iterable(
            feature.labels for feature in self.features.values( ) ) )

    def update( self, install = True ):
        ''' Attempts to update version with most relevant provider. '''
        implementation_version = self.record[ 'implementation-version' ]
        for provider in self.providers.values( ):
            implementation_version_ = (
                provider.discover_current_version( self.definition ) )
            if 0 > compare_version(
                implementation_version_, implementation_version
            ): continue
            try: record = provider.generate_current_version_record( self )
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
        feature_classes_registry = self.provide_feature_classes_registry( )
        features = { }
        mutex_labels = frozenset( )
        for name in self.definition.get( 'features', ( ) ):
            feature = feature_classes_registry[ name ]( self )
            features[ name ] = feature
            # Sanity check for mutually-exclusive features.
            if mutex_labels & feature.mutex_labels:
                # TODO: Use exception factory.
                raise ValueError
            mutex_labels = mutex_labels | frozenset( feature.mutex_labels )
        return DictionaryProxy( features )

    def _instantiate_providers( self ):
        provider_classes_registry = self.provide_provider_classes_registry( )
        providers = { }
        for name in self.definition.get( 'providers', ( ) ):
            providers[ name ] = provider_classes_registry[ name ]( self )
        return DictionaryProxy( providers )

    def _summon_definition( self ):
        return DictionaryProxy( self.summon_definitions( )[ self.name ] )

    def _summon_record( self ):
        name = self.name
        records = self.summon_records( )
        if name not in records: record = self.create_record( name )
        else: record = records[ name ]
        return DictionaryProxy( record )

    def _update_record( self ):
        versions = self.summon_records( )
        versions[ self.name ] = self.record
        self.persist_records( versions )


# TODO: Class immutability.
class LanguageFeature( metaclass = ABCFactory ):
    ''' Abstract base for language installation features. '''

    labels: _typ.FrozenSet[ str ]
    language: _typ.Type[ Language ]
    mutex_labels: _typ.FrozenSet[ str ]
    name: str

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

    def __init__( self, version ):
        self.version = validate_argument_class(
            version, LanguageVersion, 'version', self.__init__ )

    @abstract
    def modify_installation( self, installation_location ):
        ''' Modifies language version installation. '''
        # nosemgrep: python.lang.maintainability.is-function-without-parentheses
        raise create_abstract_invocation_error( self.modify_installation )

    @abstract
    def modify_provider_environment( self, environment ):
        ''' Modifies language version provider environment. '''
        raise create_abstract_invocation_error(
            # nosemgrep: python.lang.maintainability.is-function-without-parentheses
            self.modify_provider_environment )


# TODO: Class immutability.
class LanguageProvider( metaclass = ABCFactory ):
    ''' Abstract base for language version providers. '''

    language: _typ.Type[ Language ]
    name: str

    @classmethod
    def check_version_support( class_, version, platform = None ):
        ''' Does provider support version? '''
        definition = (
            class_.language.provide_version_class( )
            .extract_definition( version ) )
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
    def generate_current_version_record( class_, version ):
        ''' Detects latest Python version and returns version record. '''
        if isinstance( version, LanguageVersion ):
            definition = version.definition
        else: definition = version
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

    def __init__( self, version ):
        self.version = validate_argument_class(
            version, LanguageVersion, 'version', self.__init__ )

    @abstract
    def install( self ):
        ''' Installs version of language. '''
        raise create_abstract_invocation_error( self.install )


# TODO: Hoist into package base.
def compare_version( left, right, parser = None ):
    ''' Properly compares two version strings.

        I.e., 3.10 < 3.7 if comparison is lexicographic.
        But, 3.10 > 3.7 with this version comparison.

        If left > right, then returns 1.
        If left == right, then returns 0.
        If left < right, then returns -1. '''
    if None is parser:
        # TODO: Account for non-integer components.
        left = tuple( map( int, left.split( '.' ) ) )
        right = tuple( map( int, right.split( '.' ) ) )
    else:
        left = parser( left )
        right = parser( right )
    if left == right: return 0
    return 1 if left > right else -1


def _validate_feature_class( class_ ):
    from inspect import isclass as is_class
    if not is_class( class_ ) or not issubclass( class_, LanguageFeature ):
        raise create_argument_validation_error(
            'class_', _validate_feature_class,
            "sublcass of class 'LanguageFeature'" )
    return class_


def _validate_language( language ):
    from inspect import isclass as is_class
    if not is_class( language ) or not issubclass( language, Language ):
        raise create_argument_validation_error(
            'language', _validate_language,
            "subclass of class 'Language'" )
    return language


def _validate_provider_class( class_ ):
    from inspect import isclass as is_class
    if not is_class( class_ ) or not issubclass( class_, LanguageProvider ):
        raise create_argument_validation_error(
            'class_', _validate_provider_class,
            "subclass of class 'LanguageProvider'" )
    return class_


def _create_registration_interface( ): # pylint: disable=too-complex
    from ..base import create_registrar
    languages = create_registrar( _validate_language )
    feature_classes = create_registrar( lambda object_: object_ )
    provider_classes = create_registrar( lambda object_: object_ )

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
        feature_classes[ name ] = create_registrar( feature_class_validator )
        provider_classes[ name ] = create_registrar( provider_class_validator )

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
        if issubclass( language, Language ): language = language.name
        return feature_classes[ language ].survey_registry( )

    def survey_languages_( ):
        ''' Returns immutable view upon languages registry. '''
        return languages.survey_registry( )

    def survey_provider_classes_( language ):
        ''' Returns immutable view upon providers registry for language. '''
        if issubclass( language, Language ): language = language.name
        return provider_classes[ language ].survey_registry( )

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


def _provide_calculators( ):
    return dict(
        locations = _calculate_locations,
    )

__getattr__ = __.module_introduce_accretive_cache( _provide_calculators )
