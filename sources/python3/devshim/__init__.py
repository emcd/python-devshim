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


''' Development support modules. '''


# TODO: __version__


from . import (
    base,
    data,
    environments,
    file_utilities,
    fs_utilities,
    languages,
    locations,
    packages,
    platforms,
    project,
    scm_utilities,
    # TODO: tasks,
    user_interface,
)


def complete_initialization( scribe = None ):
    ''' Performs complete initialization of package.

        Normal module imports, as part of importing the package, are intended
        to be non-intrusive and lightweight. By contrast, this function will
        bootstrap missing dependencies, populate data caches, and set
        immutability upon the package members. '''
    from .packages import ensure_python_packages
    ensure_python_packages(
        domain = ( 'construction', 'development.user-interface', ) )
    # TODO: Remove or conceal dependency on Invoke so that latent import
    #       is not necessary.
    from . import tasks # pylint: disable=unused-import
    if None is not scribe:
        from sys import stderr
        from rich.console import Console
        from rich.logging import RichHandler
        from .base import narration_target
        for handler in scribe.handlers: scribe.removeHandler( handler )
        # TODO: Alter log format.
        scribe.addHandler( RichHandler( console = Console(
            stderr = stderr == narration_target ) ) )
        scribe.info( 'Rich logging enabled.' )
    # TODO: Tell exception factories to start using Omniexception.
    _reclassify_modules( )

def _reclassify_modules( ):
    ''' Reclassifies package for attribute concealment and immutability. '''
    from types import ModuleType as Module
    from lockup import reclassify_module
    for attribute in globals( ):
        if not isinstance( attribute, Module ): continue
        if hasattr( attribute, 'complete_initialization' ):
            attribute.complete_initialization( )
        reclassify_module( attribute )
    reclassify_module( __package__ )
