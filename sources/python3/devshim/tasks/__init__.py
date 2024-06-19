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


from . import base as __
from . import linters


# https://www.sphinx-doc.org/en/master/man/sphinx-build.html
_sphinx_options = f"-j auto -d {__.paths.caches.sphinx} -n -T"


@__.task( )
def ease(
    shell_name = None,
    function_name = 'devshim',
    with_completions = False
):
    ''' Prints shell functions for easier invocation. '''
    from ..user_interface import generate_cli_functions
    print( generate_cli_functions(
        shell_name, function_name, with_completions ) )


@__.task( 'Install: Git Pre-Commit Hooks' )
def install_git_hooks( ):
    ''' Installs hooks to check goodness of code before commit. '''
    __.project_execute_external(
        ( 'pre-commit', 'install', '--config',
          __.paths.configuration.pre_commit, '--hook-type', 'pre-commit',
         '--install-hooks' ),
        venv_specification = { } )
    __.project_execute_external(
        ( 'pre-commit', 'install', '--config',
          __.paths.configuration.pre_commit, '--hook-type', 'pre-push',
         '--install-hooks' ),
        venv_specification = { } )


@__.task(
    'Install: Python Release',
    multiplexer = __.PythonVersionMultiplexer( enable_default = False ),
)
def install_python( version ):
    ''' Installs requested Python version.

        This task requires Internet access and may take some time. '''
    from ..languages.python import language
    language.produce_descriptor( version ).install( )


@__.task(
    'Build: Python Virtual Environment',
    multiplexer = __.PythonVersionMultiplexer( ),
)
def build_python_venv( version, overwrite = False ):
    ''' Creates virtual environment for requested Python version. '''
    # TODO? Install exact packages, if possible.
    from ._invoke import extract_task_invocable
    extract_task_invocable( install_python )( version )
    from .. import environments
    environments.build_python_venv( version, overwrite = overwrite )
    # TODO: Test new virtual environment.


@__.task(
    task_nomargs = dict(
        pre = (
            __.call( build_python_venv, version = 'ALL' ),
            __.call( install_git_hooks ),
        ),
    ),
)
def bootstrap( ):
    ''' Bootstraps the development environment and utilities. '''


@__.task( 'Clean: Python Caches' )
def clean_pycaches( ):
    ''' Removes all caches of compiled CPython bytecode. '''
    from itertools import chain
    from ..fs_utilities import unlink_recursively
    anchors = (
        __.paths.sources.aux.python3,
        __.paths.sources.prj.python3,
        __.paths.sources.prj.sphinx,
        __.paths.tests.prj.python3,
    )
    for path in chain.from_iterable( map(
        lambda anchor: anchor.rglob( '__pycache__' ), anchors
    ) ): unlink_recursively( path )


@__.task( 'Clean: Tool Caches' )
def clean_tool_caches( ):
    ''' Clears the caches used by code generation and testing utilities. '''
    from itertools import chain
    anchors = __.paths.caches.SELF.glob( '*' )
    ignorable_paths = set( __.paths.caches.SELF.glob( '*/.gitignore' ) )
    ignorable_paths.update( __.paths.caches.DEV.SELF.rglob( '*' ) )
    dirs_stack = [ ]
    for path in chain.from_iterable( map(
        lambda anchor: anchor.rglob( '*' ), anchors
    ) ):
        if path in ignorable_paths: continue
        if path.is_dir( ) and not path.is_symlink( ):
            dirs_stack.append( path )
            continue
        path.unlink( )
    while dirs_stack: dirs_stack.pop( ).rmdir( )


@__.task(
    'Clean: Unused Python Packages',
    multiplexer = __.PythonVersionMultiplexer( ),
)
def clean_python_packages( version = None ):
    ''' Removes unused Python packages. '''
    from ..environments import (
        build_python_venv as build_python_venv_,
        is_executable_in_venv,
    )
    if not is_executable_in_venv( 'pip', version = version ):
        __.scribe.error(
            f"Absent or corrupt virtual environment for Python {version!r}." )
        __.scribe.info(
            f"Rebuilding virtual environment for Python {version!r}." )
        build_python_venv_( version, overwrite = True )
        return
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


