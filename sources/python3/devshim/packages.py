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


''' Development support for packages. '''


from re import compile as _regex_compile

from .base import expire as _expire


def ensure_python_packages( domain = '*', excludes = ( ) ):
    ''' Ensures availability of packages from domain in cache. '''
    requirements = extract_python_package_requirements(
        indicate_python_packages( )[ 0 ], domain )
    from collections.abc import Sequence as AbstractSequence
    if not isinstance( excludes, AbstractSequence ):
        _expire(
            'invalid state',
            f"Python package exclusions not a sequence: {excludes!r}" )
    requirements = tuple(
        requirement for requirement in requirements
        if _pip_requirement_to_name( requirement ) not in excludes )
    _ensure_python_packages( requirements )


def extract_python_package_requirements( specifications, domain = '*' ):
    ''' Extracts Python packages requirements from specifications.

        If the ``domain`` argument is given, then only requirements from that
        domain are extracted. Otherwise, the requirements across all domains
        are extracted. '''
    from .base import scribe
    _validate_pypackages_format_version( specifications )
    domains = _canonicalize_pypackages_domain( domain )
    from itertools import chain
    requirements = [ ]
    for domain_, subdomain_components_maximum in domains.items( ):
        if 0 == subdomain_components_maximum:
            requirements.extend( map(
                _extract_python_package_requirement,
                specifications.get( domain_, [ ] ) ) )
            continue
        apex_domain, *subdomain_components = domain_.split( '.' )
        apex_specifications = specifications.get( apex_domain, { } )
        subdomain_components_count = len( subdomain_components )
        if 0 == subdomain_components_count:
            requirements.extend( map(
                _extract_python_package_requirement,
                chain.from_iterable( apex_specifications.values( ) ) ) )
        elif 1 == subdomain_components_count:
            subdomain = subdomain_components[ 0 ]
            if subdomain not in apex_specifications:
                scribe.warning(
                    f"Python packages domain {domain_!r} does not exist." )
            requirements.extend( map(
                _extract_python_package_requirement,
                apex_specifications.get( subdomain, [ ] ) ) )
    return tuple( requirements )


def _validate_pypackages_format_version( specifications ):
    ''' Validates 'pypackages.toml' file format version and returns it. '''
    version = specifications.get( 'format-version', 1 )
    if 1 != version:
        _expire(
            'invalid data',
            f"Invalid Python packages manifest format version: {version!r}" )
    return version


def _extract_python_package_requirement( specification ):
    ''' Extracts Python package requirement from specification. '''
    if isinstance( specification, str ): return specification
    from collections.abc import Mapping as Dictionary
    if isinstance( specification, Dictionary ):
        # TODO: Validate that requirement entry exists.
        return specification[ 'requirement' ]
    _expire(
        'invalid state',
        "Invalid package specification type {class_!r}.".format(
            class_ = type( specification ) ) )


def _canonicalize_pypackages_domain( domain ):
    ''' Validates and canonicalizes Python packages domain. '''
    from types import MappingProxyType as DictionaryProxy
    valid_apex_domains = DictionaryProxy( {
        'construction': 0,
        'development': 1,
        'installation': 0,
        'optional-installation': 1,
    } )
    if '*' == domain: return valid_apex_domains
    from collections.abc import Sequence
    if isinstance( domain, str ):
        apex_domain, *subdomain_components = domain.split( '.' )
        components_maximum = valid_apex_domains.get( apex_domain, -1 )
        if components_maximum >= len( subdomain_components ):
            return { domain: components_maximum }
    elif isinstance( domain, Sequence ):
        domains = { }
        for domain_ in domain:
            domains.update( _canonicalize_pypackages_domain( domain_ ) )
        return domains
    _expire( 'invalid state', f"Invalid domain: {domain!r}" )


def indicate_python_packages( identifier = None ):
    ''' Returns Python package dependencies.

        First return value is contents of packages specifications file.
        Second return value is list of dependency fixtures for the given
        platform identifier. Will be empty if none is given. '''
    _ensure_essential_python_packages( )
    from tomli import load
    from devshim.locations import paths
    fixtures_path = paths.configuration.pypackages_fixtures
    if identifier and fixtures_path.exists( ):
        with fixtures_path.open( 'rb' ) as file:
            fixtures = load( file ).get( identifier, [ ] )
    else: fixtures = [ ]
    with paths.configuration.pypackages.open( 'rb' ) as file:
        specifications = load( file )
    with paths.configuration.pyproject.open( 'rb' ) as file:
        specifications[ 'construction' ] = (
            load( file )[ 'build-system' ][ 'requires' ] )
    return specifications, fixtures


def _ensure_essential_python_packages( ):
    ''' Ensures availability of essential packages in cache. '''
    # Ensure Tomli so that 'pyproject.toml' and 'pypackages.toml' can be read.
    # TODO: Python 3.11: Remove this explicit dependency.
    _ensure_python_packages( ( 'tomli', ), conceal_execution = True )


def _ensure_python_packages( requirements, conceal_execution = False ):
    ''' Ensures availability of packages to active Python. '''
    # If in allegedly Devshim-created virtual environment,
    # then assume necessary packages are installed.
    from os import environ as current_process_environment
    if 'OUR_VENV_NAME' in current_process_environment: return
    # If 'pip' module is not available, then assume PEP 517 build in progress,
    # which should have already ensured packages from 'build-requires'.
    try: import pip # pylint: disable=unused-import
    except ImportError: return
    from devshim.base import ensure_directory
    from devshim.locations import paths
    from devshim.platforms import active_python_abi_label
    cache_path = ensure_directory(
        paths.caches.packages.python3 / active_python_abi_label )
    cache_path_ = str( cache_path )
    from sys import path as python_search_paths
    if cache_path_ not in python_search_paths:
        python_search_paths.insert( 0, cache_path_ )
    # Ignore packages which are already cached.
    # TODO? Use 'pip freeze --path' output instead.
    in_cache_packages = frozenset(
        path.name for path in cache_path.glob( '*' )
        if path.suffix not in ( '.dist-info', ) )
    installable_requirements = tuple(
        requirement for requirement in requirements
        if _pip_requirement_to_name( requirement ) not in in_cache_packages )
    if installable_requirements:
        from shlex import split as split_command
        from devshim.base import standard_execute_external
        standard_execute_external(
            ( *split_command( 'pip install --upgrade --target' ),
              cache_path_, *installable_requirements ),
            capture_output = conceal_execution )


_pip_requirement_name_regex = _regex_compile( r'''^([\w\-]+)(.*)$''' )
def _pip_requirement_to_name( requirement ):
    return _pip_requirement_name_regex.match(
        requirement ).group( 1 ).replace( '-', '_' )
