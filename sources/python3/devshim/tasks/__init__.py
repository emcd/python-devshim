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

    from ..base import on_tty
    from ..environments import (
        derive_venv_context_options,
        test_package_executable,
    )
    from ..locations import paths
    from ..packages import Version
    from ..platforms import calculate_python_versions
    from ..project import (
        discover_project_name,
        discover_project_version,
    )
    from ..user_interface import render_boxed_title

    project_name = discover_project_name( )
    # https://www.sphinx-doc.org/en/master/man/sphinx-build.html
    sphinx_options = f"-j auto -d {paths.caches.sphinx} -n -T"


def _task(
    title = '',
    task_nomargs = None,
    version_expansion = '',
):
    ''' Produces decorator for the handling of assorted banalities.

        Banalities include:
        * Rendering a title box.
        * Iterative execution over multiple platform versions. '''
    from functools import wraps
    from ._invoke import Task
    from ..user_interface import render_boxed_title

    def decorator( invocable ):
        ''' Produces invoker for the handling of assorted banalities. '''
        if version_expansion:
            invocable.__doc__ = '\n\n'.join( (
                invocable.__doc__,
                f"If version is 'ALL', then all {version_expansion}." ) )

        # nosemgrep: scm-modules.semgrep-rules.python.lang.maintainability.useless-inner-function
        @wraps( invocable )
        def invoker( *posargs, **nomargs ):
            ''' Handles assorted banalities. '''
            if version_expansion:
                from ..platforms import calculate_python_versions
                versions = calculate_python_versions(
                    nomargs.get( 'version' ) )
                for version in versions:
                    if title: render_boxed_title( title, supplement = version )
                    re_posargs, re_nomargs = _replace_arguments(
                        invocable, posargs, nomargs,
                        dict( version = version ) )
                    invocable( *re_posargs, **re_nomargs )
            else:
                if title: render_boxed_title( title )
                invocable( *posargs, **nomargs )

        return Task( invoker, **( task_nomargs or { } ) )

    return decorator


def _replace_arguments( invocable, posargs, nomargs, replacements ):
    from inspect import signature as scan_signature
    binder = scan_signature( invocable ).bind( *posargs, **nomargs )
    binder.arguments.update( replacements )
    binder.apply_defaults( )
    return binder.args, binder.kwargs


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
def install_git_hooks( context ):
    ''' Installs hooks to check goodness of code changes before commit. '''
    context.run(
        f"pre-commit install --config {__.paths.configuration.pre_commit} "
        f"--hook-type pre-commit --install-hooks",
        pty = True, **__.derive_venv_context_options( ) )
    context.run(
        f"pre-commit install --config {__.paths.configuration.pre_commit} "
        f"--hook-type pre-push --install-hooks",
        pty = True, **__.derive_venv_context_options( ) )


@_task(
    'Install: Python Release',
    version_expansion = 'declared Python versions are installed',
)
def install_python( context, version ):
    ''' Installs requested Python version.

        This task requires Internet access and may take some time. '''
    context.run( f"asdf install python {version}", pty = True )


@_task(
    'Build: Python Virtual Environment',
    version_expansion = 'declared Python versions are targeted',
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
    version_expansion = 'declared Python virtual environments are targeted',
)
def clean_python_packages( context, version = None ): # pylint: disable=unused-argument
    ''' Removes unused Python packages. '''
    context_options = __.derive_venv_context_options( version = version )
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
        in indicate_current_python_packages( context_options[ 'env' ] ) )
    requirements_text = '\n'.join(
        installed - requested - { __.project_name } )
    if not requirements_text: return
    execute_pip_with_requirements(
        context_options, 'uninstall', requirements_text,
        pip_options = ( '--yes', ) )


@_task( )
def clean( context, version = None ):
    ''' Cleans all caches. '''
    clean_python_packages( context, version = version )
    clean_pycaches( context )
    clean_tool_caches( context )


@_task(
    'Lint: Package Security',
    version_expansion = 'declared Python platforms are targeted',
)
def check_security_issues( context, version = None ):
    ''' Checks for security issues in utilized packages and tools.

        This task requires Internet access and may take some time. '''
    context_options = __.derive_venv_context_options( version = version )
    context.run( f"safety check", pty = __.on_tty, **context_options )


