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

''' Management of virtual environments. '''


from lockup import NamespaceClass as _NamespaceClass
class __( metaclass = _NamespaceClass ):

    from lockup import reclassify_module


def build_python_venv( context, version, overwrite = False ):
    ''' Creates virtual environment for requested Python version. '''
    from devshim.user_interface import render_boxed_title
    render_boxed_title( f"Build: Python Virtual Environment ({version})" )
    from devshim.platforms import detect_vmgr_python_path
    python_path = detect_vmgr_python_path( version )
    from devshim.environments import derive_venv_path
    from devshim.fs_utilities import ensure_directory
    venv_path = ensure_directory( derive_venv_path( version, python_path ) )
    venv_options = [ ]
    if overwrite: venv_options.append( '--clear' )
    venv_options_str = ' '.join( venv_options )
    context.run(
        f"{python_path} -m venv {venv_options_str} {venv_path}", pty = True )
    _install_packages_into_venv( context, version, venv_path )


def _install_packages_into_venv( context, version, venv_path ):
    from devshim.environments import derive_venv_context_options
    context_options = derive_venv_context_options( venv_path )
    from .packages import install_python_packages
    install_python_packages( context, context_options )
    from devshim.packages import (
        calculate_python_packages_fixtures,
        record_python_packages_fixtures,
    )
    fixtures = calculate_python_packages_fixtures( context_options[ 'env' ] )
    from devshim.platforms import pep508_identify_python
    identifier = pep508_identify_python( version = version )
    record_python_packages_fixtures( identifier, fixtures )


__.reclassify_module( __name__ )
