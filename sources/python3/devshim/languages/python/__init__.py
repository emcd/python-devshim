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


def detect_default_version( ):
    ''' Detects default Python version.

        If in a Python virtual environment, then the Python version for that
        environment is returned. Else, the first available Python version from
        the project's Python version declarations is returned. '''
    # TODO: Detect if in relevant virtual environment and infer version.
    return next( iter( survey_versions( ) ) )


def infer_executable_location( version = None ):
    ''' Infers location of Python executable by version. '''
    return infer_installation_location( version ) / 'bin/python'


def infer_installation_location( version = None ):
    ''' Infers location of Python installation by version. '''
    versions = survey_versions( )
    if None is version: version = next( iter( versions ) )
    from .version import LanguageVersion
    version = LanguageVersion( version )
    for provider in version.providers.values( ):
        location = provider.installation_location
        if not location.exists( ):
            __.scribe.debug(
                f"Could not locate installation of {version} "
                f"by {provider.name}." )
            continue
        return location
    # TODO: Use exception factory.
    raise LookupError


def validate_version( version ):
    ''' Validates version against available Python versions. '''
    if version not in survey_versions( ):
        # TODO: Use exception factory.
        raise ValueError
    return version


def survey_versions( by_availability = False ):
    ''' Returns Python versions which have valid declarations. '''
    definitions = __.data.version_definitions
    from os import environ as current_process_environment
    selector = current_process_environment.get( 'DEVSHIM_PYTHON_VERSION' )
    if selector:
        try: return { selector: definitions[ selector ] }
        # TODO: Raise error on unmatched version.
        except KeyError: return { }
    if not by_availability: return definitions
    from .version import LanguageVersion
    select_versions = { }
    for name, definition in definitions.items( ):
        select_providers = _survey_provider_support( LanguageVersion( name ) )
        if not select_providers: continue
        select_versions[ name ] = definition.copy( )
        select_versions[ name ][ 'providers' ] = select_providers
    return select_versions


def _survey_provider_support( version ):
    ''' Returns valid providers for Python version declaration. '''
    feature_names = tuple( version.features.keys( ) )
    select_providers = [ ]
    for provider_name, provider in version.providers.items( ):
        if not provider.is_supportable_platform( ): continue
        if not provider.is_supportable_base_version(
            version.definition[ 'base-version' ]
        ): continue
        if not provider.is_supportable_implementation(
            version.definition[ 'implementation' ]
        ): continue
        if feature_names and not all(
            provider.is_supportable_feature( feature_name )
            for feature_name in feature_names
        ): continue
        select_providers.append( provider_name )
    return select_providers


def install_version( version ):
    ''' Installs requested version of Python, if declaration exists. '''
    from .version import LanguageVersion
    version = LanguageVersion( version )
    for provider in version.providers.values( ):
        try: provider.install( )
        except Exception: # pylint: disable=broad-except
            __.scribe.exception(
                f"Could not install {version} by {provider.name}." )
            continue
        break


def update_version( version, install = True ):
    ''' Updates requested version of Python, if declaration exists. '''
    from .version import LanguageVersion
    version = LanguageVersion( version )
    for provider in version.providers.values( ):
        try: definition = provider.attempt_version_data_update( )
        except Exception: # pylint: disable=broad-except
            __.scribe.exception(
                f"Could not update {version} by {provider.name}." )
            continue
        # TODO: Split language configuration and data.
        #       Data file indexed by version name.
        #       Has current provider and implementation version.
        # TODO: Use interface of version object for updates.
        if version.definition != definition:
            _update_version_data( version.name, definition )
            version.definition = definition
            break
    if install: install_version( version.name ) # Ensure installation.


def _update_version_data( version, data ):
    from ...data import paths
    from ...packages import ensure_import_package
    tomllib = ensure_import_package( 'tomllib' )
    tomli_w = ensure_import_package( 'tomli-w' )
    with paths.configuration.devshim.python.open( 'rb' ) as file:
        document = tomllib.load( file )
    # Repoen to truncate file and reset I/O cursor.
    with paths.configuration.devshim.python.open( 'wb' ) as file:
        # TODO: Check format version and dispatch accordingly.
        document[ 'versions' ][ version ] = data
        tomli_w.dump( document, file )
