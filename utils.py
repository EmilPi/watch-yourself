import json

from cross_platform import IS_MAC
import pyautogui as pygui


def json_load(fname): return json.load(open(fname))


def close_tab():  # Ctrl+W / Cmd+W on Mac
    pygui.hotkey('command' if IS_MAC else 'ctrl', 'w')


def close_window():  # ALT+F4 / ? on Mac ?
    pygui.hotkey('alt', 'f4')


def flatten(deep_array):
    ret = []
    if isinstance(deep_array, dict):
        for v in deep_array.values():
            ret.extend(v)
    elif isinstance(deep_array, (list, tuple)):
        for v in deep_array:
            ret.extend(v)
    return ret
