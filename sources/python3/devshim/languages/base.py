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
from types import (
    MappingProxyType as DictionaryProxy,
    SimpleNamespace,
)

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
        for version, definition in definitions.items( ): # pylint: disable=unused-variable
            # TODO: Consider explicit platform constraints.
            # TODO: Offload entirety of support check to version class.
            #supports = version_class.survey_provider_support( definition )
            #if not supports: continue
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

    def __init__( self, name ):
        # TODO: Validate version against defined versions.
        self.name = validate_argument_class(
            name, str, 'name', self.__init__ )
        self.definition = self._summon_definition( )
        self.record = self._summon_record( )
        self.features = self._instantiate_features( )
        self.providers = self._instantiate_providers( )

    @classmethod
    @abstract
    def create_record( class_, name ):
        ''' Creates record for language version. '''
        raise create_abstract_invocation_error( class_.create_record )

    @classmethod
    @abstract
    def provide_feature_class( class_, name ):
        ''' Provides language installation feature class by name. '''
        raise create_abstract_invocation_error( class_.provide_feature_class )

    @classmethod
    @abstract
    def provide_provider_class( class_, name ):
        ''' Provides language version provider class by name. '''
        raise create_abstract_invocation_error( class_.provide_provider_class )

    @classmethod
    @abstract
    def summon_definitions( class_ ):
        ''' Summons definitions for language versions. '''
        raise create_abstract_invocation_error( class_.summon_definitions )

    @classmethod
    @abstract
    def summon_records( class_ ):
        ''' Summons records for language versions. '''
        raise create_abstract_invocation_error( class_.summon_records )

    @classmethod
    @abstract
    def survey_provider_support( class_, definition ):
        ''' Surveys all providers which support language version. '''
        raise create_abstract_invocation_error(
            class_.survey_provider_support )

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
        from ..base import scribe
        for provider in self.providers.values( ):
            location = provider.installation_location
            if not location.exists( ):
                scribe.debug(
                    f"Could not locate installation of {self} "
                    f"by {provider.name}." )
                continue
            return location
        # TODO: Use exception factory.
        raise LookupError

    def probe_feature_labels( self, labels ):
        ''' Tests if any features of version have specific labels. '''
        if isinstance( labels, str ): labels = ( labels, )
        from itertools import chain
        return frozenset( labels ) & frozenset( chain.from_iterable(
            feature.labels for feature in self.features.values( ) ) )

    def _instantiate_features( self ):
        features = { }
        mutex_labels = frozenset( )
        for name in self.definition.get( 'features', ( ) ):
            feature = self.provide_feature_class( name )( self )
            features[ name ] = feature
            # Sanity check for mutually-exclusive features.
            if mutex_labels & feature.mutex_labels:
                # TODO: Use exception factory.
                raise ValueError
            mutex_labels = mutex_labels | frozenset( feature.mutex_labels )
        return DictionaryProxy( features )

    def _instantiate_providers( self ):
        providers = { }
        for name in self.definition.get( 'providers', ( ) ):
            providers[ name ] = self.provide_provider_class( name )( self )
        return DictionaryProxy( providers )

    def _summon_definition( self ):
        return DictionaryProxy( self.summon_definitions( )[ self.name ] )

    def _summon_record( self ):
        name = self.name
        records = self.summon_records( )
        if name not in records: record = self.create_record( name )
        else: record = records[ name ]
        return DictionaryProxy( record )


# TODO: Class immutability.
class LanguageFeature( metaclass = ABCFactory ):
    ''' Abstract base for language installation features. '''

    name: str
    labels: _typ.FrozenSet[ str ]
    mutex_labels: _typ.FrozenSet[ str ]

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

    name: str

    @classmethod
    def check_version_support( class_, version ):
        ''' Does provider support version? '''
        if isinstance( version, LanguageVersion ):
            definition = version.definition
        else: definition = version
        feature_names = definition.get( 'features', ( ) )
        #if not class_.is_supportable_platform( ): continue
        if not class_.is_supportable_base_version(
            definition[ 'base-version' ]
        ): return False
        if not class_.is_supportable_implementation(
            definition[ 'implementation' ]
        ): return False
        if not all(
            class_.is_supportable_feature( feature_name )
            for feature_name in feature_names
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
