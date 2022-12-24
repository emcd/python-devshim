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


# pylint: disable=unused-import
from abc import ABCMeta as ABCFactory, abstractmethod as abstract_function
from types import (
    MappingProxyType as DictionaryProxy,
    SimpleNamespace,
)
# pylint: enable=unused-import

from .. import base as __


# TODO: Class immutability.
class LanguageVersion( metaclass = ABCFactory ):
    ''' Abstract base for language versions. '''

    def __init__( self, language, name ):
        # TODO: Validate arguments.
        self.language = language
        self.name = name
        self.definition = self._summon_definition( )
        self.record = self._summon_record( )
        self.features = self._instantiate_features( )
        self.providers = self._instantiate_providers( )

    def __str__( self ): return f"{self.language} {self.name}"

    @classmethod
    @abstract_function
    def provide_feature_class( class_, name ):
        ''' Provides language installation feature class by name. '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @classmethod
    @abstract_function
    def provide_provider_class( class_, name ):
        ''' Provides language version provider class by name. '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @classmethod
    @abstract_function
    def summon_definitions( class_ ):
        ''' Summons definitions for language versions. '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @classmethod
    @abstract_function
    def summon_records( class_ ):
        ''' Summons records for language versions. '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @classmethod
    @abstract_function
    def survey_provider_support( class_, definition ):
        ''' Surveys all providers which support language version. '''
        # TODO: Use exception factory.
        raise NotImplementedError

    def _instantiate_features( self ):
        features = { }
        for name in self.definition.get( 'features', ( ) ):
            features[ name ] = self.provide_feature_class( name )( self )
        return DictionaryProxy( features )

    def _instantiate_providers( self ):
        providers = { }
        for name in self.definition.get( 'providers', ( ) ):
            providers[ name ] = self.provide_provider_class( name )( self )
        return DictionaryProxy( providers )

    def _summon_definition( self ):
        return DictionaryProxy( self.summon_definitions( )[ self.name ] )

    def _summon_record( self ):
        return DictionaryProxy( self.summon_records( )[ self.name ] )


# TODO: Class immutability.
class LanguageFeature( metaclass = ABCFactory ):
    ''' Abstract base for language installation features. '''

    def __init__( self, version ): self.version = version

    @abstract_function
    def modify_installation( self, installation_location ):
        ''' Modifies language version installation. '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @abstract_function
    def modify_provider_environment( self, environment ):
        ''' Modifies language version provider environment. '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @classmethod
    @abstract_function
    def is_supportable_base_version( class_, version ):
        ''' Does feature support base version? '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @classmethod
    @abstract_function
    def is_supportable_implementation( class_, implementation ):
        ''' Does feature support implementation? '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @classmethod
    @abstract_function
    def is_supportable_platform( class_, platform = None ):
        ''' Does feature support platform? '''
        # TODO: Use exception factory.
        raise NotImplementedError


# TODO: Class immutability.
class LanguageProvider( metaclass = ABCFactory ):
    ''' Abstract base for language version providers. '''

    @classmethod
    def check_version_support( class_, definition ):
        ''' Does provider support version? '''
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
    @abstract_function
    def discover_current_version( class_, definition ):
        ''' Discovers latest implementation version for base version. '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @classmethod
    @abstract_function
    def is_supportable_base_version( class_, version ):
        ''' Does provider support base version? '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @classmethod
    @abstract_function
    def is_supportable_feature( class_, feature ):
        ''' Does provider support feature? '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @classmethod
    @abstract_function
    def is_supportable_implementation( class_, implementation ):
        ''' Does provider support implementation? '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @classmethod
    @abstract_function
    def is_supportable_platform( class_, platform = None ):
        ''' Does provider support platform? '''
        # TODO: Use exception factory.
        raise NotImplementedError

    # TODO: Validate argument.
    def __init__( self, version ): self.version = version

    @abstract_function
    def install( self ):
        ''' Installs version of language. '''
        # TODO: Use exception factory.
        raise NotImplementedError

    @abstract_function
    def attempt_version_data_update( self ):
        ''' Attempts to update version data for version of language. '''
        # TODO: Use exception factory.
        raise NotImplementedError


def _calculate_locations( ):
    from ..data import locations
    return __.create_immutable_namespace( dict(
        configuration = locations.configuration.DEV.SELF / 'languages',
        state = locations.state.DEV.SELF / 'languages',
    ) )


def _produce_calculators( ):
    return dict(
        locations = _calculate_locations,
    )

data = __.produce_accretive_cacher( _produce_calculators )
