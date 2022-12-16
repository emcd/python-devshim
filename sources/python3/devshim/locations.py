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


''' Constants and utilities for locations.

    Locations are modeled in Python code rather than a data language
    or DSL, so that a separate file does not need to be loaded during
    early startup and because the Python code is more flexible than
    data languages (JSON, TOML, YAML, etc...) and nearly as compact.
    A JSON model was produced at one point and, while it saved some
    space, it did not justify the complexity of reading it and mapping
    it (with variable interpolations) into a hierarchical Python data
    structure, such as this module provides. YAML would be slightly more
    compact but it is not supported in the Python standard library. '''


# TODO: Work directly with dictionary.
#       Conversion to immutable namespace will happen on return from public
#       interface.
from types import SimpleNamespace as _SimpleNamespace


def assemble( ):
    ''' Assembles project file system locations from configuration. '''
    from .base import configuration
    paths = _SimpleNamespace(
        auxiliary = configuration[ 'auxiliary_path' ],
        project = configuration[ 'project_path' ],
    )
    paths.local = paths.project / '.local'
    paths.artifacts = _calculate_artifacts_paths( paths )
    paths.caches = _calculate_caches_paths( paths )
    paths.configuration = _calculate_configuration_paths( paths )
    paths.environments = paths.local / 'environments'
    paths.scm_modules = _calculate_scm_modules_paths( paths )
    paths.state = paths.local / 'state'
    paths.scripts = _calculate_scripts_paths( paths )
    paths.sources = _calculate_sources_paths( paths )
    paths.tests = _calculate_tests_paths( paths )
    return _create_namespace_recursive( paths.__dict__ )


def calculate_user_directories( ):
    ''' Calculates user directory locations in platform-specific manner. '''
    # TODO: Assert existence of 'platformdirs' package.
    from platformdirs import user_cache_path, user_data_path
    from .data import project_name
    data_path = user_data_path( appname = project_name )
    return _create_namespace_recursive( dict(
        caches = user_cache_path( appname = project_name ),
        data = data_path,
        installations = data_path / 'installations',
    ) )


def _calculate_artifacts_paths( paths ):
    artifacts_path = paths.local / 'artifacts'
    html_path = artifacts_path / 'html'
    return _SimpleNamespace(
        SELF = artifacts_path,
        sdists = artifacts_path / 'sdists',
        sphinx_html = html_path / 'sphinx',
        sphinx_linkcheck = artifacts_path / 'sphinx-linkcheck',
        wheels = artifacts_path / 'wheels',
    )


def _calculate_caches_paths( paths ):
    caches_path = paths.local / 'caches'
    packages_path = caches_path / 'packages'
    platforms_path = caches_path / 'platforms'
    return _SimpleNamespace(
        SELF = caches_path,
        DEV = _SimpleNamespace(
            repositories = caches_path / f"{__package__}/repositories",
        ),
        hypothesis = caches_path / 'hypothesis',
        packages = _SimpleNamespace(
            python3 = packages_path / 'python3',
        ),
        platforms = _SimpleNamespace(
            python3 = platforms_path / 'python3',
        ),
        setuptools = caches_path / 'setuptools',
        sphinx = caches_path / 'sphinx',
    )


def _calculate_configuration_paths( paths ):
    configuration_path = paths.local / 'configuration'
    return _SimpleNamespace(
        asdf = paths.project / '.tool-versions',
        bumpversion = configuration_path / 'bumpversion.cfg',
        devshim = _SimpleNamespace(
            python = _SimpleNamespace(
                packages = configuration_path.joinpath(
                    'devshim', 'python', 'packages.toml' ),
                versions = configuration_path.joinpath(
                    'devshim', 'python', 'versions.toml' ),
            ),
        ),
        pre_commit = configuration_path / 'pre-commit.yaml',
        # TODO: Move 'pypackages.toml' to Devshim config path.
        pypackages = configuration_path / 'pypackages.toml',
        # TODO: Move 'pypackages.fixtures.toml' to data path.
        pypackages_fixtures = configuration_path / 'pypackages.fixtures.toml',
        pyproject = paths.project / 'pyproject.toml',
    )


def _calculate_scm_modules_paths( paths ):
    return _SimpleNamespace(
        aux = paths.auxiliary / 'scm-modules',
        prj = paths.local / 'scm-modules',
    )


def _calculate_scripts_paths( paths ):
    auxiliary_path = paths.auxiliary / 'scripts'
    project_path = paths.project / 'scripts'
    return _SimpleNamespace(
        aux = _SimpleNamespace(
            python3 = auxiliary_path / 'python3',
        ),
        prj = _SimpleNamespace(
            python3 = project_path / 'python3',
        ),
    )


def _calculate_sources_paths( paths ):
    auxiliary_path = paths.auxiliary / 'sources'
    project_path = paths.project / 'sources'
    return _SimpleNamespace(
        aux = _SimpleNamespace(
            python3 = auxiliary_path / 'python3',
        ),
        prj = _SimpleNamespace(
            python3 = project_path / 'python3',
            sphinx = project_path / 'sphinx',
        ),
    )


def _calculate_tests_paths( paths ):
    auxiliary_path = paths.auxiliary / 'tests'
    project_path = paths.project / 'tests'
    return _SimpleNamespace(
        aux = _SimpleNamespace(
            python3 = auxiliary_path / 'python3',
        ),
        prj = _SimpleNamespace(
            python3 = project_path / 'python3',
        ),
    )


def _create_namespace_recursive( dictionary ):
    from collections.abc import Mapping as AbstractDictionary
    from inspect import isfunction as is_function
    from types import SimpleNamespace
    namespace = { }
    for name, value in dictionary.items( ):
        # TODO: Filter for valid Python identifiers.
        # TODO: Filter for public names.
        if is_function( value ):
            namespace[ name ] = staticmethod( value )
        elif isinstance( value, AbstractDictionary ):
            namespace[ name ] = _create_namespace_recursive( value )
        elif isinstance( value, SimpleNamespace ):
            namespace[ name ] = _create_namespace_recursive( value.__dict__ )
        else: namespace[ name ] = value
    namespace[ '__slots__' ] = ( )
    class_ = type( 'Namespace', ( ), namespace )
    return class_( )
