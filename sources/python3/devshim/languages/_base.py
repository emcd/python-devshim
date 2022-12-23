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


from abc import ABCMeta as ABCFactory, abstractmethod as abstract_function
from types import MappingProxyType as DictionaryProxy


# TODO: Class immutability.
class LanguageVersion( metaclass = ABCFactory ):
    ''' Abstract base for language versions. '''

    def __init__( self, language, name ):
        # TODO: Validate arguments.
        self.language = language
        self.name = name
        self.definition = self._summon_definition( )
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