@_task( 'Freshen: Version Manager' )
def freshen_asdf( context ):
    ''' Asks Asdf to update itself.

        This task requires Internet access and may take some time. '''
    context.run( 'asdf update', pty = __.on_tty )
    context.run( 'asdf plugin update python', pty = __.on_tty )
    # TODO: Preserve this call after 'freshen_asdf' has been removed.
    from ..platforms import install_python_builder
    install_python_builder( )


@_task( task_nomargs = dict( pre = ( freshen_asdf, ), ), )
def freshen_python( context, version = None ):
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
    context.run( "asdf local python {versions}".format(
        versions = ' '.join( successor_versions ) ), pty = True )
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
    version_expansion = 'declared Python virtual environments are targeted',
)
def freshen_python_packages( context, version = None ):
    ''' Updates declared Python packages in Python virtual environment. '''
    context_options = __.derive_venv_context_options( version = version )
    from ..platforms import pep508_identify_python
    identifier = pep508_identify_python( version = version )
    from ..packages import (
        calculate_python_packages_fixtures,
        install_python_packages,
        record_python_packages_fixtures,
    )
    install_python_packages( context_options )
    fixtures = calculate_python_packages_fixtures( context_options[ 'env' ] )
    record_python_packages_fixtures( identifier, fixtures )
    check_security_issues( context, version = version )
    test( context, version = version )


@_task( 'Freshen: Git Modules' )
def freshen_git_modules( context ):
    ''' Performs recursive update of all Git modules.

        This task requires Internet access and may take some time. '''
    context.run(
        'git submodule update --init --recursive --remote', pty = True )


@_task( 'Freshen: Git Hooks' )
def freshen_git_hooks( context ):
    ''' Updates Git hooks to latest tagged release.

        This task requires Internet access and may take some time. '''
    context.run(
        f"pre-commit autoupdate --config {__.paths.configuration.pre_commit}",
        pty = True, **__.derive_venv_context_options( ) )


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
    version_expansion = 'declared Python virtual environments are targeted',
)
def lint_bandit( context, version = None ):
    ''' Security checks the source code with Bandit. '''
    files = (
        __.paths.sources.prj.python3,
        __.paths.scripts.prj.python3,
        __.paths.tests.prj.python3,
        __.paths.project / 'develop.py',
        __.paths.project / 'setup.py',
        __.paths.sources.prj.sphinx / 'conf.py',
    )
    files_str = ' '.join( map( str, files ) )
    context.run(
        "bandit --recursive --verbose "
        f"--configfile {__.paths.configuration.pyproject} {files_str}",
        pty = True, **__.derive_venv_context_options( version = version ) )


@_task(
    'Lint: Mypy',
    task_nomargs = dict( iterable = ( 'packages', 'modules', 'files', ), ),
    version_expansion = 'declared Python virtual environments are targeted',
)
def lint_mypy( context, packages, modules, files, version = None ):
    ''' Lints the source code with Mypy. '''
    context_options = __.derive_venv_context_options( version = version )
    if not __.test_package_executable( 'mypy', context_options[ 'env' ] ):
        return
    if not packages and not modules and not files:
        files = (
            __.paths.sources.prj.python3,
            __.paths.scripts.prj.python3,
            __.paths.tests.prj.python3,
            __.paths.project / 'develop.py',
            __.paths.project / 'setup.py',
            __.paths.sources.prj.sphinx / 'conf.py',
        )
    packages_str = ' '.join( map(
        lambda package: f"--package {package}", packages ) )
    modules_str = ' '.join( map(
        lambda module: f"--module {module}", modules ) )
    files_str = ' '.join( map( str, files ) )
    context.run(
        f"mypy {packages_str} {modules_str} {files_str}",
        pty = True, **context_options )


