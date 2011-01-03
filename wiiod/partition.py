"""
wiiod.partition
~~~~~~~~~~~~~~~

Access a crypted Wii partition and locates the bootloader, the DOL
executable and the filesystem.

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

from Crypto.Cipher import AES

import collections
import struct

# Some magic locations :)
TITLE_KEY_OFFSET = 0x1BF
TITLE_ID_OFFSET = 0x1DC
DATA_START_OFFSET = 0x2B8
DATA_SIZE_OFFSET = 0x2BC

# Nintendo master keys leaked by Team Twiizers
MASTER_KEY = ("\xeb\xe4\x2a\x22\x5e\x85\x93\xe4"
              "\x48\xd9\xc5\x45\x73\x81\xaa\xf7")
MASTER_KEY_KOREAN = ("\x63\xb8\x2b\xb4\xf4\x61\x4e\x2e"
                     "\x13\xf2\xfe\xfb\xba\x4c\x9b\x7e")

# Size of a disc cluster and data stored by cluster
CLUSTER_SIZE = 0x8000
CLUSTER_DATA_SIZE = 0x7C00

# Number of decrypted clusters stored in the LRU cache
CLUSTER_CACHE_SIZE = 128

# Decorator implementing an LRU cache, a-la-functools.lru_cache
def lru_cached(cache_size):
    def decorator(wrapped):
        cache = collections.OrderedDict()
        def wrapper(self, idx):
            try:
                result = cache[idx]
                del cache[idx]
                cache[idx] = result
            except KeyError:
                result = wrapped(self, idx)
                cache[idx] = result
                if len(cache) > cache_size:
                    cache.popitem(0)
            return result
        return wrapper
    return decorator

class Partition(object):
    def __init__(self, disc, part_infos):
        """
        Initializes a partition object from a wiiod.disc.Disc and partition
        informations (of type wiiod.disc.PartitionInfos).
        """
        self.disc = disc
        self.disc_infos = part_infos

        self._read_header()

    def read_raw(self, offset, size):
        """
        Read raw non-decrypted data relative to the partition start.
        """
        return self.disc.read(self.disc_infos.offset + offset, size)

    def read(self, offset, size):
        """
        Reads decrypted data from the partition.
        """
        data = ''
        while size > 0:
            cluster_data = self.read_cluster(offset / CLUSTER_DATA_SIZE)

            start_off = offset % CLUSTER_DATA_SIZE
            last_off = min(start_off + size, CLUSTER_DATA_SIZE)
            read_size = last_off - start_off

            data += cluster_data[start_off:last_off]

            offset += read_size
            size -= read_size
        return data

    @lru_cached(cache_size=CLUSTER_CACHE_SIZE)
    def read_cluster(self, idx):
        """
        Reads and decrypts a data cluster from the disc. Will often be
        cached to avoid redecrypting.
        """
        raw_cluster = self.read_raw(self.data_start + idx * CLUSTER_SIZE,
                                    CLUSTER_SIZE)
        iv = raw_cluster[0x3D0:0x3E0]
        aes = AES.new(self.decryption_key, AES.MODE_CBC, iv)
        return aes.decrypt(raw_cluster[0x400:])

    def _read_header(self):
        """
        Reads the partition header to get informations like the title key and
        the partition data offset/size.
        """
        header = self.read_raw(0, 1024)

        encrypted_title_key = header[TITLE_KEY_OFFSET:TITLE_KEY_OFFSET+0x10]
        title_id = header[TITLE_ID_OFFSET:TITLE_ID_OFFSET+0x8]

        self.data_start = header[DATA_START_OFFSET:DATA_START_OFFSET+4]
        self.data_start = struct.unpack(">L", self.data_start)[0]
        self.data_start *= 4

        self.data_size = header[DATA_SIZE_OFFSET:DATA_SIZE_OFFSET+4]
        self.data_size = struct.unpack(">L", self.data_size)[0]
        self.data_size *= 4

        self.decryption_key = self._decrypt_key(encrypted_title_key, title_id)

    def _decrypt_key(self, key, title_id):
        """
        Decrypts the title decryption key using the encrypted key and the
        title id.
        """
        if self.disc.metadata.region_code == 'K':
            master_key = MASTER_KEY_KOREAN
        else:
            master_key = MASTER_KEY

        iv = title_id + 8 * "\x00"
        aes = AES.new(master_key, AES.MODE_CBC, iv)
        return aes.decrypt(key)
