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


''' Management of Python versions from Windows embeddable archives.'''


from . import base as __


supportable_features = ( 'cindervm', 'pyston-lite', )

class LanguageProvider( __.LanguageProvider ):
    ''' Works with official Windows embeddable archives from python.org.

        References:

        * https://docs.python.org/3/using/windows.html#the-embeddable-package
        * https://www.python.org/downloads/windows/
        * https://www.python.org/ftp/python/ '''

    language = __.Language
    name = 'windows-embeddable'

    @classmethod
    def discover_current_version( class_, definition ):
        # TODO: Validate version definition.
        versions = _summon_versions( )
        base_version = class_.language.derive_actual_version(
            definition [ 'base-version' ] )
        from ....platforms.identity import extract_cpu_identifier
        cpu = extract_cpu_identifier( )
        current_version = base_version
        # TODO: Filter prerelease versions by default, but allow override.
        for version, data in versions.items( ):
            # Note: Assumes that user wants 64-bit Python on AMD64.
            if cpu not in data: continue
            if current_version > version: continue
            if base_version.major < version.major: continue
            if base_version.minor < version.minor: continue
            current_version = version
        return current_version

    @classmethod
    def is_supportable_base_version( class_, version ):
        version = class_.language.derive_actual_version( version )
        return _data.supportable_base_version <= version

    @classmethod
    def is_supportable_feature( class_, feature ):
        return feature in supportable_features

    @classmethod
    def is_supportable_implementation( class_, implementation ):
        return 'cpython' == implementation

    @classmethod
    def is_supportable_platform( class_, platform = None ):
        if None is platform:
            from ....platforms.identity import extract_os_class
            platform = extract_os_class( )
        return 'nt' == platform

    def derive_executables_location( self, name = None ):
        if name in ( 'python', 'python.exe' ):
            return self.installation_location / 'python.exe'
        if name in ( 'pythonw', 'pythonw.exe' ):
            return self.installation_location / 'pythonw.exe'
        location = self.installation_location / 'Scripts'
        if None is not name: return location / name
        return location

    def install( self, force = False ):
        ''' Installs Windows embeddable archive from python.org. '''
        installation_location = self.installation_location
        if not force and installation_location.exists( ): return self
        from ....platforms.identity import extract_cpu_identifier
        cpu = extract_cpu_identifier( )
        href = _summon_versions( )[
            self.descriptor.record[ 'implementation-version' ] ][ cpu ]
        archive_location = _retrieve_archive( href )
        from zipfile import ZipFile
        with ZipFile( archive_location ) as zipfile:
            zipfile.extractall( path = installation_location )
        self._execute_post_installation_activities( )
        return self

    def _ensure_site_packages( self ):
        installation_location = self.installation_location
        python_pth_location = next(
            installation_location.glob( 'python*._pth' ) )
        python_stdlib_location = next(
            installation_location.glob( 'python*.zip' ) )
        with python_pth_location.open( 'w' ) as file:
            file.write( _python_pth_template.format(
                stdlib = python_stdlib_location.name ) )
        python_location = installation_location / 'python.exe'
        __.ensure_site_packages( installation_location, python_location )

    def _execute_post_installation_activities( self ):
        self._ensure_site_packages( )
        # Per-feature activities, such as site customization.
        for feature in self.descriptor.features.values( ):
            feature.modify_installation( self.installation_location )

__.register_provider_class( LanguageProvider )


_python_pth_template = '''
{stdlib}
.

import site
'''


def _retrieve_archive( href ):
    archive_name = href.rsplit( '/', maxsplit = 1 )[ -1 ]
    archive_location = _data.locations.archives / archive_name
    archive_location.parent.mkdir( exist_ok = True, parents = True )
    if archive_location.exists( ) and _verify_archive( archive_location ):
        return archive_location
    __.http_retrieve_url( href, archive_location )
    # TODO: Verify archive and raise error on failed verification.
    return archive_location


def _verify_archive( location ):
    from zipfile import ZipFile
    with ZipFile( location ) as zipfile:
        # TODO? Find alternative archive verification is too costly.
        # TODO: Log info message about archive verification operation.
        return None is zipfile.testzip( )


def _discover_versions( ):
    from bs4 import BeautifulSoup
    html = BeautifulSoup(
        __.http_retrieve_url(
            'https://www.python.org/downloads/windows' ).decode( ),
        'html.parser' )
    versions = [ ]
    for hyperlink in html.find_all( 'a' ):
        href = hyperlink.get( 'href' )
        if not href.startswith( 'https://www.python.org/ftp/python' ): continue
        if '-embed-' not in href: continue
        _, version, _, cpu = href.rsplit( '/' )[ -1 ].split( '-' )
        version = __.Language.derive_actual_version( version )
        if _data.supportable_base_version > version: continue
        cpu = cpu[ : -4 ].lower( )
        cpu = 'x86' if 'win32' == cpu else cpu
        versions.append( ( version, cpu, href ) )
    versions.sort( )
    from collections import defaultdict
    versions_ = defaultdict( dict )
    for version in versions:
        versions_[ version[ 0 ] ][ version[ 1 ] ] = version[ 2 ]
    return versions_


def _persist_versions( records ):
    from tomli_w import dump as persist
    location = _data.locations.version_records
    location.parent.mkdir( exist_ok = True, parents = True )
    records = { str( version ): data for version, data in records.items( ) }
    document = { 'format-version': 1, 'versions': records }
    with location.open( 'wb' ) as file:
        # TODO: Write comment header to warn about machine-generated code.
        persist( document, file )


def _summon_versions( ):
    from datetime import timedelta as TimeDelta
    from ....fs_utilities import is_older_than
    location = _data.locations.version_records
    must_discover = False
    if not location.exists( ): must_discover = True
    # TODO: Configurable refresh time.
    elif is_older_than( location, TimeDelta( days = 1 ) ): must_discover = True
    if must_discover:
        versions = _discover_versions( )
        _persist_versions( versions )
    from tomli import load as summon
    with location.open( 'rb' ) as file:
        # TODO: Check format version and update records format, if necessary.
        records = summon( file )[ 'versions' ]
    return __.DictionaryProxy( {
        __.Language.derive_actual_version( version ): data
        for version, data in records.items( ) } )


def _calculate_locations( ):
    from ....base import create_immutable_namespace
    from ....data import user_directories
    from ...base import locations
    base_location = locations.data / 'python/providers/windows-embeddable'
    return create_immutable_namespace( dict(
        archives = user_directories.artifacts / 'windows-embeddable',
        version_records = base_location / 'versions.toml',
    ) )

def _prepare_supportable_base_version( ):
    return __.Language.derive_actual_version( '3.7' )

def _produce_calculators( ):
    return dict(
        locations = _calculate_locations,
        supportable_base_version = _prepare_supportable_base_version,
    )

_data = __.produce_accretive_cacher( _produce_calculators )
__getattr__ = _data.__getattr__


__.reclassify_module( __name__ )
