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

''' Augmentations to Invoke. '''


from invoke import Task as _Task


class Task( _Task ):
    ''' Patches for broken methods. '''

    def argspec(self, invocable): # pylint: disable=arguments-renamed
        ''' Returns the argument specifications for given callable.

            * First item is list of arg names, in order defined.

            * Second item is dict mapping arg names to default values or
              `NO_DEFAULT` (an 'empty' value distinct from None, since None
              is a valid value on its own). '''
        from inspect import (
            Parameter as Variate,
            signature as scan_signature,
        )
        from invoke.tasks import NO_DEFAULT
        acceptable_variate_species = (
            Variate.POSITIONAL_ONLY, Variate.POSITIONAL_OR_KEYWORD, )
        variates = scan_signature( invocable ).parameters
        specifications = {
            variate_name:
            NO_DEFAULT if Variate.empty is variate.default else variate.default
            for variate_name, variate in variates.items( )
            if variate.kind in acceptable_variate_species }
        return specifications.keys( ), specifications


def extract_task_invocable( task ):
    ''' Extracts innermost invocable from Invoke task. '''
    invocable = task.body
    while hasattr( invocable, '__wrapped__' ):
        invocable = invocable.__wrapped__
    return invocable


from lockup import reclassify_module as _reclassify_module
_reclassify_module( __name__ )