@__.task( )
def clean( version = None ):
    ''' Cleans all caches. '''
    __.invoke_task( clean_python_packages, version = version )
    __.invoke_task( clean_pycaches )
    __.invoke_task( clean_tool_caches )


@__.task(
    'Freshen: Python Version',
    multiplexer = __.PythonVersionMultiplexer( ),
)
def freshen_python( version = None, install = True ):
    ''' Updates requested Python version, if newer one available.

        This task requires Internet access and may take some time. '''
    from ..languages.python import language
    language.produce_descriptor( version ).update( install = install )
    ## Erase packages fixtures for versions which are no longer extant.
    #from ..packages import delete_python_packages_fixtures
    #delete_python_packages_fixtures( obsolete_identifiers )


@__.task(
    'Freshen: Python Package Versions',
    multiplexer = __.PythonVersionMultiplexer( ),
)
def freshen_python_packages( version = None ):
    ''' Updates declared Python packages in Python virtual environment. '''
    from ..environments import (
        build_python_venv as build_python_venv_,
        is_executable_in_venv,
    )
    if not is_executable_in_venv( 'pip', version = version ):
        __.scribe.error(
            f"Detected corrupt virtual environment for Python {version!r}." )
        __.scribe.info(
            f"Rebuilding virtual environment for Python {version!r}." )
        build_python_venv_( version, overwrite = True )
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
    __.invoke_task( test, version = version )


@__.task( 'Freshen: Git Modules' )
def freshen_git_modules( ):
    ''' Performs recursive update of all Git modules.

        This task requires Internet access and may take some time. '''
    __.execute_external( 'git submodule update --init --recursive --remote' )


@__.task( 'Freshen: Git Hooks' )
def freshen_git_hooks( ):
    ''' Updates Git hooks to latest tagged release.

        This task requires Internet access and may take some time. '''
    __.project_execute_external(
        f"pre-commit autoupdate --config {__.paths.configuration.pre_commit}",
        venv_specification = { } )


