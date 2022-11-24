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

''' Project maintenance tasks. '''


from ..base import assert_sanity as _assert_sanity
_assert_sanity( )


from lockup import NamespaceClass as _NamespaceClass
class __( metaclass = _NamespaceClass ):

    import re

    from itertools import chain
    from pathlib import Path
    from urllib.error import URLError as UrlError
    from urllib.parse import urlparse as parse_url
    from urllib.request import urlopen as access_url

    from invoke import call

    from ..base import execute_external
    from ..environments import (
        derive_venv_variables,
        test_package_executable,
    )
    from ..locations import paths
    from ..packages import Version
    from ..project import (
        discover_project_name,
        discover_project_version,
    )

    project_name = discover_project_name( )
    # https://www.sphinx-doc.org/en/master/man/sphinx-build.html
    sphinx_options = f"-j auto -d {paths.caches.sphinx} -n -T"


from ._base import task as _task


@_task( )
def ease(
    context, # pylint: disable=unused-argument
    shell_name = None,
    function_name = 'devshim',
    with_completions = False
):
    ''' Prints shell functions for easy invocation of development shim. '''
    from ..user_interface import generate_cli_functions
    print( generate_cli_functions(
        shell_name, function_name, with_completions ) )


@_task( 'Install: Git Pre-Commit Hooks' )
def install_git_hooks( context ): # pylint: disable=unused-argument
    ''' Installs hooks to check goodness of code changes before commit. '''
    process_environment = __.derive_venv_variables( )
    __.execute_external(
        f"pre-commit install --config {__.paths.configuration.pre_commit} "
        f"--hook-type pre-commit --install-hooks",
        capture_output = False, env = process_environment )
    __.execute_external(
        f"pre-commit install --config {__.paths.configuration.pre_commit} "
        f"--hook-type pre-push --install-hooks",
        capture_output = False, env = process_environment )


@_task(
    'Install: Python Release',
    version_expansion = 'declared Python versions',
)
def install_python( context, version ): # pylint: disable=unused-argument
    ''' Installs requested Python version.

        This task requires Internet access and may take some time. '''
    __.execute_external(
        f"asdf install python {version}", capture_output = False )


@_task(
    'Build: Python Virtual Environment',
    version_expansion = 'declared Python versions',
)
def build_python_venv( context, version, overwrite = False ):
    ''' Creates virtual environment for requested Python version. '''
    # TODO? Install exact packages, if possible.
    from ._invoke import extract_task_invocable
    extract_task_invocable( install_python )( context, version )
    from .. import environments
    environments.build_python_venv( version, overwrite = overwrite )
    # TODO: Test new virtual environment.


@_task(
    task_nomargs = dict(
        pre = (
            __.call( build_python_venv, version = 'ALL' ),
            __.call( install_git_hooks ),
        ),
    ),
)
def bootstrap( context ): # pylint: disable=unused-argument
    ''' Bootstraps the development environment and utilities. '''


@_task( 'Clean: Python Caches' )
def clean_pycaches( context ): # pylint: disable=unused-argument
    ''' Removes all caches of compiled CPython bytecode. '''
    from ..fs_utilities import unlink_recursively
    anchors = (
        __.paths.sources.aux.python3,
        __.paths.sources.prj.python3,
        __.paths.sources.prj.sphinx,
        __.paths.tests.prj.python3,
    )
    for path in __.chain.from_iterable( map(
        lambda anchor: anchor.rglob( '__pycache__' ), anchors
    ) ): unlink_recursively( path )


