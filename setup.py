#!/usr/bin/env python

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import distutils.core

from piplapis import __version__


py_version = sys.version_info[:2]
if py_version not in [(2, 6), (2, 7)]:
    raise RuntimeError('Python 2.6 or 2.7 is required')


distutils.core.setup(name='piplapis-python',
                     version=__version__,
                     author="Josh Liberty",
                     author_email="josh.liberty@pipl.com",
                     description="Client library for use with the Pipl search API",
                     url="https://pipl.com/dev",
                     license="http://www.apache.org/licenses/LICENSE-2.0",
                     classifiers=[
                         "Intended Audience :: Developers",
                         "Operating System :: OS Independent",
                         "Programming Language :: Python",
                         "Programming Language :: Python :: 2",
                     ],
                     packages=['piplapis', 'piplapis.data'],
                     )
