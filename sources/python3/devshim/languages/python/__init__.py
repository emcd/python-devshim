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


def survey_support( by_availability = False ):
    ''' Returns Python versions which have valid declarations. '''
    from ...data import paths
    from ...packages import ensure_import_package
    tomllib = ensure_import_package( 'tomllib' )
    with paths.configuration.devshim.python.versions.open( 'rb' ) as file:
        document = tomllib.load( file )
    # TODO: Check format version and dispatch accordingly.
    versions = document.get( 'versions', { } )
    if not by_availability: return versions
    from os import environ as current_process_environment
    selector = current_process_environment.get( 'DEVSHIM_PYTHON_VERSION' )
    select_versions = { }
    for version, version_data in versions.items( ):
        if None is not selector and selector != version: continue
        select_providers = _survey_provider_support( version, version_data )
        if not select_providers: continue
        version_data[ 'providers' ] = select_providers
        select_versions[ version ] = version_data
    return select_versions


def _survey_provider_support( version, version_data ):
    ''' Returns valid providers for Python version declaration. '''
    context = __.LanguageContext( version )
    feature_names = tuple(
        __.normalize_feature_entry( context, feature_entry )[ 'name' ]
        for feature_entry in version_data.get( 'features', ( ) ) )
    select_providers = [ ]
    for provider_entry in version_data.get( 'providers', ( ) ):
        provider_data = __.normalize_provider_entry( context, provider_entry )
        provider_class = provider_classes[ provider_data[ 'name' ] ]
        if not provider_class.is_supportable_platform( ): continue
        if not provider_class.is_supportable_base_version(
            version_data[ 'base-version' ]
        ): continue
        if not provider_class.is_supportable_implementation(
            version_data[ 'implementation' ]
        ): continue
        if feature_names and not all(
            provider_class.is_supportable_feature( feature_name )
            for feature_name in feature_names
        ): continue
        select_providers.append( provider_data )
    return select_providers


def install_version( version ):
    ''' Installs requested version of Python, if declaration exists. '''
    context, version_data = _create_context( version )
    version = context.version
    for entry in version_data[ 'providers' ]:
        provider_data = __.normalize_provider_entry( context, entry )
        provider_class = provider_classes[ provider_data[ 'name' ] ]
        try:
            provider = provider_class( context, version_data, provider_data )
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
        provider_data = __.normalize_provider_entry( context, entry )
        provider_class = provider_classes[ provider_data[ 'name' ] ]
        try:
            provider = provider_class( context, version_data, provider_data )
            version_data_ = provider.attempt_version_data_update( )
        except Exception: # pylint: disable=broad-except
            __.scribe.exception(
                f"Could not update {context} by {provider.name}." )
            continue
        if version_data != version_data_:
            _update_version_data( version, version_data_ )
            install_version( version )
            break
        install_version( version ) # Ensure installation is complete/valid.


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
        raise __.provide_exception_factory( 'invalid data' )(
            "No relevant support declarations." )
    if None is version: version = next( iter( versions ) )
    version_data = versions.get( version )
    context = __.LanguageContext( version )
    if None is version_data:
        raise __.provide_exception_factory( 'invalid data' )(
            f"No support declaration for {context}." )
    if 'providers' not in version_data:
        raise __.provide_exception_factory( 'invalid data' )(
            f"No providers for {context}." )
    return context, version_data


from . import python_build
provider_classes = __.DictionaryProxy( {
    class_.name : class_ for class_ in ( python_build.PythonBuild, )
} )
