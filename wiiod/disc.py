"""
wiiod.disc
~~~~~~~~~~

Disc image handling utilities: access disc metadatas like game description,
maker code and region, and access raw crypted disc partitions.

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

import collections
import struct

# Some magic constants
WII_MAGIC_NUMBER = 0x5d1c9ea3

VGTABLE_OFFSET = 0x40000
NUMBER_OF_VG = 4

# Metadata from the disc image
Metadata = collections.namedtuple('Metadata', ' '.join((
    'disc_id',
    'game_code',
    'region_code',
    'maker_code',
    'disc_number',
    'disc_version',
    'wii_magic_number',
    'title'
)))

def _metadata_from_string(string):
    binary_format = ">c2sc2sBB16xL4x64s"
    tup = struct.unpack(binary_format, string)

    # Remove NULs from the end of the title
    title = tup[-1][:tup[-1].index('\0')]
    tup = tup[:-1] + (title,)

    return Metadata(*tup)
Metadata.from_string = staticmethod(_metadata_from_string)

# Partition informations. Really simple struct with only four fields.
PartitionInfos = collections.namedtuple('PartitionInfos', ' '.join((
    'volume_group',
    'index',
    'offset',
    'type'
)))

class Disc(object):
    def __init__(self, fp):
        """
        Initializes a disc object from an open file descriptor.
        """
        self.fp = fp
        self._read_metadata()
        self._read_vg_table()

    def read(self, offset, size):
        """
        Reads data from an offset and a size.
        """
        self.fp.seek(offset)
        return self.fp.read(size)

    @property
    def partitions(self):
        """
        Iterates on all the partitions
        """
        for vg in self.volume_groups:
            for part in vg:
                yield part

    def _read_metadata(self):
        """
        Reads and caches the metadata at offset 0x0 on the disc.
        """
        self.metadata = Metadata.from_string(self.read(0, 96))

        # Small sanity check
        if self.metadata.wii_magic_number != WII_MAGIC_NUMBER:
            raise ValueError("wrong magic number on the disc image")

    def _read_vg_table(self):
        """
        Reads the volume groups table, and the partitions table from the
        four volume groups.
        """
        self.volume_groups = []
        for i in xrange(NUMBER_OF_VG):
            tup = struct.unpack('>LL', self.read(VGTABLE_OFFSET + 8 * i, 8))
            number_of_partitions, parttable_offset = tup

            self.volume_groups.append([])
            self._read_partition_table(i, parttable_offset * 4,
                                       number_of_partitions)

    def _read_partition_table(self, volume_group, offset, number_of_parts):
        """
        Reads a partition table from the given informations, filling the
        provided volume group.
        """
        for i in xrange(number_of_parts):
            tup = struct.unpack('>LL', self.read(offset + 8 * i, 8))
            part_offset, part_type = tup

            infos = (volume_group, i, part_offset * 4, part_type)
            self.volume_groups[volume_group].append(PartitionInfos(*infos))
