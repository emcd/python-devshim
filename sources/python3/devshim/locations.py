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


# TODO: Reduce scope of this module. Allow other modules to calculate their own
#       locations of interest on demand rather than maintain a central
#       registry. I.e., this module should only contain the high-level skeleton
#       and not be aware of domain-specific details.
# TODO: Remove project/auxiliary dichotomy. Devshim should only care about the
#       project's sources, tests, etc... and its own configuration and state.
#       Should not need to be aware of its own sources from the project's
#       context, especially as they may be an installed package rather than a
#       submodule.


from . import base as __


def assemble( ):
    ''' Assembles project file system locations from configuration. '''
    locations = __.SimpleNamespace(
        auxiliary = __.configuration[ 'auxiliary_path' ],
        project = __.configuration[ 'project_path' ],
    )
    locations.local = locations.project / '.local'
    locations.artifacts = _calculate_artifacts_locations( locations )
    locations.caches = _calculate_caches_locations( locations )
    locations.configuration = _calculate_configuration_locations( locations )
    locations.environments = locations.local / 'environments'
    locations.scm_modules = _calculate_scm_modules_locations( locations )
    locations.state = _calculate_state_locations( locations )
    locations.scripts = _calculate_scripts_locations( locations )
    locations.sources = _calculate_sources_locations( locations )
    locations.tests = _calculate_tests_locations( locations )
    return _create_namespace_recursive( locations.__dict__ )


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


def _calculate_artifacts_locations( locations ):
    artifacts_path = locations.local / 'artifacts'
    html_path = artifacts_path / 'html'
    return __.SimpleNamespace(
        SELF = artifacts_path,
        sdists = artifacts_path / 'sdists',
        sphinx_html = html_path / 'sphinx',
        sphinx_linkcheck = artifacts_path / 'sphinx-linkcheck',
        wheels = artifacts_path / 'wheels',
    )


def _calculate_caches_locations( locations ):
    caches_path = locations.local / 'caches'
    packages_path = caches_path / 'packages'
    return __.SimpleNamespace(
        SELF = caches_path,
        DEV = __.SimpleNamespace(
            repositories = caches_path / f"{__package__}/repositories",
        ),
        hypothesis = caches_path / 'hypothesis',
        # TODO: Move 'packages' under 'DEV'.
        packages = __.SimpleNamespace(
            python3 = packages_path / 'python3',
        ),
        setuptools = caches_path / 'setuptools',
        sphinx = caches_path / 'sphinx',
    )


def _calculate_configuration_locations( locations ):
    configuration_path = locations.local / 'configuration'
    return __.SimpleNamespace(
        bumpversion = configuration_path / 'bumpversion.cfg',
        devshim = __.SimpleNamespace(
            python = configuration_path / 'devshim/python.toml',
        ),
        pre_commit = configuration_path / 'pre-commit.yaml',
        # TODO? Move 'pypackages.toml' to Devshim config path.
        #       Or move into 'pyproject.toml'.
        pypackages = configuration_path / 'pypackages.toml',
        # TODO: Move 'pypackages.fixtures.toml' to data path.
        pypackages_fixtures = configuration_path / 'pypackages.fixtures.toml',
        pyproject = locations.project / 'pyproject.toml',
    )


def _calculate_scm_modules_locations( locations ):
    return __.SimpleNamespace(
        aux = locations.auxiliary / 'scm-modules',
        prj = locations.local / 'scm-modules',
    )


def _calculate_scripts_locations( locations ):
    auxiliary_path = locations.auxiliary / 'scripts'
    project_path = locations.project / 'scripts'
    return __.SimpleNamespace(
        aux = __.SimpleNamespace(
            python3 = auxiliary_path / 'python3',
        ),
        prj = __.SimpleNamespace(
            python3 = project_path / 'python3',
        ),
    )


def _calculate_sources_locations( locations ):
    auxiliary_path = locations.auxiliary / 'sources'
    project_path = locations.project / 'sources'
    return __.SimpleNamespace(
        aux = __.SimpleNamespace(
            python3 = auxiliary_path / 'python3',
        ),
        prj = __.SimpleNamespace(
            python3 = project_path / 'python3',
            sphinx = project_path / 'sphinx',
        ),
    )


def _calculate_state_locations( locations ):
    location = locations.local / 'state'
    my_location = location / __.__package__
    return __.SimpleNamespace(
        SELF = location,
        DEV = __.SimpleNamespace(
            SELF = my_location,
        ),
    )


def _calculate_tests_locations( locations ):
    auxiliary_path = locations.auxiliary / 'tests'
    project_path = locations.project / 'tests'
    return __.SimpleNamespace(
        aux = __.SimpleNamespace(
            python3 = auxiliary_path / 'python3',
        ),
        prj = __.SimpleNamespace(
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