@_task( 'Clean: Tool Caches' )
def clean_tool_caches( context, include_development_support = False ): # pylint: disable=unused-argument
    ''' Clears the caches used by code generation and testing utilities. '''
    anchors = __.paths.caches.SELF.glob( '*' )
    ignorable_paths = set( __.paths.caches.SELF.glob( '*/.gitignore' ) )
    if not include_development_support:
        from ..platforms import active_python_abi_label
        ds_path = __.paths.caches.packages.python3 / active_python_abi_label
        ignorable_paths.add( __.paths.caches.packages.python3 )
        ignorable_paths.add( ds_path )
        ignorable_paths.update( ds_path.rglob( '*' ) )
    dirs_stack = [ ]
    for path in __.chain.from_iterable( map(
        lambda anchor: anchor.rglob( '*' ), anchors
    ) ):
        if path in ignorable_paths: continue
        if path.is_dir( ) and not path.is_symlink( ):
            dirs_stack.append( path )
            continue
        path.unlink( )
    while dirs_stack: dirs_stack.pop( ).rmdir( )
    # Regnerate development support packages cache, if necessary.
    if include_development_support:
        from ..packages import ensure_python_packages
        ensure_python_packages( domain = 'development' )


@_task(
    'Clean: Unused Python Packages',
    version_expansion = 'declared Python virtual environments',
)
def clean_python_packages( context, version = None ): # pylint: disable=unused-argument
    ''' Removes unused Python packages. '''
    process_environment = __.derive_venv_variables( version = version )
    from ..platforms import pep508_identify_python
    identifier = pep508_identify_python( version = version )
    from ..packages import (
        execute_pip_with_requirements,
        indicate_current_python_packages,
        indicate_python_packages,
    )
    _, fixtures = indicate_python_packages( identifier = identifier )
    requested = frozenset( fixture[ 'name' ] for fixture in fixtures )
    installed = frozenset(
        entry.requirement.name
        for entry
        in indicate_current_python_packages( process_environment ) )
    requirements_text = '\n'.join(
        installed - requested - { __.project_name } )
    if not requirements_text: return
    execute_pip_with_requirements(
        process_environment, 'uninstall', requirements_text,
        pip_options = ( '--yes', ) )


@_task( )
def clean( context, version = None ):
    ''' Cleans all caches. '''
    clean_python_packages( context, version = version )
    clean_pycaches( context )
    clean_tool_caches( context )


@_task(
    'Lint: Package Security',
    version_expansion = 'declared Python virtual environments',
)
def check_security_issues( context, version = None ): # pylint: disable=unused-argument
    ''' Checks for security issues in utilized packages and tools.

        This task requires Internet access and may take some time. '''
    process_environment = __.derive_venv_variables( version = version )
    __.execute_external(
        f"safety check", capture_output = False, env = process_environment )


@_task( 'Freshen: Version Manager' )
def freshen_asdf( context ): # pylint: disable=unused-argument
    ''' Asks Asdf to update itself.

        This task requires Internet access and may take some time. '''
    __.execute_external( 'asdf update', capture_output = False )
    __.execute_external( 'asdf plugin update python', capture_output = False )
    # TODO: Preserve this call after 'freshen_asdf' has been removed.
    from ..platforms import install_python_builder
    install_python_builder( )


@_task( task_nomargs = dict( pre = ( freshen_asdf, ), ), )
def freshen_python( context, version = None ): # pylint: disable=unused-argument
    ''' Updates supported Python minor version to latest patch.

        If version is 'ALL', then all supported Pythons are targeted.

        This task requires Internet access and may take some time. '''
    from ..platforms import (
        detect_vmgr_python_version,
        indicate_python_versions_support,
    )
    original_versions = indicate_python_versions_support( )
    if 'ALL' == version: versions = original_versions
    else: versions = ( version or detect_vmgr_python_version( ), )
    obsolete_identifiers = set( )
    version_replacements = { }
    for version_ in versions:
        replacement, identifier = _freshen_python( version_ )
        version_replacements.update( replacement )
        if None is not identifier: obsolete_identifiers.add( identifier )
    # Can only update record of local versions after they are installed.
    successor_versions = [
        version_replacements.get( version_, version_ )
        for version_ in original_versions ]
    __.execute_external( "asdf local python {versions}".format(
        versions = ' '.join( successor_versions ) ), capture_output = False )
    # Erase packages fixtures for versions which are no longer extant.
    from ..packages import delete_python_packages_fixtures
    delete_python_packages_fixtures( obsolete_identifiers )


