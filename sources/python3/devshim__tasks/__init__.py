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

''' Project maintenance tasks.

    `Invoke Documentation <http://docs.pyinvoke.org/en/stable/index.html>`_ '''


from .base import assert_sanity as _assert_sanity
_assert_sanity( )


from lockup import NamespaceClass as _NamespaceClass
class __( metaclass = _NamespaceClass ):

    import re

    from contextlib import ExitStack as CMStack
    from itertools import chain
    from pathlib import Path
    from tempfile import TemporaryDirectory
    from time import sleep
    from urllib.error import URLError as UrlError
    from urllib.parse import urlparse
    from urllib.request import urlopen
    from venv import create as create_venv

    from invoke import Exit, Failure, call, task
    from lockup import reclassify_module

    from .base import (
        assert_gpg_tty,
        derive_venv_context_options,
        detect_vmgr_python_version,
        eprint, epprint,
        indicate_python_versions_support,
        is_executable_in_venv,
        on_tty,
        pep508_identify_python,
        render_boxed_title,
        unlink_recursively,
    )
    from .environments import (
        build_python_venv,
    )
    from .packages import (
        calculate_python_packages_fixtures,
        delete_python_packages_fixtures,
        execute_pip_with_requirements,
        indicate_current_python_packages,
        install_python_packages,
        record_python_packages_fixtures,
        retrieve_pypi_release_information,
    )
    from .platforms import (
        freshen_python,
        install_python_builder,
    )
    from .versions import (
        Version,
    )
    from devshim__base import (
        active_python_abi_label,
        discover_project_version,
        ensure_python_support_packages,
        indicate_python_packages,
        paths,
        project_name,
    )
    from devshim__shell_function import (
        generate_cli_functions,
    )

    # https://www.sphinx-doc.org/en/master/man/sphinx-build.html
    sphinx_options = f"-j auto -d {paths.caches.sphinx} -n -T"
    setuptools_build_command = ' '.join( (
        # https://github.com/pypa/setuptools/issues/1347#issuecomment-707979218
        'egg_info',
        f"--egg-base {paths.caches.setuptools}",
        # https://github.com/pypa/wheel/issues/306#issuecomment-522529825
        'build',
        f"--build-base {paths.caches.setuptools}",
    ) )


@__.task
def ease(
    context, # pylint: disable=unused-argument
    shell_name = None,
    function_name = 'devshim',
    with_completions = False
):
    ''' Prints shell functions for easy invocation of development shim. '''
    print( __.generate_cli_functions(
        shell_name, function_name, with_completions ) )


@__.task
def install_git_hooks( context ):
    ''' Installs hooks to check goodness of code changes before commit. '''
    __.render_boxed_title( 'Install: Git Pre-Commit Hooks' )
    context.run(
        f"pre-commit install --config {__.paths.configuration.pre_commit} "
        f"--install-hooks", pty = True, **__.derive_venv_context_options( ) )


@__.task
def install_pythons( context ):
    ''' Installs each supported Python version.

        This task requires Internet access and may take some time. '''
    __.render_boxed_title( 'Install: Python Releases' )
    context.run( 'asdf install python', pty = True )


@__.task( pre = ( install_pythons, ) )
def build_python_venv( context, version, overwrite = False ):
    ''' Creates virtual environment for requested Python version. '''
    if 'ALL' == version: versions = __.indicate_python_versions_support( )
    else: versions = ( version, )
    for version_ in versions:
        __.build_python_venv( context, version_, overwrite = overwrite )


@__.task(
    pre = (
        __.call( build_python_venv, version = 'ALL' ),
        __.call( install_git_hooks ),
    )
)
def bootstrap( context ): # pylint: disable=unused-argument
    ''' Bootstraps the development environment and utilities. '''


