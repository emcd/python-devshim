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


# Latent Dependencies:
#   packages -> environments -> packages
# pylint: disable=cyclic-import


from re import compile as _regex_compile
from types import MappingProxyType as _DictionaryProxy

from .base import expire as _expire


def install_python_packages( process_environment, identifier = None ):
    ''' Installs required Python packages into virtual environment. '''
    from .base import execute_external
    raw, frozen, unpublished = generate_pip_requirements_text(
        identifier = identifier )
    execute_external(
        'pip install --upgrade setuptools pip wheel',
        env = process_environment )
    if not identifier or not frozen:
        pip_options = [ ]
        if not identifier:
            pip_options.append( '--upgrade' )
            pip_options.append( '--upgrade-strategy eager' )
        execute_pip_with_requirements(
            process_environment, 'install', raw, pip_options = pip_options )
    else:
        pip_options = [ '--require-hashes' ]
        execute_pip_with_requirements(
            process_environment, 'install', frozen, pip_options = pip_options )
    if unpublished:
        execute_pip_with_requirements(
            process_environment, 'install', unpublished )
    # Pip cannot currently mix editable and digest-bound requirements,
    # so we must install editable packages separately. (As of 2022-02-06.)
    # https://github.com/pypa/pip/issues/4995
    execute_external( 'pip install --editable .', env = process_environment )


def execute_pip_with_requirements(
    process_environment, command, requirements, pip_options = None
):
    ''' Executes a Pip command with requirements. '''
    pip_options = pip_options or ( )
    from .base import execute_external
    # Unfortunately, Pip does not support reading requirements from stdin,
    # as of 2022-01-02. To workaround, we need to write and then read
    # a temporary file. More details: https://github.com/pypa/pip/issues/7822
    from shlex import quote as shell_quote
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile( mode = 'w+' ) as requirements_file:
        requirements_file.write( requirements )
        requirements_file.flush( )
        execute_external(
            "pip {command} {options} --requirement {requirements_file}".format(
                command = command,
                options = ' '.join( pip_options ),
                requirements_file = shell_quote( requirements_file.name ) ),
            env = process_environment )


def generate_pip_requirements_text( identifier = None ):
    ''' Generates Pip requirements lists from local configuration. '''
    # https://pip.pypa.io/en/stable/reference/requirements-file-format/
    # https://pip.pypa.io/en/stable/topics/repeatable-installs/
    specifications, fixtures = indicate_python_packages(
        identifier = identifier )
    # Pip cannot currently mix frozen and unfrozen requirements,
    # so we must split them out. (As of 2022-02-06.)
    # https://github.com/pypa/pip/issues/6469
    raw, frozen, unpublished = [ ], [ ], [ ]
    from lockup import create_namespace
    for fixture in map( lambda d: create_namespace( **d ), fixtures ):
        name = fixture.name
        if hasattr( fixture, 'url' ):
            unpublished.append( f"{name}@ {fixture.url}" )
        elif hasattr( fixture, 'digests' ):
            options = ' \\\n    '.join(
                f"--hash {digest}" for digest in fixture.digests )
            frozen.append( f"{name}=={fixture.version} \\\n    {options}" )
    raw.extend( extract_python_package_requirements( specifications ) )
    return '\n'.join( raw ), '\n'.join( frozen ), '\n'.join( unpublished )


def ensure_python_packages( domain = '*', excludes = ( ) ):
    ''' Ensures availability of packages from domain in cache. '''
    from .base import scribe
    domains = _canonicalize_pypackages_domain( domain )
    scribe.info(
        "Ensuring packages for domains: {domains}".format(
            domains = ', '.join( domains.keys( ) ) ) )
    _ensure_essential_python_packages( )
    requirements = extract_python_package_requirements(
        indicate_python_packages( )[ 0 ], domains )
    from collections.abc import Sequence as AbstractSequence
    if not isinstance( excludes, AbstractSequence ):
        _expire(
            'invalid state',
            f"Python package exclusions not a sequence: {excludes!r}" )
    requirements = tuple(
        requirement for requirement in requirements
        if _pep508_requirement_to_name( requirement ) not in excludes )
    _ensure_python_packages( requirements )


