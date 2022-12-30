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


''' Management of Python installations via :command:`python-build`. '''


from . import base as __


supportable_features = ( 'cindervm', 'pyston-lite', 'tracerefs', )
supportable_implementations = ( 'cpython', 'pypy', )
supportable_platforms = ( 'posix', )

class LanguageProvider( __.LanguageProvider ):
    ''' Uses ``python-build`` program from Pyenv to manage installations. '''

    language = __.Language
    name = 'python-build'

    @classmethod
    def discover_current_version( class_, definition ):
        # TODO: Validate version definition.
        _ensure_installer( )
        pb_definition_name_base = (
            _calculate_pb_definition_name_base( definition ) )
        from ....base import execute_external
        pb_definition_names = execute_external(
            ( _data.pb_executable_location, '--definitions' ),
            capture_output = True ).stdout.strip( ).split( '\n' )
        # TODO: Filter prerelease versions by default, but allow override.
        pb_definition_name_candidates = [
            pb_definition_name for pb_definition_name in pb_definition_names
            if pb_definition_name.startswith( pb_definition_name_base ) ]
        if not pb_definition_name_candidates:
            # TODO: Use exception factory.
            raise RuntimeError
        pb_definition_name = pb_definition_name_candidates[ -1 ]
        return class_.language.derive_actual_version(
            _parse_implementation_version( pb_definition_name ) )

    @classmethod
    def is_supportable_base_version( class_, version ):
        version = class_.language.derive_actual_version( version )
        return _data.supportable_base_version <= version

    @classmethod
    def is_supportable_feature( class_, feature ):
        return feature in supportable_features

    @classmethod
    def is_supportable_implementation( class_, implementation ):
        return implementation in supportable_implementations

    @classmethod
    def is_supportable_platform( class_, platform = None ):
        if None is platform:
            from ....platforms.identity import extract_os_class
            platform = extract_os_class( )
        return platform in supportable_platforms

    def derive_executables_location( self, name = None ):
        location = self.installation_location / 'bin'
        if None is not name: return location / name
        return location

    def install( self, force = False ):
        ''' Compiles and installs Python via ``python-build``. '''
        _ensure_installer( )
        pb_definition_name = self._calculate_pb_definition_name( )
        from os import environ as current_process_environment
        subprocess_environment = current_process_environment.copy( )
        self._modify_environment_from_features( subprocess_environment )
        directory = self.installation_location
        if not force and directory.exists( ): return self
        # TODO: Attempt to unlink directory tree.
        from ....base import execute_external
        execute_external(
            ( _data.pb_executable_location, pb_definition_name, directory ),
            env = subprocess_environment )
        self._execute_post_installation_activities( )
        return self

    def _calculate_pb_definition_name( self ):
        definition = self.descriptor.definition
        record = self.descriptor.record
        base_version = definition[ 'base-version' ]
        implementation_name = definition[ 'implementation' ]
        implementation_version = record[ 'implementation-version' ]
        if 'cpython' == implementation_name: return implementation_version
        if implementation_name in ( 'pypy', ):
            return (
                f"{implementation_name}{base_version}-"
                f"{implementation_version}" )
        return f"{implementation_name}-{implementation_version}"

    def _ensure_site_packages( self ):
        installation_location = self.installation_location
        python_location = installation_location / 'bin/python'
        __.ensure_site_packages( installation_location, python_location )

    def _execute_post_installation_activities( self ):
        self._ensure_site_packages( )
        # Per-feature activities, such as site customization.
        for feature in self.descriptor.features.values( ):
            feature.modify_installation( self.installation_location )

    def _modify_environment_from_features( self, environment ):
        for feature in self.descriptor.features.values( ):
            feature.modify_provider_environment( environment )

__.register_provider_class( LanguageProvider )


def _calculate_pb_definition_name_base( definition ):
    base_version = definition[ 'base-version' ]
    implementation_name = definition[ 'implementation' ]
    if 'cpython' == implementation_name: return base_version
    if implementation_name in ( 'pypy', ):
        return f"{implementation_name}{base_version}-"
    return f"{implementation_name}-"


def _ensure_installer( ):
    ''' Ensures that ``python-build`` is available for use. '''
    repository_path = _data.pb_repository_location
    from datetime import timedelta as TimeDelta
    from ....fs_utilities import is_older_than
    if repository_path.exists( ):
        # TODO: Configurable refresh time.
        if not is_older_than( repository_path, TimeDelta( days = 1 ) ):
            # TODO: Test execute permissions by current user.
            if _data.pb_executable_location.exists( ): return
    from ....scm_utilities import github_retrieve_tarball
    github_retrieve_tarball( 'pyenv/pyenv', 'master', repository_path )
    _install_installer_archive( repository_path )

def _install_installer_archive( archive ):
    ''' Extracts and installs installer. '''
    from pathlib import Path
    from shutil import move, rmtree
    from tempfile import TemporaryDirectory
    from ....fs_utilities import extract_tarfile
    installation_path = _data.pb_installation_location
    installation_bin_path = installation_path / 'bin'
    installation_share_path = installation_path / 'share/python-build'
    def selector( member ):
        ''' Selects only archive members pertinent to ``python-build``. '''
        interior_path_parts = ( 'plugins', 'python-build' )
        return interior_path_parts == Path( member.name ).parts[ 1 : 3 ]
    with TemporaryDirectory( ) as temporary_path:
        temporary_path = Path( temporary_path )
        members = extract_tarfile(
            archive, temporary_path, selector = selector )
        source_path = temporary_path.joinpath(
            *Path( next( iter ( members ) ).name ).parts[ 0 : 3 ] )
        if installation_path.exists( ): rmtree( installation_path )
        move( source_path / 'bin', installation_bin_path )
        move( source_path / 'share/python-build', installation_share_path )
    for path in installation_bin_path.rglob( '*' ): path.chmod( 0o755 )
    # TODO? Enforce permissions on shared data.


_pb_definition_regex = __.re.compile(
    r'''^(?P<implementation_name>\w+)'''
    r'''(?P<base_version>\d\.\d)?-'''
    r'''(?P<implementation_version>.*)$''' )

def _parse_implementation_version( pb_definition_name ):
    if pb_definition_name[ 0 ].isdigit( ): # Case: cpython
        return pb_definition_name
    result = _pb_definition_regex.match( pb_definition_name )
    # TODO: Error on no match.
    return result.group( 'implementation_version' )


def _prepare_supportable_base_version( ):
    return __.Language.derive_actual_version( '3.7' )

def _produce_calculators( ):
    def calculate_pbil( ):
        from ....data import user_directories
        return user_directories.installations / 'python-build'
    def calculate_pbrl( ):
        from ....data import paths
        return paths.caches.DEV.repositories / 'pyenv.tar.gz'
    return dict(
        pb_installation_location = calculate_pbil,
        pb_executable_location = ( lambda:
            _data.pb_installation_location / 'bin/python-build' ),
        pb_repository_location = calculate_pbrl,
        supportable_base_version = _prepare_supportable_base_version,
    )

_data = __.produce_accretive_cacher( _produce_calculators )