@__.task
def clean_pycaches( context ): # pylint: disable=unused-argument
    ''' Removes all caches of compiled CPython bytecode. '''
    __.render_boxed_title( 'Clean: Python Caches' )
    anchors = (
        __.paths.sources.d.python3, __.paths.sources.p.python3,
        __.paths.sources.p.sphinx,
        __.paths.tests.p.python3,
    )
    for path in __.chain.from_iterable( map(
        lambda anchor: anchor.rglob( '__pycache__' ), anchors
    ) ): __.unlink_recursively( path )


@__.task
def clean_tool_caches( context, include_development_support = False ): # pylint: disable=unused-argument
    ''' Clears the caches used by code generation and testing utilities. '''
    __.render_boxed_title( 'Clean: Tool Caches' )
    anchors = __.paths.caches.SELF.glob( '*' )
    ignorable_paths = set( __.paths.caches.SELF.glob( '*/.gitignore' ) )
    if not include_development_support:
        ds_path = __.paths.caches.packages.python3 / __.active_python_abi_label
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
    # Setuptools hardcodes the eggs path to different location.
    __.unlink_recursively( __.paths.caches.eggs )
    # Regnerate development support packages cache, if necessary.
    if include_development_support: __.ensure_python_support_packages( )


@__.task
def clean_python_packages( context, version = None ):
    ''' Removes unused Python packages.

        If version is 'ALL', then all virtual environments are targeted. '''
    if 'ALL' == version: versions = __.indicate_python_versions_support( )
    else: versions = ( version, )
    for version_ in versions:
        _clean_python_packages( context, version = version_ )


def _clean_python_packages( context, version = None ):
    ''' Removes unused Python packages in virtual environment. '''
    __.render_boxed_title(
        'Clean: Unused Python Packages', supplement = version )
    context_options = __.derive_venv_context_options( version = version )
    identifier = __.pep508_identify_python( version = version )
    _, fixtures = __.indicate_python_packages( identifier = identifier )
    requested = frozenset( fixture[ 'name' ] for fixture in fixtures )
    installed = frozenset(
        entry.requirement.name
        for entry
        in __.indicate_current_python_packages( context_options[ 'env' ] ) )
    requirements_text = '\n'.join(
        installed - requested - { __.project_name } )
    if not requirements_text: return
    __.execute_pip_with_requirements(
        context, context_options, 'uninstall', requirements_text,
        pip_options = ( '--yes', ) )


@__.task
def clean( context, version = None ):
    ''' Cleans all caches. '''
    clean_python_packages( context, version = version )
    clean_pycaches( context )
    clean_tool_caches( context )


@__.task
def check_security_issues( context, version = None ):
    ''' Checks for security issues in utilized packages and tools.

        This task requires Internet access and may take some time. '''
    __.render_boxed_title( 'Lint: Package Security', supplement = version )
    context_options = __.derive_venv_context_options( version = version )
    context.run( f"safety check", pty = __.on_tty, **context_options )


@__.task
def freshen_asdf( context ):
    ''' Asks Asdf to update itself.

        This task requires Internet access and may take some time. '''
    __.render_boxed_title( 'Freshen: Version Manager' )
    context.run( 'asdf update', pty = __.on_tty )
    context.run( 'asdf plugin update python', pty = __.on_tty )
    # TODO: Preserve this call after 'freshen_asdf' has been removed.
    __.install_python_builder( )


@__.task( pre = ( freshen_asdf, ) )
def freshen_python( context, version = None ):
    ''' Updates supported Python minor version to latest patch.

        If version is 'ALL', then all supported Pythons are targeted.

        This task requires Internet access and may take some time. '''
    original_versions = __.indicate_python_versions_support( )
    if 'ALL' == version: versions = original_versions
    else: versions = ( version or __.detect_vmgr_python_version( ), )
    obsolete_identifiers = set( )
    version_replacements = { }
    for version_ in versions:
        replacement, identifier = __.freshen_python( context, version_ )
        version_replacements.update( replacement )
        if None is not identifier: obsolete_identifiers.add( identifier )
    # Can only update record of local versions after they are installed.
    successor_versions = [
        version_replacements.get( version_, version_ )
        for version_ in original_versions ]
    context.run( "asdf local python {versions}".format(
        versions = ' '.join( successor_versions ) ), pty = True )
    # Erase packages fixtures for versions which are no longer extant.
    __.delete_python_packages_fixtures( obsolete_identifiers )