def extract_python_package_requirements( specifications, domain = '*' ):
    ''' Extracts Python packages requirements from specifications.

        If the ``domain`` argument is given, then only requirements from that
        domain are extracted. Otherwise, the requirements across all domains
        are extracted. '''
    from .base import scribe
    _validate_pypackages_format_version( specifications )
    from collections.abc import Mapping as AbstractDictionary
    if isinstance( domain, AbstractDictionary ): domains = domain
    else: domains = _canonicalize_pypackages_domain( domain )
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
    assert_python_packages( ( 'tomli', ) )
    from tomli import load
    from .data import paths
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


def assert_python_packages( requirements ):
    ''' Asserts availability of packages to active Python. '''
    # If in virtual environment that we allegedly created,
    # then assume necessary packages are installed.
    from .environments import in_our_python_environment
    if in_our_python_environment: return
    cache = _ensure_python_packages_cache( )
    installable_requirements = _filter_available_python_packages(
        requirements, cache = cache )
    if not installable_requirements: return
    from .base import expire
    names = ', '.join(
        map( _pep508_requirement_to_name, installable_requirements ) )
    expire( 'invalid state',
            f"Packages absent from local cache: {names!r}" )


def ensure_import_package( name ):
    ''' Ensures package is available for import and imports it.

        Translates aliases for forward compatibility. '''
    name = _package_aliases.get( name, name )
    _ensure_python_packages( ( name, ) )
    legal_name = name.replace( '-', '_' )
    from importlib import import_module
    # nosemgrep: python.lang.security.audit.non-literal-import
    return import_module( legal_name )


_package_aliases = _DictionaryProxy( {
    'tomllib': 'tomli', # TODO: Python 3.11: Remove.
} )


def _ensure_essential_python_packages( ):
    ''' Ensures availability of essential packages in cache. '''
    # Ensure Tomli so that 'pyproject.toml' and 'pypackages.toml' can be read.
    # TODO: Python 3.11: Remove this explicit dependency.
    _ensure_python_packages( ( 'tomli', ) )


def _ensure_python_packages( requirements ):
    ''' Ensures availability of packages to active Python. '''
    # If in virtual environment that we allegedly created,
    # then assume necessary packages are installed.
    from .environments import in_our_python_environment
    if in_our_python_environment: return
    # If 'pip' module is not available, then assume PEP 517 build in progress,
    # which should have already ensured packages from 'build-requires'.
    try: import pip # pylint: disable=unused-import
    except ImportError: return
    cache = _ensure_python_packages_cache( )
    installable_requirements = _filter_available_python_packages(
        requirements, cache = cache )
    if installable_requirements:
        from shlex import split as split_command
        from .base import execute_external
        execute_external(
            ( *split_command( 'pip install --upgrade --target' ),
              cache, *installable_requirements ) )


def _filter_available_python_packages( requirements, cache = None ):
    ''' Only accepts Pip requirements for packages not in cache. '''
    if not cache: cache = _ensure_python_packages_cache( )
    # TODO? Use 'pip freeze --path' output instead.
    present_packages = frozenset(
        path.name for path in cache.glob( '*' )
        if path.suffix not in ( '.dist-info', ) )
    return tuple(
        requirement for requirement in requirements
        if _pep508_requirement_to_name( requirement ) not in present_packages )


def _ensure_python_packages_cache( ):
    ''' Ensures availability of packages cache for active Python. '''
    from .data import paths
    from .fs_utilities import ensure_directory
    from .platforms import active_python_abi_label
    cache = ensure_directory(
        paths.caches.packages.python3 / active_python_abi_label )
    cache_ = str( cache )
    from sys import path as python_search_paths
    if cache_ not in python_search_paths:
        python_search_paths.insert( 0, cache_ )
    return cache


