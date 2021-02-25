import json

from cross_platform import IS_MAC
import pyautogui as pygui


def json_load(fname): return json.load(open(fname))


def close_tab():  # Ctrl+W / Cmd+W on Mac
    pygui.hotkey('command' if IS_MAC else 'ctrl', 'w')


def close_window():  # ALT+F4 / ? on Mac ?
    pygui.hotkey('alt', 'f4')