@__.task
def freshen_python_packages( context, version = None ):
    ''' Updates declared Python packages.

        If version is 'ALL', then all virtual environments are targeted. '''
    if 'ALL' == version: versions = __.indicate_python_versions_support( )
    else: versions = ( version, )
    for version_ in versions: _freshen_python_packages( context, version_ )


def _freshen_python_packages( context, version = None ):
    ''' Updates Python packages in virtual environment. '''
    __.render_boxed_title(
        'Freshen: Python Package Versions', supplement = version )
    context_options = __.derive_venv_context_options( version = version )
    identifier = __.pep508_identify_python( version = version )
    __.install_python_packages( context, context_options )
    fixtures = __.calculate_python_packages_fixtures(
        context_options[ 'env' ] )
    __.record_python_packages_fixtures( identifier, fixtures )
    check_security_issues( context, version = version )
    test( context, version = version )


@__.task
def freshen_git_modules( context ):
    ''' Performs recursive update of all Git modules.

        Initializes SCM modules as needed.
        This task requires Internet access and may take some time. '''
    __.render_boxed_title( 'Freshen: SCM Modules' )
    context.run(
        'git submodule update --init --recursive --remote', pty = True )


@__.task
def freshen_git_hooks( context ):
    ''' Updates Git hooks to latest tagged release.

        This task requires Internet access and may take some time. '''
    __.render_boxed_title( 'Freshen: SCM Hooks' )
    context.run(
        f"pre-commit autoupdate --config {__.paths.configuration.pre_commit}",
        pty = True, **__.derive_venv_context_options( ) )


@__.task(
    pre = (
        __.call( clean ),
        __.call( freshen_git_modules ),
        __.call( freshen_python, version = 'ALL' ),
        __.call( freshen_python_packages, version = 'ALL' ),
        __.call( freshen_git_hooks ),
    )
)
def freshen( context ): # pylint: disable=unused-argument
    ''' Performs the various freshening tasks, cleaning first.

        This task requires Internet access and may take some time. '''


@__.task
def lint_bandit( context, version = None ):
    ''' Security checks the source code with Bandit. '''
    __.render_boxed_title( 'Lint: Bandit', supplement = version )
    context.run(
        f"bandit --recursive --verbose {__.paths.sources.p.python3}",
        pty = True, **__.derive_venv_context_options( version = version ) )


@__.task( iterable = ( 'packages', 'modules', 'files', ) )
def lint_mypy( context, packages, modules, files, version = None ):
    ''' Lints the source code with Mypy. '''
    __.render_boxed_title( 'Lint: Mypy', supplement = version )
    context_options = __.derive_venv_context_options( version = version )
    if not __.is_executable_in_venv(
        'mypy', venv_path = context_options[ 'env' ][ 'VIRTUAL_ENV' ]
    ):
        __.eprint( 'Mypy not available on this platform. Skipping.' )
        return
    configuration_str = f"--config-file {__.paths.configuration.mypy}"
    if not packages and not modules and not files:
        #files = ( __.paths.sources.p.python3, __.paths.project / 'tasks' )
        files = ( __.paths.sources.p.python3, )
    packages_str = ' '.join( map(
        lambda package: f"--package {package}", packages ) )
    modules_str = ' '.join( map(
        lambda module: f"--module {module}", modules ) )
    files_str = ' '.join( map( str, files ) )
    context.run(
        f"mypy {configuration_str} "
        f"{packages_str} {modules_str} {files_str}",
        pty = True, **context_options )