def record_python_packages_fixtures( identifier, fixtures ):
    ''' Records table of Python packages fixtures. '''
    from operator import itemgetter
    from tomli import load
    from tomli_w import dump
    from .data import paths
    fixtures_path = paths.configuration.pypackages_fixtures
    if fixtures_path.exists( ):
        with fixtures_path.open( 'rb' ) as file: document = load( file )
    else: document = { }
    document[ identifier ] = fixtures
    # Minimize delta sizes for SCM commits by preserving order.
    # I.e., a micro version bump should not reshuffle a large block of data.
    document = dict( sorted( document.items( ), key = itemgetter( 0 ) ) )
    with fixtures_path.open( 'wb' ) as file: dump( document, file )


def delete_python_packages_fixtures( identifiers ):
    ''' Deletes tables of Python packages fixtures. '''
    from tomli import load
    from tomli_w import dump
    from .data import paths
    fixtures_path = paths.configuration.pypackages_fixtures
    if not fixtures_path.exists( ): return
    with fixtures_path.open( 'rb' ) as file: document = load( file )
    for identifier in identifiers:
        if identifier not in document: continue
        document.pop( identifier )
    with fixtures_path.open( 'wb' ) as file: dump( document, file )


def calculate_python_packages_fixtures( environment ):
    ''' Calculates Python package fixtures, such as digests or URLs. '''
    fixtures = [ ]
    for entry in indicate_current_python_packages( environment ):
        requirement = entry.requirement
        fixture = dict( name = requirement.name )
        if 'editable' in entry.flags: continue
        if requirement.url: fixture.update( dict( url = requirement.url, ) )
        else:
            package_version = next( iter( requirement.specifier ) ).version
            fixture.update( dict(
                version = package_version,
                digests = tuple( map(
                    lambda s: f"sha256:{s}",
                    aggregate_pypi_release_digests(
                        requirement.name, package_version )
                ) )
            ) )
        fixtures.append( fixture )
    return fixtures


def indicate_current_python_packages( environment ):
    ''' Returns currently-installed Python packages. '''
    eggstractor = _regex_compile(
        r'''.*#egg=(?P<package_name>\w[\w\-]+\w)(?:&.*)?$''' )
    from shlex import split as split_command
    from types import SimpleNamespace
    from packaging.requirements import Requirement
    from .base import execute_external
    entries = [ ]
    for line in execute_external(
        split_command( 'pip freeze' ),
        capture_output = True, env = environment,
    ).stdout.strip( ).splitlines( ):
        if line.startswith( '#' ): continue
        entry = SimpleNamespace( flags = [ ] )
        if line.startswith( '-e git' ):
            entry.flags.append( 'editable' )
            # Replace '-e' with '{package_name}@'.
            name_match = eggstractor.match( line )
            if not name_match: continue
            requirement = ' '.join( (
                name_match.group( 'package_name' ) + '@',
                line.split( ' ', maxsplit = 1 )[ 1 ] ) )
        # TODO: Case: -e /home/me/src/python-devshim
        elif line.startswith( '-e' ): continue
        else: requirement = line
        entry.requirement = Requirement( requirement )
        entries.append( entry )
    return entries


pypi_release_digests_cache = { }
def aggregate_pypi_release_digests( name, version, index_url = '' ):
    ''' Aggregates hashes for release on PyPI. '''
    cache_index = ( index_url, name, version )
    digests = pypi_release_digests_cache.get( cache_index )
    if digests: return digests
    release_info = retrieve_pypi_release_information(
        name, version, index_url = index_url )
    digests = [
        package_info[ 'digests' ][ 'sha256' ]
        for package_info in release_info ]
    pypi_release_digests_cache[ cache_index ] = digests
    return digests


