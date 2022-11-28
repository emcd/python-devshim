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


''' Management of Python language installations. '''


from . import _base as __


def survey_support( ):
    ''' Returns declarations of Pythons versions support. '''
    from ...data import paths
    from ...packages import ensure_import_package
    tomllib = ensure_import_package( 'tomllib' )
    with paths.configuration.devshim.python.versions.open( 'rb' ) as file:
        data = tomllib.load( file )
    # TODO: Check format version and dispatch accordingly.
    declarations = data.get( 'versions', { } )
    from os import environ as current_process_environment
    selector = current_process_environment.get( 'DEVSHIM_PYTHON_VERSION' )
    if selector:
        declarations = {
            name: value for name, value in declarations.items( )
            if selector == name
        }
    # TODO: Filter by availability of providers on current OS platform.
    return declarations


def install( version ):
    ''' Installs requested version of Python, if declaration exists. '''
    version_data = survey_support( ).get( version )
    context = __.LanguageContext( version )
    # TODO: Ensure exception factories are loaded and use them instead.
    # TODO: Use context information in error messages.
    if None is version_data:
        __.expire( 'invalid data', f"No support declaration for {version!r}." )
    if 'providers' not in version_data:
        __.expire( 'invalid data', f"No providers for {version!r}." )
    for entry in version_data[ 'providers' ]:
        provider_data = _normalize_provider_entry( context, entry )
        class_ = provider_classes[ provider_data[ 'name' ] ]
        try:
            provider = class_( context, version_data, provider_data )
            provider.install( )
        except Exception: # pylint: disable=broad-except
            __.scribe.exception(
                f"Could not install {context} by {provider.name}." )
            continue
        break


def _normalize_provider_entry( context, entry ):
    # TODO: Ensure exception factories are loaded and use them instead.
    # TODO: Use context information in error messages.
    if isinstance( entry, str ):
        return __.DictionaryProxy( { 'name' : entry } )
    if isinstance( entry, __.AbstractDictionary ):
        if 'name' in entry: return entry
    __.expire(
        'invalid data',
        f"Invalid provider entry, {entry!r}, for {context.version!r}." )


class PythonBuild( __.LanguageProvider ):
    ''' Works with ``python-build`` program from Pyenv. '''

    name = 'python-build'
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
        execute_external(
            ( self.our_installer_path, pb_definition_name, installation_path ),
            capture_output = False )

    def _calculate_pb_definition_name( self ):
        base_version = self.version_data[ 'base-version' ]
        implementation_name = self.version_data[ 'implementation' ]
        implementation_version = self.version_data[
            'implementation-version' ]
        if 'cpython' == implementation_name:
            return self.version_data[ 'implementation-version' ]
        if implementation_name in ( 'pypy3', ):
            return (
                f"{implementation_name}{base_version}-"
                f"{implementation_version}" )
        return f"{implementation_name}-{implementation_version}"

    @classmethod
    def is_supportable_feature( class_, feature ):
        # TODO: Implement.
        pass

    @classmethod
    def is_supportable_platform( class_, platform ):
        # TODO: Implement.
        pass

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


provider_classes = __.DictionaryProxy( {
    class_.name : class_ for class_ in ( PythonBuild, )
} )