def _freshen_python( version ):
    ''' Updates supported Python minor version to latest patch. '''
    from ..user_interface import render_boxed_title
    render_boxed_title( 'Freshen: Python Version', supplement = version )
    from .. import platforms
    return platforms.freshen_python( version )


@_task(
    'Freshen: Python Package Versions',
    version_expansion = 'declared Python virtual environments',
)
def freshen_python_packages( context, version = None ):
    ''' Updates declared Python packages in Python virtual environment. '''
    process_environment = __.derive_venv_variables( version = version )
    from ..platforms import pep508_identify_python
    identifier = pep508_identify_python( version = version )
    from ..packages import (
        calculate_python_packages_fixtures,
        install_python_packages,
        record_python_packages_fixtures,
    )
    install_python_packages( process_environment )
    fixtures = calculate_python_packages_fixtures( process_environment )
    record_python_packages_fixtures( identifier, fixtures )
    check_security_issues( context, version = version )
    test( context, version = version )


@_task( 'Freshen: Git Modules' )
def freshen_git_modules( context ): # pylint: disable=unused-argument
    ''' Performs recursive update of all Git modules.

        This task requires Internet access and may take some time. '''
    __.execute_external(
        'git submodule update --init --recursive --remote',
        capture_output = False )


@_task( 'Freshen: Git Hooks' )
def freshen_git_hooks( context ): # pylint: disable=unused-argument
    ''' Updates Git hooks to latest tagged release.

        This task requires Internet access and may take some time. '''
    process_environment = __.derive_venv_variables( )
    __.execute_external(
        f"pre-commit autoupdate --config {__.paths.configuration.pre_commit}",
        capture_output = False, env = process_environment )


@_task(
    task_nomargs = dict(
        pre = (
            __.call( clean ),
            __.call( freshen_git_modules ),
            __.call( freshen_python, version = 'ALL' ),
            __.call( freshen_python_packages, version = 'ALL' ),
            __.call( freshen_git_hooks ),
        ),
    ),
)
def freshen( context ): # pylint: disable=unused-argument
    ''' Performs the various freshening tasks, cleaning first.

        This task requires Internet access and may take some time. '''


@_task(
    'Lint: Bandit',
    version_expansion = 'declared Python virtual environments',
)
def lint_bandit( context, version = None ): # pylint: disable=unused-argument
    ''' Security checks the source code with Bandit. '''
    files = _lint_targets_default
    files_str = ' '.join( map( str, files ) )
    process_environment = __.derive_venv_variables( version = version )
    __.execute_external(
        "bandit --recursive "
        f"--configfile {__.paths.configuration.pyproject} {files_str}",
        capture_output = False, env = process_environment )


@_task(
    'Lint: Mypy',
    task_nomargs = dict( iterable = ( 'packages', 'modules', 'files', ), ),
    version_expansion = 'declared Python virtual environments',
)
def lint_mypy( context, packages, modules, files, version = None ): # pylint: disable=unused-argument
    ''' Lints the source code with Mypy. '''
    process_environment = __.derive_venv_variables( version = version )
    # TODO: Check executable in '_task'.
    if not __.test_package_executable( 'mypy', process_environment ): return
    if not packages and not modules and not files:
        # TODO: Is this the best approach?
        files = _lint_targets_default
    packages_str = ' '.join( map(
        lambda package: f"--package {package}", packages ) )
    modules_str = ' '.join( map(
        lambda module: f"--module {module}", modules ) )
    files_str = ' '.join( map( str, files ) )
    __.execute_external(
        f"mypy {packages_str} {modules_str} {files_str}",
        capture_output = False, env = process_environment )


