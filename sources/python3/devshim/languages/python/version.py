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


''' Python versions to install. '''


from . import base as __


class LanguageVersion( __.LanguageVersion ):
    ''' Abstract base for Python language versions. '''

    def __init__( self, name ): super( ).__init__( 'Python', name )

    @classmethod
    def provide_feature_class( class_, name ):
        # TODO: Implement.
        raise NotImplementedError

    @classmethod
    def provide_provider_class( class_, name ):
        from .data import provider_classes
        return provider_classes[ name ]

    @classmethod
    def summon_definitions( class_ ):
        from .data import version_definitions
        return version_definitions

    @classmethod
    def summon_records( class_ ):
        from ...packages import ensure_import_package
        tomllib = ensure_import_package( 'tomllib' )
        from .data import locations
        records_location = locations.version_records
        if not records_location.exists( ): class_._create_records( )
        # TODO: Check format version and dispatch accordingly.
        with records_location.open( 'rb' ) as file:
            return tomllib.load( file )[ 'versions' ]

    @classmethod
    def _create_records( class_ ):
        from .data import version_definitions
        document = { 'format-version': 1, 'versions': { } }
        for name, definition in version_definitions.items( ):
            # TODO: Sort records by version descending.
            record = next( iter( class_.survey_provider_support(
                definition ) ) )
            document[ 'versions' ][ name ] = record
        _commit_version_records( document )
        return class_

    @classmethod
    def survey_provider_support( class_, definition ):
        from .data import provider_classes
        supports = [ ]
        for provider_class in provider_classes.values( ):
            if not provider_class.check_version_support( definition ): continue
            supports.append( {
                'implementation-version':
                    provider_class.discover_current_version( definition ),
                'provider': provider_class.name,
            } )
        return supports

    def install( self ):
        ''' Installs version with provider of record. '''
        provider = self.providers[ self.record[ 'provider' ] ]
        provider.install( )

    def update( self, install = True ):
        ''' Attempts to update version with most relevant provider. '''
        from ...base import scribe
        implementation_version = tuple( map(
            int, self.record[ 'implementation-version' ].split( '.' ) ) )
        for provider in self.providers.values( ):
            current_implementation_version = tuple( map(
                int,
                provider.discover_current_version(
                    self.definition ).split( '.' )
            ) )
            if current_implementation_version <= implementation_version:
                continue
            try: record = provider.generate_current_version_record( self )
            except Exception: # pylint: disable=broad-except
                scribe.exception(
                    f"Could not update {self.name} by {provider.name}." )
                continue
            if self.record != record:
                self.record = record
                self._update( )
                break
        if install: self.install( ) # Ensure installation.
        return self

    def _update( self ):
        from ...packages import ensure_import_package
        tomllib = ensure_import_package( 'tomllib' )
        # TODO: Check format version and dispatch accordingly.
        from .data import locations
        with locations.version_records.open( 'rb' ) as file:
            document = tomllib.load( file )
        document[ 'versions' ][ self.name ] = self.record
        _commit_version_records( document )


def _commit_version_records( document ):
    from ...packages import ensure_import_package
    tomli_w = ensure_import_package( 'tomli-w' )
    from .data import locations
    records_location = locations.version_records
    records_location.parent.mkdir( exist_ok = True, parents = True )
    with records_location.open( 'wb' ) as file:
        # TODO: Write comment header to warn about machine-generated code.
        tomli_w.dump( document, file )