def retrieve_pypi_release_information( name, version, index_url = '' ): # pylint: disable=inconsistent-return-statements
    ''' Retrieves information about specific release on PyPI. '''
    index_url = index_url or 'https://pypi.org'
    from json import load
    from time import sleep
    from urllib.error import URLError as UrlError
    from urllib.request import Request as HttpRequest, urlopen as access_url
    # https://warehouse.pypa.io/api-reference/json.html#release
    request = HttpRequest(
        f"{index_url}/pypi/{name}/json",
        headers = { 'Accept': 'application/json', } )
    attempts_count_max = 2
    for attempts_count in range( attempts_count_max + 1 ):
        try:
            with access_url( request ) as http_reader: # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected
                return load( http_reader )[ 'releases' ][ version ]
        except ( KeyError, UrlError, ):
            if attempts_count_max == attempts_count: raise
            sleep( 2 ** attempts_count )


_pep508_requirement_name_regex = _regex_compile( r'''^([\w\-]+)(.*)$''' )
def _pep508_requirement_to_name( requirement ):
    return _pep508_requirement_name_regex.match(
        requirement ).group( 1 ).replace( '-', '_' )


class Version:
    ''' Version manager.

        Compatible with the version scheme laid forth in
        `PEP 440 <https://www.python.org/dev/peps/pep-0440/#version-scheme>`_.

        Core Format: ``{{major}}.{{minor}}``
        Release amendments extend the core format by appending
        ``.{{amendment}}``.
        Development prereleases extend the core format by appending
        ``a{{timestamp:yyyymmddHHMM}}``.
        Release candidates extend the core format by appending
        ``rc{{candidate}}``, where ``candidate`` starts at ``1`` and increases
        by one upon each increment. '''

    @classmethod
    def from_string( kind, version ):
        ''' Constructs a version object by parsing it from a string. '''
        from re import match
        matched = match(
            r"(?P<major>\d+)\.(?P<minor>\d+)"
            r"(?:\.(?P<patch>\d+)"
            r"|(?P<stage>a|rc)(?:"
            r"(?:(?<=a)(?P<ts>\d{12}))|(?:(?<=rc)(?P<rc>\d+))"
            r"))", version )
        stage = matched.group( 'stage' ) or 'f'
        patch = (
            matched.group( 'ts' ) if 'a' == stage
            else (
                matched.group( 'rc' ) if 'rc' == stage
                else matched.group( 'patch' ) ) )
        return kind(
            stage, matched.group( 'major' ), matched.group( 'minor' ), patch )

    def __init__( self, stage, major, minor, patch ):
        if stage not in ( 'a', 'rc', 'f' ):
            # TODO: Use 'expire' instead of 'invoke.Exit'.
            from invoke import Exit
            raise Exit( f"Bad stage: {stage}" )
        self.stage = stage
        self.major = int( major )
        self.minor = int( minor )
        self.patch = int( patch )

    def __str__( self ):
        stage, patch = self.stage, self.patch
        return ''.join( filter( None, (
            f"{self.major}", f".{self.minor}",
            f".{patch}" if 'f' == stage else '',
            f"{stage}{patch}" if stage in ( 'a', 'rc' ) else '' ) ) )

    def as_bumped( self, piece ):
        ''' Returns a derivative of the version,
            altered according to current state and desired modification. '''
        # TODO: Use 'expire' instead of 'invoke.Exit'.
        from invoke import Exit
        Version_ = type( self )
        stage, major, minor, patch = (
            self.stage, self.major, self.minor, self.patch )
        if 'stage' == piece:
            if 'a' == stage: return Version_( 'rc', major, minor, 1 )
            if 'rc' == stage: return Version_( 'f', major, minor, 0 )
            raise Exit( 'Cannot bump last stage.' )
        from datetime import datetime as DateTime
        timestamp = DateTime.utcnow( ).strftime( '%Y%m%d%H%M' )
        if 'patch' == piece:
            if 'a' == stage:
                return Version_( 'a', major, minor, timestamp )
            return Version_( stage, major, minor, patch + 1 )
        if 'major' == piece:
            return Version_( 'a', major + 1, 0, timestamp )
        if 'minor' == piece:
            return Version_( 'a', major, minor + 1, timestamp )
        raise Exit( f"Unknown kind of piece: {piece}" )