@_task(
    'Lint: Pylint',
    task_nomargs = dict( iterable = ( 'targets', 'checks', ), ),
    version_expansion = 'declared Python virtual environments',
)
def lint_pylint( context, targets, checks, version = None ): # pylint: disable=unused-argument
    ''' Lints the source code with Pylint. '''
    process_environment = __.derive_venv_variables( version = version )
    # TODO: Check executable in '_task'.
    if not __.test_package_executable( 'pylint', process_environment ): return
    reports_str = '--reports=no --score=no' if targets or checks else ''
    if not targets: targets = _lint_targets_default
    targets_str = ' '.join( map( str, targets ) )
    checks_str = (
        "--disable=all --enable={}".format( ','.join( checks ) )
        if checks else '' )
    __.execute_external(
        f"pylint {reports_str} {checks_str} --recursive yes {targets_str}",
        capture_output = False, env = process_environment )


@_task(
    'Lint: Semgrep',
    version_expansion = 'declared Python virtual environments',
)
def lint_semgrep( context, version = None ): # pylint: disable=unused-argument
    ''' Lints the source code with Semgrep. '''
    process_environment = __.derive_venv_variables( version = version )
    # TODO: Check executable in '_task'.
    if not __.test_package_executable( 'semgrep', process_environment ): return
    files = _lint_targets_default
    files_str = ' '.join( map( str, files ) )
    sgconfig_path = __.paths.scm_modules.aux.joinpath(
        'semgrep-rules', 'python', 'lang' )
    __.execute_external(
        #f"strace -ff -tt --string-limit=120 --output=strace/semgrep "
        f"semgrep --config {sgconfig_path} --error --use-git-ignore "
        f"{files_str}", capture_output = False, env = process_environment )


_lint_targets_default = (
    __.paths.sources.prj.python3,
    __.paths.scripts.prj.python3,
    __.paths.tests.prj.python3,
    __.paths.project / 'develop.py',
    __.paths.project / 'setup.py',
    __.paths.sources.prj.sphinx / 'conf.py',
)


@_task( version_expansion = 'declared Python virtual environments' )
def lint( context, version = None ):
    ''' Lints the source code. '''
    lint_pylint( context, targets = ( ), checks = ( ), version = version )
    lint_semgrep( context, version = version )
    lint_mypy(
        context,
        packages = ( ), modules = ( ), files = ( ), version = version )
    lint_bandit( context, version = version )


@_task( 'Artifact: Code Coverage Report' )
def report_coverage( context ): # pylint: disable=unused-argument
    ''' Combines multiple code coverage results into a single report. '''
    process_environment = __.derive_venv_variables( )
    __.execute_external(
        'coverage combine', capture_output = False, env = process_environment )
    __.execute_external(
        'coverage report', capture_output = False, env = process_environment )
    __.execute_external(
        'coverage html', capture_output = False, env = process_environment )
    __.execute_external(
        'coverage xml', capture_output = False, env = process_environment )


@_task(
    version_expansion = 'declared Python virtual environments',
)
def test( context, ensure_sanity = True, version = None ):
    ''' Runs the test suite in Python virtual environment. '''
    clean( context, version = version )
    if ensure_sanity: lint( context, version = version )
    from ..user_interface import render_boxed_title
    render_boxed_title( 'Test: Unit + Code Coverage', supplement = version )
    process_environment = __.derive_venv_variables( version = version )
    process_environment.update( dict(
        HYPOTHESIS_STORAGE_DIRECTORY = __.paths.caches.hypothesis,
        PYTHONUNBUFFERED = 'TRUE', # Ensure complete crash output.
    ) )
    __.execute_external(
        f"coverage run --source {__.project_name}",
        capture_output = False, env = process_environment )


@_task( 'Test: Documentation URLs' )
def check_urls( context ): # pylint: disable=unused-argument
    ''' Checks the HTTP URLs in the documentation for liveness. '''
    process_environment = __.derive_venv_variables( )
    __.execute_external(
        f"sphinx-build -b linkcheck {__.sphinx_options} "
        f"{__.paths.sources.prj.sphinx} {__.paths.artifacts.sphinx_linkcheck}",
        capture_output = False, env = process_environment )


