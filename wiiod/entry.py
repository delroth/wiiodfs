"""
wiiodmount
~~~~~~~~~~

Mounts a Wii optical disc using the wiiod Python module.

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

from __future__ import absolute_import

from fs.expose import fuse
from wiiod import disc, partition, wiiodfs, fs

import os.path
import os
import sys

def main():
    if len(sys.argv) < 3 or '--help' in sys.argv or '-h' in sys.argv:
        print 'usage: %s <image> <mountpoint> [partition index]' % sys.argv[0]
        sys.exit(1)

    try:
        image_file = open(sys.argv[1], 'rb')
    except IOError:
        print '%s: no such file or directory: %s' % (sys.argv[0], sys.argv[1])
        sys.exit(1)

    mount_point = sys.argv[2]
    if not os.path.isdir(mount_point):
        print '%s: %s is not a directory' % (sys.argv[0], sys.argv[2])
        sys.exit(1)

    try:
        part_index = int(sys.argv[3]) if len(sys.argv) > 3 else None
    except ValueError:
        print '%s: the partition index should be an integer' % sys.argv[0]
        sys.exit(1)

    disc_obj = disc.Disc(image_file)
    all_game_parts = [part for part in disc_obj.partitions
                           if part.type == 0]
    if len(all_game_parts) > 1 and part_index is None:
        print 'There is %d game partitions on the disc.' % len(all_game_parts)
        print 'Please relaunch the program and specify the partition index.'
        sys.exit(1)

    if part_index is None:
        part_index = 0

    if part_index >= len(all_game_parts) or part_index < 0:
        print 'Invalid partition index (out of bounds)'
        sys.exit(1)

    part = partition.Partition(disc_obj, all_game_parts[part_index])
    fs_obj = wiiodfs.Filesystem(part)
    pyfs_obj = fs.WiiODFS(fs_obj)

    print 'Use fusermount -u %s to unmount the disc after use.' % mount_point
    if not os.fork():
        fuse.mount(pyfs_obj, mount_point, foreground=True)