@__.task( iterable = ( 'targets', 'checks', ) )
def lint_pylint( context, targets, checks, version = None ):
    ''' Lints the source code with Pylint. '''
    __.render_boxed_title( 'Lint: Pylint', supplement = version )
    context_options = __.derive_venv_context_options( version = version )
    if not __.is_executable_in_venv(
        'pylint', venv_path = context_options[ 'env' ][ 'VIRTUAL_ENV' ]
    ):
        __.eprint( 'Pylint not available on this platform. Skipping.' )
        return
    reports_str = '--reports=no --score=no' if targets or checks else ''
    if not targets:
        targets = (
            __.project_name,
            *__.paths.tests.p.python3.rglob( '*.py' ),
            *__.paths.sources.d.python3.rglob( '*.py' ),
            __.paths.sources.p.sphinx / 'conf.py',
            __package__, )
    targets_str = ' '.join( map( str, targets ) )
    checks_str = (
        "--disable=all --enable={}".format( ','.join( checks ) )
        if checks else '' )
    context.run(
        f"pylint {reports_str} {checks_str} {targets_str}",
        pty = True, **context_options )


@__.task
def lint_semgrep( context, version = None ):
    ''' Lints the source code with Semgrep. '''
    __.render_boxed_title( 'Lint: Semgrep', supplement = version )
    context_options = __.derive_venv_context_options( version = version )
    if not __.is_executable_in_venv(
        'semgrep', venv_path = context_options[ 'env' ][ 'VIRTUAL_ENV' ]
    ):
        __.eprint( 'Semgrep not available on this platform. Skipping.' )
        return
    sgconfig_path = __.paths.scm_modules / 'semgrep-rules' / 'python' / 'lang'
    context.run(
        f"semgrep --config {sgconfig_path} --use-git-ignore "
        f"{__.paths.sources.p.python3}", pty = __.on_tty, **context_options )


@__.task
def lint( context, version = None ):
    ''' Lints the source code. '''
    lint_pylint( context, targets = ( ), checks = ( ), version = version )
    lint_semgrep( context, version = version )
    lint_mypy( context,
        packages = ( ), modules = ( ), files = ( ), version = version )
    lint_bandit( context, version = version )


@__.task
def report_coverage( context ):
    ''' Combines multiple code coverage results into a single report. '''
    __.render_boxed_title( 'Artifact: Code Coverage Report' )
    context_options = __.derive_venv_context_options( )
    context.run( 'coverage combine', pty = True, **context_options )
    context.run( 'coverage report', pty = True, **context_options )
    context.run( 'coverage html', pty = True, **context_options )
    context.run( 'coverage xml', pty = True, **context_options )


@__.task
def test( context, version = None ):
    ''' Runs the test suite.

        If version is 'ALL', then all virtual environments are targeted. '''
    if 'ALL' == version: versions = __.indicate_python_versions_support( )
    else: versions = ( version, )
    for version_ in versions: _test( context, version_ )


def _test( context, version = None ):
    ''' Runs the test suite in virtual environment. '''
    clean( context, version = version )
    lint( context, version = version )
    __.render_boxed_title( 'Test: Unit + Code Coverage', supplement = version )
    context_options = __.derive_venv_context_options( version = version )
    context_options[ 'env' ].update( dict(
        HYPOTHESIS_STORAGE_DIRECTORY = __.paths.caches.hypothesis,
    ) )
    context.run(
        f"coverage run --source {__.project_name}",
        pty = True, **context_options )


@__.task
def check_urls( context ):
    ''' Checks the HTTP URLs in the documentation for liveness. '''
    __.render_boxed_title( 'Test: Documentation URLs' )
    context.run(
        f"sphinx-build -b linkcheck {__.sphinx_options} "
        f"{__.paths.sources.p.sphinx} {__.paths.artifacts.sphinx_linkcheck}",
        pty = __.on_tty, **__.derive_venv_context_options( ) )


@__.task
def check_readme( context ):
    ''' Checks that the README will render correctly on PyPI. '''
    __.render_boxed_title( 'Test: README Render' )
    path = _get_sdist_path( )
    context.run(
        f"twine check {path}",
        pty = __.on_tty, **__.derive_venv_context_options( ) )