@_task( 'Test: README Render' )
def check_readme( context ): # pylint: disable=unused-argument
    ''' Checks that the README will render correctly on PyPI. '''
    path = _get_sdist_path( )
    process_environment = __.derive_venv_variables( )
    __.execute_external(
        f"twine check {path}",
        capture_output = False, env = process_environment )


@_task(
    'Artifact: Source Distribution',
    task_nomargs = dict( post = ( check_readme, ), ),
)
def make_sdist( context, ensure_sanity = True, signature = True ):
    ''' Packages the Python sources for release. '''
    if ensure_sanity:
        test( context )
        check_urls( context )
    path = _get_sdist_path( )
    if path.exists( ): path.unlink( ) # TODO: Python 3.8: missing_ok = True
    process_environment = __.derive_venv_variables( )
    __.execute_external(
        f"python3 -m build --sdist --outdir {__.paths.artifacts.sdists}",
        capture_output = False, env = process_environment )
    if signature:
        from ..file_utilities import gpg_sign_file
        gpg_sign_file( path )


def _get_sdist_path( ):
    project_version = __.discover_project_version( )
    name = f"{__.project_name}-{project_version}.tar.gz"
    return __.paths.artifacts.sdists / name


@_task( 'Artifact: Python Wheel' )
def make_wheel( context, ensure_sanity = True, signature = True ):
    ''' Packages a Python wheel for release. '''
    make_sdist( context, ensure_sanity = ensure_sanity, signature = signature )
    path = _get_wheel_path( )
    if path.exists( ): path.unlink( ) # TODO: Python 3.8: missing_ok = True
    process_environment = __.derive_venv_variables( )
    __.execute_external(
        f"python3 -m build --wheel --outdir {__.paths.artifacts.wheels}",
        capture_output = False, env = process_environment )
    if signature:
        from ..file_utilities import gpg_sign_file
        gpg_sign_file( path )


def _get_wheel_path( ):
    project_version = __.discover_project_version( )
    name = f"{__.project_name}-{project_version}-py3-none-any.whl"
    return __.paths.artifacts.wheels / name


@_task(
    'Artifact: Documentation',
    task_nomargs = dict( pre = ( check_urls, ), ),
)
def make_html( context ): # pylint: disable=unused-argument
    ''' Generates documentation as HTML artifacts. '''
    from ..fs_utilities import unlink_recursively
    unlink_recursively( __.paths.artifacts.sphinx_html )
    process_environment = __.derive_venv_variables( )
    __.execute_external(
        f"sphinx-build -b html {__.sphinx_options} "
        f"{__.paths.sources.prj.sphinx} {__.paths.artifacts.sphinx_html}",
        capture_output = False, env = process_environment )


@_task( task_nomargs = dict( pre = ( clean, make_wheel, make_html, ), ), )
def make( context ): # pylint: disable=unused-argument
    ''' Generates all of the artifacts. '''


def _ensure_clean_workspace( ):
    ''' Error if version control reports any dirty or untracked files. '''
    result = __.execute_external( 'git status --short' )
    if result.stdout or result.stderr:
        # TODO: Use different error-handling mechanism.
        from invoke import Exit
        raise Exit( 'Dirty workspace. Please stash or commit changes.' )


@_task( 'Version: Adjust' )
def bump( context, piece ): # pylint: disable=unused-argument
    ''' Bumps a piece of the current version. '''
    _ensure_clean_workspace( )
    from ..file_utilities import assert_gpg_tty
    assert_gpg_tty( )
    project_version = __.discover_project_version( )
    current_version = __.Version.from_string( project_version )
    new_version = current_version.as_bumped( piece )
    if 'stage' == piece: part = 'release_class'
    elif 'patch' == piece:
        if current_version.stage in ( 'a', 'rc' ): part = 'prerelease'
        else: part = 'patch'
    else: part = piece
    process_environment = __.derive_venv_variables( )
    __.execute_external(
        f"bumpversion --config-file={__.paths.configuration.bumpversion}"
        f" --current-version {current_version}"
        f" --new-version {new_version}"
        f" {part}", capture_output = False, env = process_environment )