@__.task(
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
def freshen( ):
    ''' Performs the various freshening tasks, cleaning first.

        This task requires Internet access and may take some time. '''


@__.task(
    'Lint: Bandit',
    multiplexer = __.PythonVersionMultiplexer( ),
)
def lint_bandit( version = None ):
    ''' Security checks the source code with Bandit. '''
    # Cyaml binary package requires standard ABI.
    from ..languages.python import language
    if (
        language.produce_descriptor( version )
        .probe_feature_labels( 'abi-incompatible' )
    ): return
    files = _lint_targets_default
    files_str = ' '.join( map( str, files ) )
    __.project_execute_external(
        "bandit --recursive "
        f"--configfile {__.paths.configuration.pyproject} {files_str}",
        venv_specification = dict( version = version ) )


@__.task(
    'Lint: Mypy',
    multiplexer = __.PythonVersionMultiplexer( ),
    task_nomargs = dict(
        iterable = ( 'packages', 'modules', 'files', ),
        pre = ( clean_tool_caches, ), # TODO: Target Mypy cache only.
    ),
)
def lint_mypy( packages, modules, files, version = None ):
    ''' Lints the source code with Mypy. '''
    # Mypy binary package requires standard ABI.
    from ..languages.python import language
    if (
        language.produce_descriptor( version )
        .probe_feature_labels( 'abi-incompatible' )
    ): return
    process_environment = __.derive_venv_variables( version = version )
    # TODO: Check executable in decorator.
    from ..environments import test_package_executable
    if not test_package_executable( 'mypy', process_environment ): return
    if not packages and not modules and not files:
        # TODO: Is this the best approach?
        files = _lint_targets_default
    packages_str = ' '.join( map(
        lambda package: f"--package {package}", packages ) )
    modules_str = ' '.join( map(
        lambda module: f"--module {module}", modules ) )
    files_str = ' '.join( map( str, files ) )
    __.project_execute_external(
        f"mypy {packages_str} {modules_str} {files_str}",
        env = process_environment )


@__.task(
    'Lint: Pylint',
    multiplexer = __.PythonVersionMultiplexer( ),
    task_nomargs = dict( iterable = ( 'targets', 'checks', ), ),
)
def lint_pylint( targets, checks, report = False, version = None ):
    ''' Lints the source code with Pylint. '''
    process_environment = __.derive_venv_variables( version = version )
    # TODO: Check executable in decorator.
    from ..environments import test_package_executable
    if not test_package_executable( 'pylint', process_environment ): return
    options = (
        f"--rcfile={__.paths.configuration.pyproject}",
        "--reports={}".format( 'no' if not report else 'yes' ),
        "--score={}".format( 'no' if targets or checks else 'yes' ),
    )
    if not targets: targets = _lint_targets_default
    checks = (
        ( '--disable=all', "--enable={}".format( ','.join( checks ) ), )
        if checks else ( ) )
    __.project_execute_external(
        ( 'pylint', *options, *checks, '--recursive=yes', *targets ),
        env = process_environment )


@__.task(
    'Lint: Semgrep',
    multiplexer = __.PythonVersionMultiplexer( ),
)
def lint_semgrep( version = None ):
    ''' Lints the source code with Semgrep. '''
    # Ruamel binary package requires standard ABI.
    from ..languages.python import language
    if (
        language.produce_descriptor( version )
        .probe_feature_labels( 'abi-incompatible' )
    ): return
    process_environment = __.derive_venv_variables( version = version )
    # TODO: Check executable in decorator.
    from ..environments import test_package_executable
    if not test_package_executable( 'semgrep', process_environment ): return
    files = _lint_targets_default
    files_str = ' '.join( map( lambda path: str( path.resolve( ) ), files ) )
    from .linters.semgrep import update_rules
    rules_location = update_rules( )
    python_rules_location = ( rules_location / 'python/lang' ).resolve( )
    __.execute_external(
        #f"strace -ff -tt --string-limit=120 --output=strace/semgrep "
        f"semgrep --config {python_rules_location} --error --use-git-ignore "
        f"{files_str}", cwd = rules_location, env = process_environment )


_lint_targets_default = (
    __.paths.sources.prj.python3,
    __.paths.tests.prj.python3,
    __.paths.project / 'develop.py',
    __.paths.project / 'setup.py',
    __.paths.sources.prj.sphinx / 'conf.py',
)


@__.task( multiplexer = __.PythonVersionMultiplexer( ), )
def lint( version = None ):
    ''' Lints the source code. '''
    __.invoke_task(
        lint_pylint, targets = ( ), checks = ( ), version = version )
    __.invoke_task( lint_semgrep, version = version )
    __.invoke_task(
        lint_mypy,
        packages = ( ), modules = ( ), files = ( ), version = version )
    __.invoke_task( lint_bandit, version = version )


@__.task( 'Make: Code Coverage Report' )
def report_coverage( ):
    ''' Combines multiple code coverage results into a single report. '''
    execution_options = dict( venv_specification = { } )
    __.project_execute_external( f"coverage combine", **execution_options )
    __.project_execute_external( f"coverage report", **execution_options )
    __.project_execute_external( f"coverage html", **execution_options )
    __.project_execute_external( f"coverage xml", **execution_options )


@__.task( multiplexer = __.PythonVersionMultiplexer( ), )
def test( ensure_sanity = True, version = None ):
    ''' Runs the test suite in Python virtual environment. '''
    __.invoke_task( clean, version = version )
    if ensure_sanity: __.invoke_task( lint, version = version )
    from ..user_interface import render_boxed_title
    render_boxed_title( 'Test: Unit + Code Coverage', supplement = version )
    # Cyaml binary package requires standard ABI.
    from ..languages.python import language
    if (
        language.produce_descriptor( version )
        .probe_feature_labels( 'abi-incompatible' )
    ): return
    process_environment = __.derive_venv_variables( version = version )
    process_environment.update( dict(
        HYPOTHESIS_STORAGE_DIRECTORY = __.paths.caches.hypothesis,
        PYTHONUNBUFFERED = 'TRUE', # Ensure complete crash output.
    ) )
    __.project_execute_external(
        f"coverage run --source {__.project_name}", env = process_environment )


@__.task( 'Test: Documentation URLs' )
def check_urls( ):
    ''' Checks the HTTP URLs in the documentation for liveness. '''
    __.project_execute_external(
        f"sphinx-build -b linkcheck {_sphinx_options} "
        f"{__.paths.sources.prj.sphinx} {__.paths.artifacts.sphinx_linkcheck}",
        venv_specification = { } )


@__.task( 'Test: README Render' )
def check_readme( ):
    ''' Checks that the README will render correctly on PyPI. '''
    path = _get_sdist_path( )
    __.project_execute_external(
        f"twine check {path}", venv_specification = { } )


@__.task(
    'Artifact: Source Distribution',
    task_nomargs = dict( post = ( check_readme, ), ),
)
def make_sdist( ensure_sanity = True, signature = True ):
    ''' Packages the Python sources for release. '''
    if ensure_sanity:
        __.invoke_task( test )
        __.invoke_task( check_urls )
    path = _get_sdist_path( )
    if path.exists( ): path.unlink( ) # TODO: Python 3.8: missing_ok = True
    __.project_execute_external(
        f"python3 -m build --sdist --outdir {__.paths.artifacts.sdists}",
        venv_specification = { } )
    if signature:
        from ..file_utilities import gpg_sign_file
        gpg_sign_file( path )


def _get_sdist_path( ):
    project_version = __.discover_project_version( )
    name = f"{__.project_name}-{project_version}.tar.gz"
    return __.paths.artifacts.sdists / name


@__.task( 'Artifact: Python Wheel' )
def make_wheel( ensure_sanity = True, signature = True ):
    ''' Packages a Python wheel for release. '''
    __.invoke_task(
        make_sdist, ensure_sanity = ensure_sanity, signature = signature )
    path = _get_wheel_path( )
    if path.exists( ): path.unlink( ) # TODO: Python 3.8: missing_ok = True
    __.project_execute_external(
        f"python3 -m build --wheel --outdir {__.paths.artifacts.wheels}",
        venv_specification = { } )
    if signature:
        from ..file_utilities import gpg_sign_file
        gpg_sign_file( path )


def _get_wheel_path( ):
    project_version = __.discover_project_version( )
    name = f"{__.project_name}-{project_version}-py3-none-any.whl"
    return __.paths.artifacts.wheels / name


@__.task(
    'Artifact: Documentation',
    task_nomargs = dict( pre = ( check_urls, ), ),
)
def make_html( ):
    ''' Generates documentation as HTML artifacts. '''
    from ..fs_utilities import unlink_recursively
    unlink_recursively( __.paths.artifacts.sphinx_html )
    __.project_execute_external(
        f"sphinx-build -b html {_sphinx_options} "
        f"{__.paths.sources.prj.sphinx} {__.paths.artifacts.sphinx_html}",
        venv_specification = { } )


@__.task( task_nomargs = dict( pre = ( clean, make_wheel, make_html, ), ), )
def make( ):
    ''' Generates all of the artifacts. '''


def _ensure_clean_workspace( ):
    ''' Error if version control reports any dirty or untracked files. '''
    result = __.project_execute_external(
        'git status --short', capture_output = True )
    if result.stdout or result.stderr:
        # TODO: Use different error-handling mechanism.
        from invoke import Exit
        raise Exit( 'Dirty workspace. Please stash or commit changes.' )


@__.task( 'Change: Project Version' )
def bump( piece ):
    ''' Bumps a piece of the current version. '''
    _ensure_clean_workspace( )
    from ..file_utilities import assert_gpg_tty
    from ..packages import Version
    assert_gpg_tty( )
    project_version = __.discover_project_version( )
    current_version = Version.from_string( project_version )
    new_version = current_version.as_bumped( piece )
    if 'stage' == piece: part = 'release_class'
    elif 'patch' == piece:
        if current_version.stage in ( 'a', 'rc' ): part = 'prerelease'
        else: part = 'patch'
    else: part = piece
    __.project_execute_external(
        f"bumpversion --config-file={__.paths.configuration.bumpversion}"
        f" --current-version {current_version}"
        f" --new-version {new_version}"
        f" {part}", venv_specification = { } )


@__.task(
    task_nomargs = dict( post = ( __.call( bump, piece = 'patch' ), ), ),
)
def bump_patch( ):
    ''' Bumps to next patch level. '''


@__.task(
    task_nomargs = dict( post = ( __.call( bump, piece = 'stage' ), ), ),
)
def bump_stage( ):
    ''' Bumps to next release stage. '''


@__.task( task_nomargs = dict( post = ( bump_stage, ), ), )
def branch_release( remote = 'origin' ):
    ''' Makes a new branch for development torwards a release. '''
    import re
    from invoke import Exit  # TODO: Use different error-handling mechanism.
    _ensure_clean_workspace( )
    project_version = __.discover_project_version( )
    mainline_regex = re.compile(
        r'''^\s+HEAD branch:\s+(.*)$''', re.MULTILINE )
    mainline_branch = mainline_regex.search( __.project_execute_external(
        f"git remote show {remote}",
        capture_output = True ).stdout.strip( ) )[ 1 ]
    true_branch = __.project_execute_external(
        'git branch --show-current', capture_output = True ).stdout.strip( )
    if mainline_branch != true_branch:
        # TODO: Use different error-reporting mechanism.
        raise Exit( f"Cannot create release from branch: {true_branch}" )
    from ..packages import Version
    this_version = Version.from_string( project_version )
    stage = this_version.stage
    if 'a' != stage:
        # TODO: Use different error-reporting mechanism.
        raise Exit( f"Cannot create release from stage: {stage}" )
    target_branch = f"release-{this_version.major}.{this_version.minor}"
    __.project_execute_external( f"git checkout -b {target_branch}" )


@__.task( 'Code Format: YAPF' )
def check_code_style( write_changes = False ):
    ''' Checks code style of new changes. '''
    from ..base import split_command
    yapf_options = [ ]
    if write_changes: yapf_options.append( '--in-place --verbose' )
    yapf_options_string = ' '.join( yapf_options )
    from contextlib import ExitStack as ContextStack
    from subprocess import Popen, PIPE # nosec B404
    process_environment = __.derive_venv_variables( )
    contexts = ContextStack( )
    # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
    git_diff_process = contexts.enter_context( Popen( # nosec B603
        ( *split_command("git diff --unified=0 --no-color --"),
          *_lint_targets_default ), stdout = PIPE, text = True ) )
    # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
    yapf_diff_process = contexts.enter_context( Popen( # nosec B603
        split_command( f"yapf-diff {yapf_options_string}" ),
        env = process_environment,
        stdin = git_diff_process.stdout, text = True ) )
    with contexts:
        git_diff_process.stdout.close( )
        yapf_diff_process.communicate( )
    exit_code = git_diff_process.returncode or yapf_diff_process.returncode
    if exit_code: raise SystemExit( exit_code )


@__.task( 'Publish: Push Branch with Tags' )
def push( remote = 'origin' ):
    ''' Pushes commits on current branch, plus all tags. '''
    # TODO: Discover remote corresponding to current branch.
    _ensure_clean_workspace( )
    project_version = __.discover_project_version( )
    true_branch = __.project_execute_external(
        'git branch --show-current', capture_output = True ).stdout.strip( )
    from ..packages import Version
    this_version = Version.from_string( project_version )
    target_branch = f"release-{this_version.major}.{this_version.minor}"
    if true_branch == target_branch:
        __.project_execute_external(
            f"git push --set-upstream {remote} {true_branch}" )
    else: __.project_execute_external( 'git push' )
    __.project_execute_external( 'git push --no-verify --tags' )


@__.task( )
def check_pip_install( index_url = '', version = None ):
    ''' Checks import of current package after installation via Pip. '''
    version = version or __.discover_project_version( )
    from ..user_interface import render_boxed_title
    render_boxed_title( f"Verify: Python Package Installation ({version})" )
    from pathlib import Path
    from subprocess import SubprocessError # nosec B404
    from tempfile import TemporaryDirectory
    from time import sleep
    from venv import create as create_venv
    with TemporaryDirectory( ) as venv_path:
        venv_path = Path( venv_path )
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
                    env = process_environment )
            except SubprocessError:
                if attempts_count_max == attempts_count: raise
                sleep( 2 ** attempts_count )
            else: break
        python_import_command = (
            f"import {__.project_name}; "
            f"print( {__.project_name}.__version__ )" )
        __.execute_external(
            f"python3 -c '{python_import_command}'",
            env = process_environment )