@__.task( pre = ( test, check_urls, ), post = ( check_readme, ) )
def make_sdist( context ):
    ''' Packages the Python sources for release. '''
    __.render_boxed_title( 'Artifact: Source Distribution' )
    __.assert_gpg_tty( )
    path = _get_sdist_path( )
    # https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html
    context.run(
        f"python3 setup.py {__.setuptools_build_command} "
            f"sdist --dist-dir {__.paths.artifacts.sdists}",
        **__.derive_venv_context_options( ) )
    context.run( f"gpg --detach-sign --armor {path}", pty = True )


def _get_sdist_path( ):
    project_version = __.discover_project_version( )
    name = f"{__.project_name}-{project_version}.tar.gz"
    return __.paths.artifacts.sdists / name


@__.task( pre = ( make_sdist, ) )
def make_wheel( context ):
    ''' Packages a Python wheel for release. '''
    __.render_boxed_title( 'Artifact: Python Wheel' )
    __.assert_gpg_tty( )
    path = _get_wheel_path( )
    # https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html
    context.run(
        f"python3 setup.py {__.setuptools_build_command} "
            f"bdist_wheel --dist-dir {__.paths.artifacts.wheels}",
        **__.derive_venv_context_options( ) )
    context.run( f"gpg --detach-sign --armor {path}", pty = True )


def _get_wheel_path( ):
    project_version = __.discover_project_version( )
    name = f"{__.project_name}-{project_version}-py3-none-any.whl"
    return __.paths.artifacts.wheels / name


@__.task( pre = ( check_urls, ) )
def make_html( context ):
    ''' Generates documentation as HTML artifacts. '''
    __.render_boxed_title( 'Artifact: Documentation' )
    __.unlink_recursively( __.paths.artifacts.sphinx_html )
    context.run(
        f"sphinx-build -b html {__.sphinx_options} "
        f"{__.paths.sources.p.sphinx} {__.paths.artifacts.sphinx_html}",
        pty = __.on_tty, **__.derive_venv_context_options( ) )


@__.task( pre = ( clean, make_wheel, make_html, ) )
def make( context ): # pylint: disable=unused-argument
    ''' Generates all of the artifacts. '''


def _ensure_clean_workspace( context ):
    ''' Error if version control reports any dirty or untracked files. '''
    result = context.run( 'git status --short', pty = True )
    if result.stdout or result.stderr:
        raise __.Exit( 'Dirty workspace. Please stash or commit changes.' )


@__.task
def bump( context, piece ):
    ''' Bumps a piece of the current version. '''
    __.render_boxed_title( f"Version: Adjust" )
    _ensure_clean_workspace( context )
    __.assert_gpg_tty( )
    project_version = __.discover_project_version( )
    current_version = __.Version.from_string( project_version )
    new_version = current_version.as_bumped( piece )
    if 'stage' == piece: part = 'release_class'
    elif 'patch' == piece:
        if current_version.stage in ( 'a', 'rc' ): part = 'prerelease'
        else: part = 'patch'
    else: part = piece
    context.run(
        f"bumpversion --config-file={__.paths.configuration.bumpversion}"
        f" --current-version {current_version}"
        f" --new-version {new_version}"
        f" {part}", pty = True, **__.derive_venv_context_options( ) )


@__.task( post = ( __.call( bump, piece = 'patch' ), ) )
def bump_patch( context ): # pylint: disable=unused-argument
    ''' Bumps to next patch level. '''


@__.task( post = ( __.call( bump, piece = 'stage' ), ) )
def bump_stage( context ): # pylint: disable=unused-argument
    ''' Bumps to next release stage. '''


