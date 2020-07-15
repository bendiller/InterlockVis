"""Just a scratch file for using Python to generate the InterlockComponent JSON"""
import logging

import jsons

from interlock import Interlock
from ilock_cfg_payload import fname, payload  # Used to keep real config out of version control


def demonstrate_ser_deser(obj):
    """Demonstrate serialization and deserialization and show equality of repr"""
    serialized = jsons.dumps(obj)
    deserialized = jsons.loads(serialized, Interlock)

    logging.info(f"Original:  {repr(obj)}")
    logging.info(f"Processed: {repr(deserialized)}")
    logging.info(f"Equal?: {repr(obj) == repr(deserialized)}")


def write_file(fname, obj):
    with open(fname, 'w') as f:
        f.write(jsons.dumps(obj))


def read_file(fname):
    with open(fname, 'r') as f:
        return jsons.loads(f.read(), Interlock)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # demonstrate_ser_deser(payload)
    # write_file(fname, payload)
    result = read_file(fname)
    logging.info(f"Equal?: {repr(payload) == repr(result)}")
