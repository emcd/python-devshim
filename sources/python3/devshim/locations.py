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
    locations.data = _calculate_data_locations( locations )
    locations.configuration = _calculate_configuration_locations( locations )
    locations.environments = locations.local / 'environments'
    locations.scm_modules = _calculate_scm_modules_locations( locations )
    locations.state = _calculate_state_locations( locations )
    locations.sources = _calculate_sources_locations( locations )
    locations.tests = _calculate_tests_locations( locations )
    return __.create_immutable_namespace( locations )


def calculate_user_directories( ):
    ''' Calculates user directory locations in platform-specific manner. '''
    # TODO: Assert existence of 'platformdirs' package.
    from platformdirs import user_cache_path, user_data_path
    from .data import project_name
    caches_location = user_cache_path( appname = project_name )
    data_location = user_data_path( appname = project_name )
    return __.create_immutable_namespace( dict(
        artifacts = caches_location / 'artifacts',
        caches = caches_location,
        data = data_location,
        installations = data_location / 'installations',
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
    return __.SimpleNamespace(
        SELF = caches_path,
        DEV = __.SimpleNamespace(
            repositories = caches_path / f"{__package__}/repositories",
        ),
        hypothesis = caches_path / 'hypothesis',
        setuptools = caches_path / 'setuptools',
        sphinx = caches_path / 'sphinx',
    )


def _calculate_configuration_locations( locations ):
    location = locations.local / 'configuration'
    my_location = location / __.__package__
    return __.SimpleNamespace(
        SELF = location,
        DEV = __.SimpleNamespace(
            SELF = my_location,
        ),
        bumpversion = location / 'bumpversion.cfg',
        # TODO: Remove. Use 'DEV' entry instead.
        devshim = __.SimpleNamespace(
            python = location / 'devshim/python.toml',
        ),
        pre_commit = location / 'pre-commit.yaml',
        # TODO? Move 'pypackages.toml' to Devshim config path.
        #       Or move into 'pyproject.toml'.
        pypackages = location / 'pypackages.toml',
        # TODO: Move 'pypackages.fixtures.toml' to state path.
        pypackages_fixtures = location / 'pypackages.fixtures.toml',
        pyproject = locations.project / 'pyproject.toml',
    )


def _calculate_data_locations( locations ):
    location = locations.local / 'data'
    my_location = location / __.__package__
    return __.SimpleNamespace(
        SELF = location,
        DEV = __.SimpleNamespace(
            SELF = my_location,
        ),
    )


def _calculate_scm_modules_locations( locations ):
    return __.SimpleNamespace(
        aux = locations.auxiliary / 'scm-modules',
        prj = locations.local / 'scm-modules',
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
