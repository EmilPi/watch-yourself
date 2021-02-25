#!/usr/bin/env python3
# https://stackoverflow.com/a/36419702/3036878

# For Linux:
# Install wnck (sudo apt-get install python-wnck on Ubuntu, see libwnck.)

# For Windows:
# Make sure win32gui is available

# For Mac:
# Make sure AppKit is available

"""Find the currently active window."""

import logging
import sys

# logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
#                     level=logging.DEBUG,
#                     stream=sys.stdout)


def get_active_window_mac():
    return NSWorkspace.sharedWorkspace().frontmostApplication().localizedName()


def get_active_window_linux_failing():
    # Alternatives: http://unix.stackexchange.com/q/38867/4784
    if wnck is not None:
        screen = wnck.screen_get_default()
        screen.force_update()
        window = screen.get_active_window()
        if window is not None:
            pid = window.get_pid()
            with open("/proc/{pid}/cmdline".format(pid=pid)) as f:
                active_window_name = f.read()
    else:
        if gi is not None:
            Gtk.init([])  # necessary if not using a Gtk.main() loop
            screen = Wnck.Screen.get_default()
            screen.force_update()  # recommended per Wnck documentation
            active_window = screen.get_active_window()
            pid = active_window.get_pid()
            with open("/proc/{pid}/cmdline".format(pid=pid)) as f:
                active_window_name = f.read()


def get_cmd_output(cmd):
    """
    assuming no spaces in cmd
    :param cmd:
    :return:
    """
    if isinstance(cmd, str):
        cmd = cmd.split(' ')
    return subprocess.check_output(cmd).decode('utf-8')[:-1]

def get_active_window_linux_working():
    window_id = get_cmd_output('xdotool getwindowfocus')
    active_window_pid = get_cmd_output('xdotool getwindowpid %s' % window_id)
    process_name = get_cmd_output('cat /proc/%s/comm' % active_window_pid)
    process_cmdline = get_cmd_output('cat /proc/%s/cmdline' % active_window_pid)
    if 'PyCharm' in process_cmdline:
        process_name = 'pycharm-community'
    return process_name + ' __ ' + get_cmd_output('xdotool getwindowfocus getwindowname')


def get_active_window_win():
    # http://stackoverflow.com/a/608814/562769
    window = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(window)


if sys.platform in ['linux', 'linux2']:
    # Alternatives: http://unix.stackexchange.com/q/38867/4784

    # try:
    #     import wnck
    # except ImportError:
    #     logging.info("wnck not installed")
    #     wnck = None
    # if wnck is None:
    #     try:
    #         import gi
    #         gi.require_version('Wnck', '3.0')
    #         gi.require_version('Gtk', '3.0')
    #         from gi.repository import Gtk, Wnck
    #         gi = "Installed"
    #     except ImportError:
    #         logging.info("gi.repository not installed")
    #         gi = None
    # get_active_window = get_active_window_linux_failing

    import subprocess

    get_active_window = get_active_window_linux_working

elif sys.platform in ['Windows', 'win32', 'cygwin']:
    # http://stackoverflow.com/a/608814/562769
    import win32gui

    get_active_window = get_active_window_win
elif sys.platform in ['Mac', 'darwin', 'os2', 'os2emx']:
    # http://stackoverflow.com/a/373310/562769
    from AppKit import NSWorkspace

    get_active_window = get_active_window_mac
else:
    print("sys.platform={platform} is unknown. Please report."
          .format(platform=sys.platform))
    print(sys.version)
    exit(1)
