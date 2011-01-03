"""
wiiod.fs
~~~~~~~~

Implementation of a PyFS filesystem over wiiod.wiiodfs.

This file is part of wiiodfs.

wiiodfs is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

wiiodfs is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
wiiodfs.  If not, see <http://www.gnu.org/licenses/>.
"""

# Required because of the fs/wiiod.fs confusion
from __future__ import absolute_import

from fs.base import FS
from fs.errors import UnsupportedError, ResourceInvalidError, \
                      ResourceNotFoundError
from fs.path import normpath

import stat

class WiiODFS(FS):
    _meta = {
        'virtual': False,
        'read_only': True,
        'unicode_paths': False,
        'case_insensitive_paths': False,
        'network': False
    }

    def __init__(self, fs):
        """
        Constructor which takes a wiiod.wiiodfs.Filesystem.
        """
        self.fs = fs

    def close(self):
        pass

    def open(self, path, mode="r", **kwargs):
        if '+' in mode or 'w' in mode or 'a' in mode:
            raise UnsupportedError("write access")
        path = normpath(path)

        if not self.isfile(path):
            if self.isdir(path):
                raise ResourceInvalidError(path)
            else:
                raise ResourceNotFoundError(path)

        return self.fs.open(path)

    def isfile(self, path):
        return self.fs.isfile(normpath(path))

    def isdir(self, path):
        return self.fs.isdir(normpath(path))

    def exists(self, path):
        return self.fs.exists(normpath(path))

    def listdir(self, path="/", wildcard=None, full=False, absolute=False,
                dirs_only=False, files_only=False):
        path = normpath(path)
        if not self.fs.isdir(path):
            raise ResourceInvalidError(path, msg="not a directory")
        paths = self.fs.listdir(path)
        return self._listdir_helper(path, paths, wildcard, full, absolute,
                                    dirs_only, files_only)

    def getinfo(self, path):
        path = normpath(path)
        if self.fs.isdir(path):
            return { 'st_mode': 0555 | stat.S_IFDIR }
        elif self.fs.isfile(path):
            return { 'st_mode': 0444 | stat.S_IFREG,
                     'size': self.fs.getsize(path) }
        else:
            raise ResourceNotFoundError(path)
