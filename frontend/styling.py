import logging
"""
This module is intended to streamline styling of elements within the GUI, by providing a set of argument dicts to be
accessed by specifying an object or object.attr string.
"""

MAIN_WIDTH = 50


def style_args(obj, attr_name=None):
    idx = obj.__class__.__name__
    if attr_name:
        idx += f".{attr_name}"
    try:
        return styles[idx]
    except IndexError:
        logging.warning(f"Unknown styling index: {idx}")
        return {'background_color': 'red'}


# Styling arguments for objects in interlock.py:
styles = {
    'Interlock.name': {
        'font': 'Any 18',
        'justification': 'center',
        'size': (MAIN_WIDTH, 1),
    },
    'Component.name': {'font': 'Any 12', },
    'Component.desc': {'font': 'Any 12', },
}
