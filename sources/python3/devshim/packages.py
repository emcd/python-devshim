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


def ensure_python_support_packages( ):
    ''' Ensures availability of support packages to active Python. '''
    # Ensure Tomli so that 'pyproject.toml' can be read.
    # TODO: Python 3.11: Remove this explicit dependency.
    _ensure_python_packages( ( 'tomli', ) )
    from tomli import load
    base_requirements = extract_python_package_requirements(
        indicate_python_packages( )[ 0 ], 'development.base' )
    from devshim.locations import paths
    with paths.configuration.pyproject.open( 'rb' ) as file:
        construction_requirements = (
            load( file )[ 'build-system' ][ 'requires' ] )
    _ensure_python_packages( frozenset(
        ( *base_requirements, *construction_requirements ) ) )


def extract_python_package_requirements( specifications, domain = None ): # pylint: disable=too-many-branches
    ''' Extracts Python packages requirements from specifications.

        If the ``domain`` argument is given, then only requirements from that
        domain are extracted. Otherwise, the requirements across all domains
        are extracted. '''
    # TODO: Raise error on unsupported format version.
    if 1 != specifications.get( 'format-version', 1 ): pass
    from itertools import chain
    valid_apex_domains = (
        'installation', 'optional-installation', 'development', )
    domains = ( domain, ) if domain else valid_apex_domains
    requirements = [ ]
    for domain_ in domains:
        if 'installation' == domain_:
            requirements.extend( map(
                _extract_python_package_requirement,
                specifications.get( domain, [ ] ) ) )
        else:
            apex_domain, *subdomains = domain_.split( '.' )
            # TODO: Raise error if apex domain is not a valid.
            apex_specifications = specifications.get( apex_domain, { } )
            if 0 == len( subdomains ):
                requirements.extend( map(
                    _extract_python_package_requirement,
                    chain.from_iterable( apex_specifications.values( ) ) ) )
            elif 1 == len( subdomains ):
                subdomain = subdomains[ 0 ]
                requirements.extend( map(
                    _extract_python_package_requirement,
                    apex_specifications.get( subdomain, [ ] ) ) )
            # TODO: Raise more appropriate error.
            else: raise RuntimeError( f"Invalid domain: {domain}" )
    return tuple( requirements )


def _extract_python_package_requirement( specification ):
    ''' Extracts Python package requirement from specification. '''
    if isinstance( specification, str ): return specification
    from collections.abc import Mapping as Dictionary
    if isinstance( specification, Dictionary ):
        # TODO: Validate that requirement entry exists.
        return specification[ 'requirement' ]
    # TODO: Raise error about invalid state if this is reached.
    raise RuntimeError


def _ensure_python_packages( requirements ):
    ''' Ensures availability of packages to active Python. '''
    from os import environ as cpe
    # TODO: Change this to an on-demand cache access.
    from devshim.platforms import active_python_abi_label
    # Ignore if in an appropriate virtual environment.
    if active_python_abi_label == cpe.get( 'OUR_VENV_NAME' ): return
    # If 'pip' module is not available, then assume PEP 517 build in progress,
    # which should have already ensured packages from 'build-requires'.
    try: import pip # pylint: disable=unused-import
    except ImportError: return
    from devshim.base import ensure_directory
    from devshim.locations import paths
    cache_path = ensure_directory(
        paths.caches.packages.python3 / active_python_abi_label )
    cache_path_ = str( cache_path )
    from sys import path as python_search_paths
    if cache_path_ not in python_search_paths:
        python_search_paths.insert( 0, cache_path_ )
    # Ignore packages which are already cached.
    in_cache_packages = frozenset(
        path.name for path in cache_path.glob( '*' )
        if path.suffix not in ( '.dist-info', ) )
    from re import match as regex_match
    def requirement_to_name( requirement ):
        return regex_match(
            r'^([\w\-]+)(.*)$', requirement ).group( 1 ).replace( '-', '_' )
    installable_requirements = tuple(
        requirement for requirement in requirements
        if requirement_to_name( requirement ) not in in_cache_packages )
    if installable_requirements:
        from shlex import split as split_command
        from devshim.base import standard_execute_external
        standard_execute_external(
            ( *split_command( 'pip install --upgrade --target' ),
              cache_path_, *installable_requirements ) )


def indicate_python_packages( identifier = None ):
    ''' Returns Python package dependencies.

        First return value is contents of packages specifications file.
        Second return value is list of dependency fixtures for the given
        platform identifier. Will be empty if none is given. '''
    from tomli import load
    from devshim.locations import paths
    fixtures_path = paths.configuration.pypackages_fixtures
    if identifier and fixtures_path.exists( ):
        with fixtures_path.open( 'rb' ) as file:
            fixtures = load( file ).get( identifier, [ ] )
    else: fixtures = [ ]
    with paths.configuration.pypackages.open( 'rb' ) as file:
        specifications = load( file )
    return specifications, fixtures


# TODO: Add hook for this to an on-demand cache object.
#       Compute only on '__getattr__' for it.
ensure_python_support_packages( )