@__.task( )
def check_pypi_integrity( version = None, index_url = '' ):
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
        check_pypi_package( url )


# TODO: Move to '.packages' and separate retry logic from fetch logic.
def check_pypi_package( package_url ): # pylint: disable=too-many-locals
    ''' Verifies signature on package. '''
    from ..file_utilities import assert_gpg_tty
    assert_gpg_tty( )
    from urllib.parse import urlparse as parse_url
    package_filename = parse_url( package_url ).path.split( '/' )[ -1 ]
    from pathlib import Path
    from tempfile import TemporaryDirectory
    from time import sleep
    from urllib.error import URLError as UrlError
    from urllib.request import urlopen as access_url
    with TemporaryDirectory( ) as cache_path_raw:
        cache_path = Path( cache_path_raw )
        package_path = cache_path / package_filename
        signature_path = cache_path / f"{package_filename}.asc"
        attempts_count_max = 2
        for attempts_count in range( attempts_count_max + 1 ):
            try:
                # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected
                with access_url( package_url ) as http_reader:
                    with package_path.open( 'wb' ) as file:
                        file.write( http_reader.read( ) )
                # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected
                with access_url( f"{package_url}.asc" ) as http_reader:
                    with signature_path.open( 'wb' ) as file:
                        file.write( http_reader.read( ) )
            except UrlError:
                if attempts_count_max == attempts_count: raise
                sleep( 2 ** attempts_count )
            else: break
        __.execute_external( f"gpg --verify {signature_path}" )


