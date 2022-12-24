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
        supports = LanguageVersion.survey_provider_support( definition )
        if not supports: continue
        select_versions[ name ] = definition.copy( )
        select_versions[ name ][ 'providers' ] = tuple(
            record[ 'provider' ] for record in supports )
    return select_versions


def install_version( version ):
    ''' Installs requested version of Python, if declaration exists. '''
    from .version import LanguageVersion
    version = LanguageVersion( version )
    version.install( )


def update_version( version, install = True ):
    ''' Updates requested version of Python, if declaration exists. '''
    from .version import LanguageVersion
    version = LanguageVersion( version )
    version.update( install = install )