@_task(
    'Lint: Pylint',
    task_nomargs = dict( iterable = ( 'targets', 'checks', ), ),
    version_expansion = 'declared Python virtual environments are targeted',
)
def lint_pylint( context, targets, checks, version = None ):
    ''' Lints the source code with Pylint. '''
    context_options = __.derive_venv_context_options( version = version )
    if not __.test_package_executable( 'pylint', context_options[ 'env' ] ):
        return
    reports_str = '--reports=no --score=no' if targets or checks else ''
    if not targets:
        targets = (
            *__.paths.sources.prj.python3.rglob( '*.py' ),
            *__.paths.scripts.prj.python3.rglob( '*.py' ),
            *__.paths.tests.prj.python3.rglob( '*.py' ),
            __.paths.project / 'develop.py',
            __.paths.project / 'setup.py',
            __.paths.sources.prj.sphinx / 'conf.py',
        )
    targets_str = ' '.join( map( str, targets ) )
    checks_str = (
        "--disable=all --enable={}".format( ','.join( checks ) )
        if checks else '' )
    context.run(
        f"pylint {reports_str} {checks_str} {targets_str}",
        pty = True, **context_options )


@_task(
    'Lint: Semgrep',
    version_expansion = 'declared Python virtual environments',
)
def lint_semgrep( context, version = None ):
    ''' Lints the source code with Semgrep. '''
    context_options = __.derive_venv_context_options( version = version )
    if not __.test_package_executable( 'semgrep', context_options[ 'env' ] ):
        return
    files = (
        __.paths.sources.prj.python3,
        __.paths.scripts.prj.python3,
        __.paths.tests.prj.python3,
        __.paths.project / 'develop.py',
        __.paths.project / 'setup.py',
        __.paths.sources.prj.sphinx / 'conf.py',
    )
    files_str = ' '.join( map( str, files ) )
    sgconfig_path = __.paths.scm_modules.aux.joinpath(
        'semgrep-rules', 'python', 'lang' )
    context.run(
        #f"strace -ff -tt --string-limit=120 --output=strace/semgrep "
        f"semgrep --config {sgconfig_path} --error --use-git-ignore "
        f"{files_str}", pty = __.on_tty, **context_options )


@_task( )
def lint( context, version = None ):
    ''' Lints the source code. '''
    for version_ in __.calculate_python_versions( version ):
        lint_pylint( context, targets = ( ), checks = ( ), version = version_ )
        lint_semgrep( context, version = version_ )
        lint_mypy(
            context,
            packages = ( ), modules = ( ), files = ( ), version = version_ )
        lint_bandit( context, version = version_ )


@_task( 'Artifact: Code Coverage Report' )
def report_coverage( context ):
    ''' Combines multiple code coverage results into a single report. '''
    context_options = __.derive_venv_context_options( )
    context.run( 'coverage combine', pty = True, **context_options )
    context.run( 'coverage report', pty = True, **context_options )
    context.run( 'coverage html', pty = True, **context_options )
    context.run( 'coverage xml', pty = True, **context_options )


@_task(
    version_expansion = 'declared Python virtual environments are targeted',
)
def test( context, prelint = True, version = None ):
    ''' Runs the test suite in Python virtual environment. '''
    clean( context, version = version )
    if prelint: lint( context, version = version )
    __.render_boxed_title( 'Test: Unit + Code Coverage', supplement = version )
    context_options = __.derive_venv_context_options( version = version )
    context_options[ 'env' ].update( dict(
        HYPOTHESIS_STORAGE_DIRECTORY = __.paths.caches.hypothesis,
        PYTHONUNBUFFERED = 'TRUE', # Ensure complete crash output.
    ) )
    context.run(
        f"coverage run --source {__.project_name}",
        pty = True, **context_options )


@_task( 'Test: Documentation URLs' )
def check_urls( context ):
    ''' Checks the HTTP URLs in the documentation for liveness. '''
    context.run(
        f"sphinx-build -b linkcheck {__.sphinx_options} "
        f"{__.paths.sources.prj.sphinx} {__.paths.artifacts.sphinx_linkcheck}",
        pty = __.on_tty, **__.derive_venv_context_options( ) )


