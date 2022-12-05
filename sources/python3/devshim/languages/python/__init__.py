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
        document = tomllib.load( file )
    # TODO: Check format version and dispatch accordingly.
    declarations = document.get( 'versions', { } )
    from os import environ as current_process_environment
    selector = current_process_environment.get( 'DEVSHIM_PYTHON_VERSION' )
    if selector:
        declarations = {
            name: value for name, value in declarations.items( )
            if selector == name
        }
    # TODO: Filter by availability of providers on current OS platform.
    return declarations


def install_version( version ):
    ''' Installs requested version of Python, if declaration exists. '''
    context, version_data = _create_context( version )
    version = context.version
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


def update_version( version ):
    ''' Updates requested version of Python, if declaration exists. '''
    context, version_data = _create_context( version )
    version = context.version
    for entry in version_data[ 'providers' ]:
        provider_data = _normalize_provider_entry( context, entry )
        class_ = provider_classes[ provider_data[ 'name' ] ]
        try:
            provider = class_( context, version_data, provider_data )
            version_data_ = provider.attempt_version_data_update( )
        except Exception: # pylint: disable=broad-except
            __.scribe.exception(
                f"Could not update {context} by {provider.name}." )
            continue
        if version_data != version_data_:
            _update_version_data( version, version_data_ )
            install_version( version )
            break


def _update_version_data( version, data ):
    from ...data import paths
    from ...packages import ensure_import_package
    tomllib = ensure_import_package( 'tomllib' )
    tomli_w = ensure_import_package( 'tomli-w' )
    with paths.configuration.devshim.python.versions.open( 'r+b' ) as file:
        document = tomllib.load( file )
        # TODO: Check format version and dispatch accordingly.
        document[ 'versions' ][ version ] = data
        file.seek( 0 )
        tomli_w.dump( document, file )


def _create_context( version ):
    versions = survey_support( )
    if not versions:
        __.expire( 'invalid data', "No relevant support declarations." )
    if None is version: version = next( iter( versions ) )
    version_data = versions.get( version )
    context = __.LanguageContext( version )
    # TODO: Ensure exception factories are loaded and use them instead.
    # TODO: Use context information in error messages.
    if None is version_data:
        __.expire( 'invalid data', f"No support declaration for {version!r}." )
    if 'providers' not in version_data:
        __.expire( 'invalid data', f"No providers for {version!r}." )
    return context, version_data


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


from . import python_build
provider_classes = __.DictionaryProxy( {
    class_.name : class_ for class_ in ( python_build.PythonBuild, )
} )
