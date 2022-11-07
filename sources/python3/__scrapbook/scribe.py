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


''' Custom logger class. '''


def create_scribe_class( ):
    ''' Creates logger class for package. '''
    from logging import getLoggerClass as get_logger_kind
    logger_kind = get_logger_kind( )

    class Scribe( logger_kind ):
        ''' Logger class with preferred method names. '''

        detail      = logger_kind.debug
        inform      = logger_kind.info
        admonish    = logger_kind.warning
        explode     = logger_kind.critical

    return Scribe
