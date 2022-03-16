import os

from utils import json_load, flatten

ENTRY_DATETIME_FORMAT = '%y_%m_%d__%H_%M_%S'

DEFAULT_TRAIN_SPLIT = .9

SETTINGS = json_load('settings.json')
BLACKLISTED_WINDOWS_TITLES_PARTS = SETTINGS['BLACKLISTED_WINDOWS_TITLES_PARTS']
BROWSERS_BINARIES_NAMES_LIST = SETTINGS['BROWSERS_BINARIES_NAMES_LIST']
BROWSERS_WINDOWS_TITLES_STRINGS = flatten(SETTINGS['BROWSERS_WINDOWS_TITLES_STRINGS'])
WINDOWS_GROUPS = json_load('windows_groups.json') if os.path.exists('windows_groups.json') \
    else json_load('windows_groups_example.json')