@_task( 'Test: README Render' )
def check_readme( context ):
    ''' Checks that the README will render correctly on PyPI. '''
    path = _get_sdist_path( )
    context.run(
        f"twine check {path}",
        pty = __.on_tty, **__.derive_venv_context_options( ) )


@_task(
    'Artifact: Source Distribution',
    task_nomargs = dict(
        pre = ( test, check_urls, ), post = ( check_readme, ),
    ),
)
def make_sdist( context, signature = True ):
    ''' Packages the Python sources for release. '''
    from ..user_interface import assert_gpg_tty
    assert_gpg_tty( )
    path = _get_sdist_path( )
    if path.exists( ): path.unlink( ) # TODO: Python 3.8: missing_ok = True
    # TODO: https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html
    context.run(
        'python3 setup.py sdist', **__.derive_venv_context_options( ) )
    if signature:
        context.run( f"gpg --detach-sign --armor {path}", pty = True )


def _get_sdist_path( ):
    project_version = __.discover_project_version( )
    name = f"{__.project_name}-{project_version}.tar.gz"
    return __.paths.artifacts.sdists / name


@_task(
    'Artifact: Python Wheel',
    task_nomargs = dict( pre = ( make_sdist, ), ),
)
def make_wheel( context, signature = True ):
    ''' Packages a Python wheel for release. '''
    from ..user_interface import assert_gpg_tty
    assert_gpg_tty( )
    path = _get_wheel_path( )
    if path.exists( ): path.unlink( ) # TODO: Python 3.8: missing_ok = True
    # TODO: https://blog.ganssle.io/articles/2021/10/setup-py-deprecated.html
    context.run(
        'python3 setup.py bdist_wheel', **__.derive_venv_context_options( ) )
    if signature:
        context.run( f"gpg --detach-sign --armor {path}", pty = True )


def _get_wheel_path( ):
    project_version = __.discover_project_version( )
    name = f"{__.project_name}-{project_version}-py3-none-any.whl"
    return __.paths.artifacts.wheels / name


@_task(
    'Artifact: Documentation',
    task_nomargs = dict( pre = ( check_urls, ), ),
)
def make_html( context ):
    ''' Generates documentation as HTML artifacts. '''
    from ..fs_utilities import unlink_recursively
    unlink_recursively( __.paths.artifacts.sphinx_html )
    context.run(
        f"sphinx-build -b html {__.sphinx_options} "
        f"{__.paths.sources.prj.sphinx} {__.paths.artifacts.sphinx_html}",
        pty = __.on_tty, **__.derive_venv_context_options( ) )


@_task( task_nomargs = dict( pre = ( clean, make_wheel, make_html, ), ), )
def make( context ): # pylint: disable=unused-argument
    ''' Generates all of the artifacts. '''


def _ensure_clean_workspace( context ):
    ''' Error if version control reports any dirty or untracked files. '''
    result = context.run( 'git status --short', pty = True )
    if result.stdout or result.stderr:
        # TODO: Use different error-handling mechanism.
        from invoke import Exit
        raise Exit( 'Dirty workspace. Please stash or commit changes.' )


@_task( 'Version: Adjust' )
def bump( context, piece ):
    ''' Bumps a piece of the current version. '''
    _ensure_clean_workspace( context )
    from ..user_interface import assert_gpg_tty
    assert_gpg_tty( )
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
def branch_release( context, remote = 'origin' ):
    ''' Makes a new branch for development torwards a release. '''
    from invoke import Exit  # TODO: Use different error-handling mechanism.
    _ensure_clean_workspace( context )
    project_version = __.discover_project_version( )
    mainline_regex = __.re.compile(
        r'''^\s+HEAD branch:\s+(.*)$''', __.re.MULTILINE )
    mainline_branch = mainline_regex.search( context.run(
        f"git remote show {remote}", hide = 'stdout' ).stdout.strip( ) )[ 1 ]
    true_branch = context.run(
        'git branch --show-current', hide = 'stdout' ).stdout.strip( )
    if mainline_branch != true_branch:
        raise Exit( f"Cannot create release from branch: {true_branch}" )
    this_version = __.Version.from_string( project_version )
    stage = this_version.stage
    if 'a' != stage:
        raise Exit( f"Cannot create release from stage: {stage}" )
    target_branch = f"release-{this_version.major}.{this_version.minor}"
    context.run( f"git checkout -b {target_branch}", pty = True )


