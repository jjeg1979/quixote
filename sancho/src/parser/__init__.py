from os import listdir

from .btparser import (
    BtParser,
    BT_EXTENSIONS,
    BT_TIMEFRAMES,
    BtOrderType,
    BtPeriods,
    BtPlatforms,
)

BT_FILES = [file for file in listdir(r'sancho/src/payload/') \
    if file.endswith(BT_EXTENSIONS)]

__version__ = '0.1.0'