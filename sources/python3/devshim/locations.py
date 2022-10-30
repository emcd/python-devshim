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


''' Constants and utilities for locations. '''


# TODO: Read fs structure from a JSON file.
#       YAML would be ideal but Python stdlib has no innate support.


# TODO? Early importation of immutable namespace class.
from types import SimpleNamespace as _SimpleNamespace


def _calculate_paths( ):
    from .base import configuration
    paths_ = _SimpleNamespace(
        auxiliary = configuration[ 'auxiliary_path' ],
        project = configuration[ 'project_path' ],
    )
    paths_.local = paths_.project / '.local'
    paths_.artifacts = _calculate_artifacts_paths( paths_ )
    paths_.caches = _calculate_caches_paths( paths_ )
    paths_.configuration = _calculate_configuration_paths( paths_ )
    paths_.environments = paths_.local / 'environments'
    paths_.scm_modules = _calculate_scm_modules_paths( paths_ )
    paths_.state = paths_.local / 'state'
    paths_.scripts = _calculate_scripts_paths( paths_ )
    paths_.sources = _calculate_sources_paths( paths_ )
    paths_.tests = _calculate_tests_paths( paths_ )
    return paths_


def _calculate_artifacts_paths( paths_ ):
    artifacts_path = paths_.local / 'artifacts'
    html_path = artifacts_path / 'html'
    return _SimpleNamespace(
        SELF = artifacts_path,
        sdists = artifacts_path / 'sdists',
        sphinx_html = html_path / 'sphinx',
        sphinx_linkcheck = artifacts_path / 'sphinx-linkcheck',
        wheels = artifacts_path / 'wheels',
    )


def _calculate_caches_paths( paths_ ):
    caches_path = paths_.local / 'caches'
    packages_path = caches_path / 'packages'
    platforms_path = caches_path / 'platforms'
    utilities_path = caches_path / 'utilities'
    return _SimpleNamespace(
        SELF = caches_path,
        hypothesis = caches_path / 'hypothesis',
        packages = _SimpleNamespace(
            python3 = packages_path / 'python3',
        ),
        platforms = _SimpleNamespace(
            python3 = platforms_path / 'python3',
        ),
        setuptools = caches_path / 'setuptools',
        sphinx = caches_path / 'sphinx',
        utilities = _SimpleNamespace(
            python_build = utilities_path / 'python-build',
        ),
    )


def _calculate_configuration_paths( paths_ ):
    configuration_path = paths_.local / 'configuration'
    return _SimpleNamespace(
        asdf = paths_.project / '.tool-versions',
        bumpversion = configuration_path / 'bumpversion.cfg',
        pre_commit = configuration_path / 'pre-commit.yaml',
        pypackages = configuration_path / 'pypackages.toml',
        pypackages_fixtures = configuration_path / 'pypackages.fixtures.toml',
        pyproject = paths_.project / 'pyproject.toml',
    )


def _calculate_scm_modules_paths( paths_ ):
    return _SimpleNamespace(
        aux = paths_.auxiliary / 'scm-modules',
        prj = paths_.local / 'scm-modules',
    )


def _calculate_scripts_paths( paths_ ):
    auxiliary_path = paths_.auxiliary / 'scripts'
    project_path = paths_.project / 'scripts'
    return _SimpleNamespace(
        aux = _SimpleNamespace(
            python3 = auxiliary_path / 'python3',
        ),
        prj = _SimpleNamespace(
            python3 = project_path / 'python3',
        ),
    )


def _calculate_sources_paths( paths_ ):
    auxiliary_path = paths_.auxiliary / 'sources'
    project_path = paths_.project / 'sources'
    return _SimpleNamespace(
        aux = _SimpleNamespace(
            python3 = auxiliary_path / 'python3',
        ),
        prj = _SimpleNamespace(
            python3 = project_path / 'python3',
            sphinx = project_path / 'sphinx',
        ),
    )


def _calculate_tests_paths( paths_ ):
    auxiliary_path = paths_.auxiliary / 'tests'
    project_path = paths_.project / 'tests'
    return _SimpleNamespace(
        aux = _SimpleNamespace(
            python3 = auxiliary_path / 'python3',
        ),
        prj = _SimpleNamespace(
            python3 = project_path / 'python3',
        ),
    )


# TODO: Add hook for this to an on-demand cache object.
#       Compute only on '__getattr__' for it.
paths = _calculate_paths( )