@__.task( post = ( bump_stage, ) )
def branch_release( context, remote = 'origin' ):
    ''' Makes a new branch for development torwards a release. '''
    _ensure_clean_workspace( context )
    project_version = __.discover_project_version( )
    mainline_regex = __.re.compile(
        r'''^\s+HEAD branch:\s+(.*)$''', __.re.MULTILINE )
    mainline_branch = mainline_regex.search( context.run(
        f"git remote show {remote}", hide = 'stdout' ).stdout.strip( ) )[ 1 ]
    true_branch = context.run(
        'git branch --show-current', hide = 'stdout' ).stdout.strip( )
    if mainline_branch != true_branch:
        raise __.Exit( f"Cannot create release from branch: {true_branch}" )
    this_version = __.Version.from_string( project_version )
    stage = this_version.stage
    if 'a' != stage:
        raise __.Exit( f"Cannot create release from stage: {stage}" )
    target_branch = f"release-{this_version.major}.{this_version.minor}"
    context.run( f"git checkout -b {target_branch}", pty = True )


@__.task
def check_code_style( context, write_changes = False ):
    ''' Checks code style of new changes. '''
    yapf_options = [ ]
    if write_changes: yapf_options.append( '--in-place --verbose' )
    yapf_options_string = ' '.join( yapf_options )
    context.run(
        f"git diff --unified=0 --no-color -- {__.paths.sources.p.python3} "
        f"| yapf-diff {yapf_options_string}",
        pty = __.on_tty, **__.derive_venv_context_options( ) )


@__.task( pre = ( test, ) )
def push( context, remote = 'origin' ):
    ''' Pushes commits on current branch, plus all tags. '''
    __.render_boxed_title( 'SCM: Push Branch with Tags' )
    _ensure_clean_workspace( context )
    project_version = __.discover_project_version( )
    true_branch = context.run(
        'git branch --show-current', hide = 'stdout' ).stdout.strip( )
    this_version = __.Version.from_string( project_version )
    target_branch = f"release-{this_version.major}.{this_version.minor}"
    if true_branch == target_branch:
        context.run(
            f"git push --set-upstream {remote} {true_branch}", pty = True )
    else: context.run( 'git push', pty = True )
    context.run( 'git push --tags', pty = True )


@__.task
def check_pip_install( context, index_url = '', version = None ):
    ''' Checks import of current package after installation via Pip. '''
    version = version or __.discover_project_version( )
    __.render_boxed_title( f"Verify: Python Package Installation ({version})" )
    with __.TemporaryDirectory( ) as venv_path:
        venv_path = __.Path( venv_path )
        __.create_venv( venv_path, clear = True, with_pip = True )
        index_url_option = ''
        if index_url: index_url_option = f"--index-url {index_url}"
        context_options = __.derive_venv_context_options( venv_path )
        attempts_count_max = 2
        for attempts_count in range( attempts_count_max + 1 ):
            try:
                context.run(
                    f"pip install {index_url_option} "
                    f"  {__.project_name}=={version}",
                    pty = __.on_tty, **context_options )
            except __.Failure:
                if attempts_count_max == attempts_count: raise
                __.sleep( 2 ** attempts_count )
            else: break
        python_import_command = (
            f"import {__.project_name}; "
            f"print( {__.project_name}.__version__ )" )
        context.run(
            f"python -c '{python_import_command}'",
            pty = True, **context_options )


@__.task
def check_pypi_integrity( context, version = None, index_url = '' ):
    ''' Checks integrity of project packages on PyPI.
        If no version is provided, the current project version is used.

        This task requires Internet access and may take some time. '''
    version = version or __.discover_project_version( )
    __.render_boxed_title( f"Verify: Python Package Integrity ({version})" )
    release_info = __.retrieve_pypi_release_information(
        __.project_name, version, index_url = index_url )
    for package_info in release_info:
        url = package_info[ 'url' ]
        if not package_info.get( 'has_sig', False ):
            raise __.Exit( f"No signature found for: {url}" )
        check_pypi_package( context, url )