@__.task(
    'Publish: Test PyPI',
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
def upload_test_pypi( ):
    ''' Publishes current sdist and wheels to Test PyPI. '''
    _upload_pypi( 'testpypi' )


@__.task(
    'Publish: PyPI',
    task_nomargs = dict(
        pre = (
            __.call( upload_test_pypi ),
            __.call( test, version = 'ALL' ),
        ),
        post = ( check_pypi_integrity, check_pip_install, ),
    ),
)
def upload_pypi( ):
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
    __.project_execute_external(
        f"twine upload --skip-existing --verbose {repository_option} "
        f"{artifacts}", env = process_environment )


def _get_pypi_artifacts( ):
    from itertools import chain
    stems = ( _get_sdist_path( ), _get_wheel_path( ), )
    return ' '.join( chain(
        map( str, stems ), map( lambda p: f"{p}.asc", stems ) ) )


def _get_pypi_credentials( repository_name ):
    from tomli import load as load_toml
    if '' == repository_name: repository_name = 'pypi'
    with open( __.paths.project / 'credentials.toml', 'rb' ) as file:
        table = load_toml( file )[ repository_name ]
    return {
        'TWINE_USERNAME': table[ 'username' ],
        'TWINE_PASSWORD': table[ 'password' ], }


@__.task( task_nomargs = dict( pre = ( bump_patch, push, upload_pypi, ), ), )
def release_new_patch( ):
    ''' Unleashes a new patch upon the world. '''


@__.task( task_nomargs = dict( pre = ( bump_stage, push, upload_pypi, ), ), )
def release_new_stage( ):
    ''' Unleashes a new stage upon the world. '''


@__.task( )
def run( command, version = None ):
    ''' Runs command in virtual environment. '''
    __.execute_external(
        command, venv_specification = dict( version = version ) )


@__.task( )
def show_python( all_versions = False ):
    ''' Lists names of default supported Python version. '''
    # TODO? With Rich and 'detail' flag, show panels with details.
    from ..languages.python import language
    if all_versions:
        for version in language.survey_descriptors( ).keys( ): print( version )
    else: print( language.detect_default_descriptor( ).name )


@__.task( )
def show_environments( ):
    ''' Lists names of available environments. '''
    # TODO? With Rich and 'detail' flag, show panels with details.
    from ..environments import survey_descriptors
    for descriptor in survey_descriptors( ).keys( ): print( descriptor )


# For use by Invoke's module loader. Must be called 'namespace' (or 'ns').
namespace = __.TaskCollection( )
namespace.add_task( bootstrap )
namespace.add_task( ease )
namespace.add_task( push )
namespace.add_task( run )
namespace.add_task( test )
namespace.add_collection( __.TaskCollection(
    'build',
    python_venv = build_python_venv,
    release_branch = branch_release,
) )
namespace.add_collection( __.TaskCollection(
    'change',
    version_piece = bump,
    version_patch = bump_patch,
    version_stage = bump_stage,
) )
namespace.add_collection( __.TaskCollection(
    'check',
    pip_install = check_pip_install,
    pypi_integrity = check_pypi_integrity,
    pypi_readme = check_readme,
    sphinx_urls = check_urls,
) )
namespace.add_collection( __.TaskCollection(
    'clean',
    pycaches = clean_pycaches,
    pypackages = clean_python_packages,
    tool_caches = clean_tool_caches,
) )
namespace.subcollection_from_path( 'clean' ).add_task(
    clean, name = 'ALL', default = True )
namespace.add_collection( __.TaskCollection(
    'freshen',
    git_hooks = freshen_git_hooks,
    git_modules = freshen_git_modules,
    pypackages = freshen_python_packages,
    python = freshen_python,
) )
namespace.subcollection_from_path( 'freshen' ).add_task(
    freshen, name = 'ALL', default = True )
namespace.add_collection( __.TaskCollection(
    'install',
    git_hooks = install_git_hooks,
    python = install_python,
) )
namespace.add_collection( __.TaskCollection(
    'lint',
    bandit = lint_bandit,
    mypy = lint_mypy,
    pylint = lint_pylint,
    semgrep = lint_semgrep,
    yapf = check_code_style,
) )
namespace.subcollection_from_path( 'lint' ).add_task(
    lint, name = 'ALL', default = True )
namespace.add_collection( __.TaskCollection(
    'make',
    coverage = report_coverage,
    html = make_html,
    sdist = make_sdist,
    wheel = make_wheel,
) )
namespace.subcollection_from_path( 'make' ).add_task(
    make, name = 'ALL', default = True )
namespace.add_collection( __.TaskCollection(
    'publish',
    new_patch = release_new_patch,
    new_stage = release_new_stage,
    pypi = upload_pypi,
    test_pypi = upload_test_pypi,
) )
namespace.add_collection( __.TaskCollection(
    'show',
    environments = show_environments,
    python = show_python,
) )
namespace.add_collection( __.TaskCollection(
    'xp',
) )