@_task(
    task_nomargs = dict( post = ( __.call( bump, piece = 'patch' ), ), ),
)
def bump_patch( context ): # pylint: disable=unused-argument
    ''' Bumps to next patch level. '''


@_task(
    task_nomargs = dict( post = ( __.call( bump, piece = 'stage' ), ), ),
)
def bump_stage( context ): # pylint: disable=unused-argument
    ''' Bumps to next release stage. '''


@_task( task_nomargs = dict( post = ( bump_stage, ), ), )
def branch_release( context, remote = 'origin' ): # pylint: disable=unused-argument
    ''' Makes a new branch for development torwards a release. '''
    from invoke import Exit  # TODO: Use different error-handling mechanism.
    _ensure_clean_workspace( )
    project_version = __.discover_project_version( )
    mainline_regex = __.re.compile(
        r'''^\s+HEAD branch:\s+(.*)$''', __.re.MULTILINE )
    mainline_branch = mainline_regex.search( __.execute_external(
        f"git remote show {remote}" ).stdout.strip( ) )[ 1 ]
    true_branch = __.execute_external(
        'git branch --show-current' ).stdout.strip( )
    if mainline_branch != true_branch:
        # TODO: Use different error-reporting mechanism.
        raise Exit( f"Cannot create release from branch: {true_branch}" )
    this_version = __.Version.from_string( project_version )
    stage = this_version.stage
    if 'a' != stage:
        # TODO: Use different error-reporting mechanism.
        raise Exit( f"Cannot create release from stage: {stage}" )
    target_branch = f"release-{this_version.major}.{this_version.minor}"
    __.execute_external(
        f"git checkout -b {target_branch}", capture_output = False )


@_task( 'Code Format: YAPF' )
def check_code_style( context, write_changes = False ): # pylint: disable=unused-argument
    ''' Checks code style of new changes. '''
    yapf_options = [ ]
    if write_changes: yapf_options.append( '--in-place --verbose' )
    yapf_options_string = ' '.join( yapf_options )
    from contextlib import ExitStack as ContextStack
    from shlex import split as split_command
    from subprocess import Popen, PIPE # nosec B404
    process_environment = __.derive_venv_variables( )
    contexts = ContextStack( )
    # nosemgrep: scm-modules.semgrep-rules.python.lang.security.audit.dangerous-subprocess-use-audit
    git_diff_process = contexts.enter_context( Popen( # nosec B603
        ( *split_command("git diff --unified=0 --no-color --"),
          *_lint_targets_default ), stdout = PIPE, text = True ) )
    # nosemgrep: scm-modules.semgrep-rules.python.lang.security.audit.dangerous-subprocess-use-audit
    yapf_diff_process = contexts.enter_context( Popen( # nosec B603
        split_command( f"yapf-diff {yapf_options_string}" ),
        env = process_environment,
        stdin = git_diff_process.stdout, text = True ) )
    with contexts:
        git_diff_process.stdout.close( )
        yapf_diff_process.communicate( )
    exit_code = git_diff_process.returncode or yapf_diff_process.returncode
    if exit_code: raise SystemExit( exit_code )


@_task( 'SCM: Push Branch with Tags' )
def push( context, remote = 'origin' ): # pylint: disable=unused-argument
    ''' Pushes commits on current branch, plus all tags. '''
    # TODO: Discover remote corresponding to current branch.
    _ensure_clean_workspace( )
    project_version = __.discover_project_version( )
    true_branch = __.execute_external(
        'git branch --show-current' ).stdout.strip( )
    this_version = __.Version.from_string( project_version )
    target_branch = f"release-{this_version.major}.{this_version.minor}"
    if true_branch == target_branch:
        __.execute_external(
            f"git push --set-upstream {remote} {true_branch}",
            capture_output = False )
    else: __.execute_external( 'git push', capture_output = False )
    __.execute_external(
        'git push --no-verify --tags', capture_output = False )


