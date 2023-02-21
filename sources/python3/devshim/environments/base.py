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


''' Utilities for management of environments. '''


from os import environ as current_process_environment
from types import MappingProxyType as DictionaryProxy

from ..base import (
    create_immutable_namespace,
    create_invocable_dictionary,
    create_semelfactive_namespace,
)
from ..exceptionality import (
    create_data_validation_error,
    validate_argument_class,
)


# TODO: Class immutability.
class Environment:
    ''' Manager for environment. '''

    @classmethod
    def is_supportable( class_, definition, platform = None ):
        ''' Is environment supportable by all of its language descriptors.

            If platform is not supplied, then current platform is assumed. '''
        descriptors = definition[ 'language-descriptors' ]
        from ..languages import survey_languages
        languages = survey_languages( )
        for language_name, descriptor_name in descriptors.items( ):
            # TODO: Handle case of absent language.
            language = languages[ language_name ]
            if not language.descriptor_class.is_supportable(
                descriptor_name, platform = platform
            ): return False
        return True

    def __init__( self, name ):
        # TODO: Validate name against definition keys.
        self.name = validate_argument_class( name, str, 'name', self.__init__ )
        self.definition = self._summon_definition( )

    def __str__( self ): return self.name

    def _summon_definition( self ):
        return DictionaryProxy( _data.definitions[ self.name ] )


def survey_descriptors( ):
    ''' Returns environment descriptors which have relevant definitions. '''
    definitions = _data.definitions
    from ..base import derive_environment_entry_name
    descriptor = current_process_environment.get(
        derive_environment_entry_name( 'environment', 'descriptor' ) )
    if None is not descriptor:
        if descriptor in definitions:
            definitions = { descriptor: definitions[ descriptor ] }
        else:
            raise create_data_validation_error(
                f"No descriptor {descriptor!r} in environment definitions." )
    descriptors = { }
    for descriptor, definition in definitions.items( ):
        if not Environment.is_supportable( definition ): continue
        descriptors[ descriptor ] = Environment( descriptor )
    return DictionaryProxy( descriptors )


def _calculate_locations( ):
    from ..data import locations as base_locations
    return create_immutable_namespace( dict(
        configuration = base_locations.configuration.DEV.SELF,
        data = base_locations.data.DEV.SELF,
    ) )


def _summon_definitions( ):
    ''' Summons definitions for environment decriptors. '''
    # TODO? Use 'importlib-resources' to access default definitions.
    location = _data.locations.configuration / 'environments.toml'
    from tomli import load as summon
    with location.open( 'rb' ) as file: document = summon( file )
    # TODO: Check format version and dispatch accordingly.
    return DictionaryProxy( document.get( 'descriptors', { } ) )


_data = create_semelfactive_namespace( create_invocable_dictionary(
    definitions = _summon_definitions,
    locations = _calculate_locations,
) )
__getattr__ = _data.__getattr__
