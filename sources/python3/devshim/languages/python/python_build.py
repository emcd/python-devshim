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


''' Management of Python language installations with 'python-build'. '''


from . import _base as __


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


class PythonBuild( __.LanguageProvider ):
    ''' Works with ``python-build`` program from Pyenv. '''

    name = 'python-build'
    supportable_features = (
        'cindervm', 'cpython-tracerefs', 'pyston-lite',
    )
    from ...data import paths
    # TODO: Installation paths should be relative to home directory of user
    #       and not relative to the current repository.
    installations_path = paths.installations / 'python/python-build'
    our_installation_path = paths.installations / 'python-build'
    our_installer_path = our_installation_path / 'bin/python-build'
    our_repository_path = paths.caches.DEV.repositories / 'pyenv.tar.gz'

    def __init__( self, context, version_data, provider_data ):
        self.context = context
        self.provider_data = provider_data
        self.version_data = version_data

    def install( self ):
        ''' Compiles and installs Python via ``python-build``. '''
        self._ensure_installer( )
        pb_definition_name = self._calculate_pb_definition_name( )
        # TODO: Set environment from relevant feature flags.
        # TODO: Add platform identifiers to installation path.
        installation_path = self.installations_path / pb_definition_name
        # TODO: Allow 'clean' flag to override.
        if installation_path.exists( ): return
        from ...base import execute_external
        execute_external( (
            self.our_installer_path, pb_definition_name, installation_path ) )

    def attempt_version_data_update( self ):
        ''' Detects new Python version and returns version data update. '''
        self._ensure_installer( )
        pb_definition_name_base = self._calculate_pb_definition_name_base( )
        from ...base import execute_external
        pb_definition_names = execute_external(
            ( self.our_installer_path, '--definitions' ),
            capture_output = True ).stdout.strip( ).split( '\n' )
        pb_definition_name_candidates = [
            pb_definition_name for pb_definition_name in pb_definition_names
            if pb_definition_name.startswith( pb_definition_name_base ) ]
        if not pb_definition_name_candidates:
            # TODO: Log warning about no valid definitions matching base.
            #       Or, consider raising error.
            return self.version_data
        pb_definition_name = pb_definition_name_candidates[ -1 ]
        implementation_version = _parse_implementation_version(
            pb_definition_name )
        version_data = self.version_data.copy( )
        version_data[ 'implementation-version' ] = implementation_version
        return version_data

    @classmethod
    def is_supportable_feature( class_, feature ):
        return feature in class_.supportable_features

    @classmethod
    def is_supportable_platform( class_, platform ):
        import os
        return 'posix' == os.name

    def _calculate_pb_definition_name( self ):
        base_version = self.version_data[ 'base-version' ]
        implementation_name = self.version_data[ 'implementation' ]
        implementation_version = self.version_data[
            'implementation-version' ]
        if 'cpython' == implementation_name:
            return self.version_data[ 'implementation-version' ]
        if implementation_name in ( 'pypy', ):
            return (
                f"{implementation_name}{base_version}-"
                f"{implementation_version}" )
        return f"{implementation_name}-{implementation_version}"

    def _calculate_pb_definition_name_base( self ):
        base_version = self.version_data[ 'base-version' ]
        implementation_name = self.version_data[ 'implementation' ]
        if 'cpython' == implementation_name: return base_version
        if implementation_name in ( 'pypy', ):
            return f"{implementation_name}{base_version}-"
        implementation_version = self.version_data[
            'implementation-version' ]
        implementation_version_base = '.'.join(
            implementation_version.split( '.' )[ : -1 ] )
        return f"{implementation_name}-{implementation_version_base}"

    def _ensure_installer( self ):
        ''' Ensures that ``python-build`` is available for use. '''
        repository_path = self.our_repository_path
        from datetime import timedelta as TimeDelta
        from ...fs_utilities import is_older_than
        if repository_path.exists( ):
            # TODO: Configurable refresh time.
            if not is_older_than( repository_path, TimeDelta( days = 1 ) ):
                # TODO: Test execute permissions by current user.
                if self.our_installer_path.exists( ): return
        from ...scm_utilities import github_retrieve_tarball
        github_retrieve_tarball( 'pyenv/pyenv', 'master', repository_path )
        self._install_installer_archive( repository_path )

    def _install_installer_archive( self, archive ):
        ''' Extracts and installs installer. '''
        from pathlib import Path
        from shutil import move, rmtree
        from tempfile import TemporaryDirectory
        from ...fs_utilities import extract_tarfile
        installation_path = self.our_installation_path
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
