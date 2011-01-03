"""
wiiod.wiiodfs
~~~~~~~~~~~~~

Partition filesystem access. Open files, read them, etc.

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

import struct

# Magic fixed locations
FST_OFFSET_POS = 0x424

class _File(object):
    """
    Object providing a file-like interface to the data.
    """

    def __init__(self, part, offset, size):
        self.part = part
        self.offset = offset
        self.size = size
        self.pos = 0

    def close(self):
        pass

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        if whence == 0:
            start_pos = 0
        elif whence == 1:
            start_pos = self.pos
        elif whence == 2:
            start_pos = self.size
        else:
            raise ValueError("invalid whence value")

        if start_pos + offset < 0:
            raise IOError("negative offset")

        self.pos = start_pos + offset

    def read(self, size=-1):
        if self.pos >= self.size:
            return ''

        if size < 0:
            size = self.size

        actual_size = min(size, self.size - self.pos)
        data = self.part.read(self.offset + self.pos, actual_size)
        self.pos += actual_size
        return data

class Filesystem(object):
    def __init__(self, part):
        """
        Creates a filesystem object representing the filesystem present on the
        given partition object (of type wiiod.partition.Partition).
        """
        self.part = part

        self._build_tree()

    def open(self, path):
        """
        Opens the provided path and returns a file-like object.
        """
        root = self.tree
        for comp in path.split('/'):
            if comp == '':
                continue
            if comp not in root:
                raise IOError("file not found")
            root = root[comp]

        if isinstance(root, dict):
            raise IOError("is a directory")

        return _File(self.part, *root)

    def listdir(self, path):
        """
        Lists the provided path and return a list of the direct child names.
        """
        root = self.tree
        for comp in path.split('/'):
            if comp == '':
                continue
            if comp not in root:
                raise IOError("file not found")
            root = root[comp]

        if isinstance(root, tuple):
            raise IOError("not a directory")

        return root.keys()

    def _build_tree(self):
        """
        Reads the FileSystem Table (FST) to build the tree structure of the
        filesystem.
        """
        # Offset to the FST
        fst_offset_string = self.part.read(FST_OFFSET_POS, 4)
        self.fst_offset = struct.unpack('>L', fst_offset_string)[0] * 4

        # Offset to the filenames table
        descr_count_string = self.part.read(self.fst_offset, 12)
        self.str_offset = self.fst_offset
        self.str_offset += struct.unpack('>8xL', descr_count_string)[0] * 12

        _, _, self.tree = self._parse_descriptor(0)

    def _parse_descriptor(self, idx):
        """
        Parses the descriptor whose index matches the parameter. Returns the
        number of descriptors parsed (if the descriptor represents a directory,
        all the childs will be parsed), the file name and its data (or childs
        in case of a directory).
        """
        descr_string = self.part.read(self.fst_offset + 12 * idx, 12)
        (name_off, data_off, size) = struct.unpack('>LLL', descr_string)

        data_off *= 4

        is_dir = bool(name_off & 0xFF000000)
        name = self._read_filename(name_off & ~0xFF000000) if idx else ''

        if is_dir:
            children = {}
            idx += 1
            while idx < size:
                idx, child_name, child_data = self._parse_descriptor(idx)
                children[child_name] = child_data
            return idx, name, children
        else:
            return idx + 1, name, (data_off, size)

    def _read_filename(self, offset):
        """
        Reads a filename from the filenames table given its offset.
        """
        real_offset = self.str_offset + offset
        string = self.part.read(real_offset, 256)
        return string[:string.index('\0')]