def check_pypi_package( context, package_url ):
    ''' Verifies signature on package. '''
    __.assert_gpg_tty( )
    package_filename = __.urlparse( package_url ).path.split( '/' )[ -1 ]
    with __.TemporaryDirectory( ) as cache_path_raw:
        cache_path = __.Path( cache_path_raw )
        package_path = cache_path / package_filename
        signature_path = cache_path / f"{package_filename}.asc"
        attempts_count_max = 2
        for attempts_count in range( attempts_count_max + 1 ):
            try:
                with __.urlopen( package_url ) as http_reader:
                    with package_path.open( 'wb' ) as file:
                        file.write( http_reader.read( ) )
                with __.urlopen( f"{package_url}.asc" ) as http_reader:
                    with signature_path.open( 'wb' ) as file:
                        file.write( http_reader.read( ) )
            except __.UrlError:
                if attempts_count_max == attempts_count: raise
                __.sleep( 2 ** attempts_count )
            else: break
        context.run( f"gpg --verify {signature_path}" )


@__.task(
    pre = ( make, ),
    post = (
        __.call(
            check_pypi_integrity, index_url = 'https://test.pypi.org'
        ),
        __.call(
            check_pip_install, index_url = 'https://test.pypi.org/simple/'
        ),
    )
)
def upload_test_pypi( context ):
    ''' Publishes current sdist and wheels to Test PyPI. '''
    _upload_pypi( context, 'testpypi' )


@__.task(
    pre = (
        __.call( upload_test_pypi ),
        __.call( test, version = 'ALL' ),
    ),
    post = ( check_pypi_integrity, check_pip_install, )
)
def upload_pypi( context ):
    ''' Publishes current sdist and wheels to PyPI. '''
    _upload_pypi( context )


def _upload_pypi( context, repository_name = '' ):
    repository_option = ''
    task_name_suffix = ''
    if repository_name:
        repository_option = f"--repository {repository_name}"
        task_name_suffix = f" ({repository_name})"
    __.render_boxed_title( f"Publication: PyPI{task_name_suffix}" )
    artifacts = _get_pypi_artifacts( )
    context_options = __.derive_venv_context_options( )
    context_options.update( _get_pypi_credentials( repository_name ) )
    context.run(
        f"twine upload --skip-existing --verbose {repository_option} "
        f"{artifacts}", pty = True, **context_options )


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
@__.task( pre = ( test, make_html, ) )
def upload_github_pages( context ):
    ''' Publishes Sphinx HTML output to Github Pages for project. '''
    __.render_boxed_title( 'Publication: Github Pages' )
    # Use relative path, since 'git subtree' needs it.
    html_path = __.paths.artifacts.sphinx_html.relative_to( __.paths.project )
    nojekyll_path = html_path / '.nojekyll'
    target_branch = 'documentation'
    with __.CMStack( ) as cm_stack:
        # Work from project root, since 'git subtree' requires relative paths.
        cm_stack.enter_context( context.cd( __.paths.project ) )
        saved_branch = context.run(
            'git branch --show-current', hide = 'stdout' ).stdout.strip( )
        context.run( f"git branch -D local-{target_branch}", warn = True )
        context.run( f"git checkout -b local-{target_branch}", pty = True )
        def restore( *exc_info ): # pylint: disable=unused-argument
            context.run( f"git checkout {saved_branch}", pty = True )
        cm_stack.push( restore )
        nojekyll_path.touch( exist_ok = True )
        # Override .gitignore to pickup artifacts.
        context.run( f"git add --force {html_path}", pty = True )
        context.run( 'git commit -m "Update documentation."', pty = True )
        subtree_id = context.run(
            f"git subtree split --prefix {html_path}",
            hide = 'stdout' ).stdout.strip( )
        context.run(
            f"git push --force origin {subtree_id}:refs/heads/{target_branch}",
            pty = True )


@__.task( pre = ( bump_patch, push, upload_pypi, ) )
def release_new_patch( context ): # pylint: disable=unused-argument
    ''' Unleashes a new patch upon the world. '''


@__.task( pre = ( bump_stage, push, upload_pypi, ) )
def release_new_stage( context ): # pylint: disable=unused-argument
    ''' Unleashes a new stage upon the world. '''


@__.task
def run( context, command, version = None ):
    ''' Runs command in virtual environment. '''
    context.run(
        command,
        pty = __.on_tty,
        **__.derive_venv_context_options( version = version ) )


__.reclassify_module( __name__ )