@_task( )
def check_code_style( context, write_changes = False ):
    ''' Checks code style of new changes. '''
    yapf_options = [ ]
    if write_changes: yapf_options.append( '--in-place --verbose' )
    yapf_options_string = ' '.join( yapf_options )
    context.run(
        f"git diff --unified=0 --no-color -- {__.paths.sources.prj.python3} "
        f"| yapf-diff {yapf_options_string}",
        pty = __.on_tty, **__.derive_venv_context_options( ) )


@_task( 'SCM: Push Branch with Tags' )
def push( context, remote = 'origin' ):
    ''' Pushes commits on current branch, plus all tags. '''
    # TODO: Discover remote corresponding to current branch.
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
    context.run( 'git push --no-verify --tags', pty = True )


@_task( )
def check_pip_install( context, index_url = '', version = None ):
    ''' Checks import of current package after installation via Pip. '''
    version = version or __.discover_project_version( )
    __.render_boxed_title( f"Verify: Python Package Installation ({version})" )
    from tempfile import TemporaryDirectory
    from time import sleep
    from venv import create as create_venv
    from invoke import Failure
    with TemporaryDirectory( ) as venv_path:
        venv_path = __.Path( venv_path )
        create_venv( venv_path, clear = True, with_pip = True )
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
            except Failure:
                if attempts_count_max == attempts_count: raise
                sleep( 2 ** attempts_count )
            else: break
        python_import_command = (
            f"import {__.project_name}; "
            f"print( {__.project_name}.__version__ )" )
        context.run(
            f"python -c '{python_import_command}'",
            pty = True, **context_options )


@_task( )
def check_pypi_integrity( context, version = None, index_url = '' ):
    ''' Checks integrity of project packages on PyPI.
        If no version is provided, the current project version is used.

        This task requires Internet access and may take some time. '''
    version = version or __.discover_project_version( )
    __.render_boxed_title( f"Verify: Python Package Integrity ({version})" )
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
def check_pypi_package( context, package_url ):
    ''' Verifies signature on package. '''
    from ..user_interface import assert_gpg_tty
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
        context.run( f"gpg --verify {signature_path}" )


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
def upload_test_pypi( context ):
    ''' Publishes current sdist and wheels to Test PyPI. '''
    _upload_pypi( context, 'testpypi' )


@_task(
    task_nomargs = dict(
        pre = (
            __.call( upload_test_pypi ),
            __.call( test, version = 'ALL' ),
        ),
        post = ( check_pypi_integrity, check_pip_install, ),
    ),
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
    process_environment = context_options.get( 'env', { } )
    process_environment.update( _get_pypi_credentials( repository_name ) )
    context_options[ 'env' ] = process_environment
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
@_task(
    'Publication: Github Pages',
    task_nomargs = dict( pre = ( test, make_html, ), ),
)
def upload_github_pages( context ):
    ''' Publishes Sphinx HTML output to Github Pages for project. '''
    # Use relative path, since 'git subtree' needs it.
    html_path = __.paths.artifacts.sphinx_html.relative_to( __.paths.project )
    nojekyll_path = html_path / '.nojekyll'
    target_branch = 'documentation'
    from contextlib import ExitStack as CMStack
    with CMStack( ) as cm_stack:
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


@_task( task_nomargs = dict( pre = ( bump_patch, push, upload_pypi, ), ), )
def release_new_patch( context ): # pylint: disable=unused-argument
    ''' Unleashes a new patch upon the world. '''


@_task( task_nomargs = dict( pre = ( bump_stage, push, upload_pypi, ), ), )
def release_new_stage( context ): # pylint: disable=unused-argument
    ''' Unleashes a new stage upon the world. '''


@_task( )
def run( context, command, version = None ):
    ''' Runs command in virtual environment. '''
    context.run(
        command,
        pty = __.on_tty,
        **__.derive_venv_context_options( version = version ) )