@_task( )
def check_pip_install( context, index_url = '', version = None ): # pylint: disable=unused-argument
    ''' Checks import of current package after installation via Pip. '''
    version = version or __.discover_project_version( )
    from ..user_interface import render_boxed_title
    render_boxed_title( f"Verify: Python Package Installation ({version})" )
    from subprocess import SubprocessError # nosec B404
    from tempfile import TemporaryDirectory
    from time import sleep
    from venv import create as create_venv
    with TemporaryDirectory( ) as venv_path:
        venv_path = __.Path( venv_path )
        create_venv( venv_path, clear = True, with_pip = True )
        index_url_option = ''
        if index_url: index_url_option = f"--index-url {index_url}"
        process_environment = __.derive_venv_variables( venv_path = venv_path )
        attempts_count_max = 2
        for attempts_count in range( attempts_count_max + 1 ):
            try:
                __.execute_external(
                    f"pip install {index_url_option} "
                    f"  {__.project_name}=={version}",
                    capture_output = False, env = process_environment )
            except SubprocessError:
                if attempts_count_max == attempts_count: raise
                sleep( 2 ** attempts_count )
            else: break
        python_import_command = (
            f"import {__.project_name}; "
            f"print( {__.project_name}.__version__ )" )
        __.execute_external(
            f"python -c '{python_import_command}'",
            capture_output = False, env = process_environment )


@_task( )
def check_pypi_integrity( context, version = None, index_url = '' ):
    ''' Checks integrity of project packages on PyPI.
        If no version is provided, the current project version is used.

        This task requires Internet access and may take some time. '''
    version = version or __.discover_project_version( )
    from ..user_interface import render_boxed_title
    render_boxed_title( f"Verify: Python Package Integrity ({version})" )
    from ..packages import retrieve_pypi_release_information
    release_info = retrieve_pypi_release_information(
        __.project_name, version, index_url = index_url )
    for package_info in release_info:
        url = package_info[ 'url' ]
        if not package_info.get( 'has_sig', False ):
            # TODO: Use different error-handling mechanism.
            from invoke import Exit
            raise Exit( f"No signature found for: {url}" )
        check_pypi_package( context, url )


# TODO: Move to '.packages' and separate retry logic from fetch logic.
def check_pypi_package( context, package_url ): # pylint: disable=unused-argument
    ''' Verifies signature on package. '''
    from ..file_utilities import assert_gpg_tty
    assert_gpg_tty( )
    package_filename = __.parse_url( package_url ).path.split( '/' )[ -1 ]
    from tempfile import TemporaryDirectory
    from time import sleep
    with TemporaryDirectory( ) as cache_path_raw:
        cache_path = __.Path( cache_path_raw )
        package_path = cache_path / package_filename
        signature_path = cache_path / f"{package_filename}.asc"
        attempts_count_max = 2
        for attempts_count in range( attempts_count_max + 1 ):
            try:
                with __.access_url( package_url ) as http_reader:
                    with package_path.open( 'wb' ) as file:
                        file.write( http_reader.read( ) )
                with __.access_url( f"{package_url}.asc" ) as http_reader:
                    with signature_path.open( 'wb' ) as file:
                        file.write( http_reader.read( ) )
            except __.UrlError:
                if attempts_count_max == attempts_count: raise
                sleep( 2 ** attempts_count )
            else: break
        __.execute_external(
            f"gpg --verify {signature_path}", capture_output = False )


@_task(
    task_nomargs = dict(
        pre = ( make, ),
        post = (
            __.call(
                check_pypi_integrity, index_url = 'https://test.pypi.org'
            ),
            __.call(
                check_pip_install, index_url = 'https://test.pypi.org/simple/'
            ),
        ),
    ),
)
def upload_test_pypi( context ): # pylint: disable=unused-argument
    ''' Publishes current sdist and wheels to Test PyPI. '''
    _upload_pypi( 'testpypi' )


@_task(
    task_nomargs = dict(
        pre = (
            __.call( upload_test_pypi ),
            __.call( test, version = 'ALL' ),
        ),
        post = ( check_pypi_integrity, check_pip_install, ),
    ),
)
def upload_pypi( context ): # pylint: disable=unused-argument
    ''' Publishes current sdist and wheels to PyPI. '''
    _upload_pypi( )


def _upload_pypi( repository_name = '' ):
    repository_option = ''
    task_name_suffix = ''
    if repository_name:
        repository_option = f"--repository {repository_name}"
        task_name_suffix = f" ({repository_name})"
    from ..user_interface import render_boxed_title
    render_boxed_title( f"Publication: PyPI{task_name_suffix}" )
    artifacts = _get_pypi_artifacts( )
    process_environment = __.derive_venv_variables( )
    process_environment.update( _get_pypi_credentials( repository_name ) )
    __.execute_external(
        f"twine upload --skip-existing --verbose {repository_option} "
        f"{artifacts}", capture_output = False, env = process_environment )


def _get_pypi_artifacts( ):
    stems = ( _get_sdist_path( ), _get_wheel_path( ), )
    return ' '.join( __.chain(
        map( str, stems ), map( lambda p: f"{p}.asc", stems ) ) )


def _get_pypi_credentials( repository_name ):
    from tomli import load as load_toml
    if '' == repository_name: repository_name = 'pypi'
    with open( __.paths.project / 'credentials.toml', 'rb' ) as file:
        table = load_toml( file )[ repository_name ]
    return {
        'TWINE_USERNAME': table[ 'username' ],
        'TWINE_PASSWORD': table[ 'password' ], }


# Inspiration: https://stackoverflow.com/a/58993849/14833542
@_task(
    'Publication: Github Pages',
    task_nomargs = dict( pre = ( test, make_html, ), ),
)
def upload_github_pages( context ): # pylint: disable=unused-argument
    ''' Publishes Sphinx HTML output to Github Pages for project. '''
    # Use relative path, since 'git subtree' needs it.
    html_path = __.paths.artifacts.sphinx_html.relative_to( __.paths.project )
    nojekyll_path = html_path / '.nojekyll'
    target_branch = 'documentation'
    from contextlib import ExitStack as ContextStack
    from subprocess import SubprocessError # nosec B404
    from ..base import springy_chdir
    with ContextStack( ) as contexts:
        # Work from project root, since 'git subtree' requires relative paths.
        contexts.enter_context( springy_chdir( __.paths.project ) )
        saved_branch = __.execute_external(
            'git branch --show-current' ).stdout.strip( )
        try:
            __.execute_external(
                f"git branch -D local-{target_branch}",
                capture_output = False )
        except SubprocessError: pass
        __.execute_external(
            f"git checkout -b local-{target_branch}", capture_output = False )
        def restore( *exc_info ): # pylint: disable=unused-argument
            __.execute_external(
                f"git checkout {saved_branch}", capture_output = False )
        contexts.push( restore )
        nojekyll_path.touch( exist_ok = True )
        # Override .gitignore to pickup artifacts.
        __.execute_external(
            f"git add --force {html_path}", capture_output = False )
        __.execute_external(
            'git commit -m "Update documentation."', capture_output = False )
        subtree_id = __.execute_external(
            f"git subtree split --prefix {html_path}" ).stdout.strip( )
        __.execute_external(
            f"git push --force origin {subtree_id}:refs/heads/{target_branch}",
            capture_output = False )


@_task( task_nomargs = dict( pre = ( bump_patch, push, upload_pypi, ), ), )
def release_new_patch( context ): # pylint: disable=unused-argument
    ''' Unleashes a new patch upon the world. '''


@_task( task_nomargs = dict( pre = ( bump_stage, push, upload_pypi, ), ), )
def release_new_stage( context ): # pylint: disable=unused-argument
    ''' Unleashes a new stage upon the world. '''


@_task( )
def run( context, command, version = None ): # pylint: disable=unused-argument
    ''' Runs command in virtual environment. '''
    process_environment = __.derive_venv_variables( version = version )
    __.execute_external(
        command, capture_output = False, env = process_environment )
