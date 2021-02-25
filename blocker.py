#!/bin/python3
from time import sleep, strftime
import json

import pyautogui as pygui
from idle_time import IdleMonitor

from get_active_window_title import get_active_window

import os

import sys

no_webcam = '--log-titles-only' in sys.argv
if not no_webcam:
    import cv2


SCRIPT_PATH = os.sep.join(__file__.rsplit(os.sep, 1)[:-1])
IMG_PATH = '%s%simgs' % (SCRIPT_PATH, os.sep)
LOG_PATH = '%s%slog_all.txt' % (SCRIPT_PATH, os.sep)
SETTINGS_PATH = '%s%ssettings.json' % (SCRIPT_PATH, os.sep)
# pid = os.getpid()
# PIDAPP="/home/emil/Desktop/Projects/TodoApps/watch-yourself/pidfile.pid"
# op = open(PIDAPP, "w")
# op.write("%s" % pid)
# op.close()



class MultiLogger(object):
    MIN_IDLE_LOGGING_INTERVAL = 10
    def __init__(self, no_webcam=False):
        self.no_webcam = no_webcam
        if self.no_webcam:
            self.cap = None
        else:
            self.cap = cv2.VideoCapture(0)
            # camera warmup, preventing blank images
            for i in range(30):
                self.cap.read()
        self.logfile = open(LOG_PATH, 'a', encoding='utf-8')
        self.idle_monitor = IdleMonitor.get_monitor()
        self.last_idle_time = 0
        self.last_window_title = ''

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cap:
            self.cap.release()
        self.logfile.close()

    @staticmethod
    def _datetime_str():
        return strftime('%y-%m-%d %H:%M:%S')

    def log_entry(self, entry_text):
        self.logfile.write('\n%s : %s' % (
            self._datetime_str(),
            entry_text
        ))

    def make_screenshot(self):
        # NotImplementedError: "scrot" must be installed to use screenshot functions in Linux. Run: sudo apt-get install scrot
        img_path = '%s/screen_%s.png' % (
            IMG_PATH,
            self._datetime_str())
        screenshot = pygui.screenshot(img_path)
        screenshot.save(img_path)

    def make_webcam_photo(self):
        if self.cap is None:
            return
        ret, frame = self.cap.read()
        cv2.imwrite('%s/webcam_%s.png' % (
            IMG_PATH,
            self._datetime_str()), frame)

    def log_idle(self):
        idle_time = self.idle_monitor.get_idle_time()
        if idle_time > 2 * self.last_idle_time \
        or idle_time < self.last_idle_time:
            self.logfile.write('\t%.3f' % idle_time)
            if idle_time > self.MIN_IDLE_LOGGING_INTERVAL:
                self.log_pictures()
            self.last_idle_time = idle_time

    def log_pictures(self):
        self.make_screenshot()
        self.make_webcam_photo()

    def log_all(self, entry_text):
        self.log_entry(entry_text)
        self.log_pictures()

    def window_changed(self, window_title):
        if window_title != self.last_window_title:
            self.last_window_title = window_title
            return True
        return False


class MultiBlocker(object):
    def __init__(self):
        settings = json.load(open(SETTINGS_PATH, encoding='utf-8'))
        self.BROWSERS_LIST = settings['BROWSERS_LIST']
        self.BLACKLISTED_PAGES_PARTS = settings['BLACKLISTED_PAGES_PARTS']

    def close_tab(self):
        pygui.hotkey('ctrl', 'w')

    def close_window(self):
        pygui.hotkey('alt', 'F4')

    def is_bad_browser_window(self, window_title):
        return any([window_title.startswith(
            browser_binary_name)
            for browser_binary_name in self.BROWSERS_LIST]) \
               and any([blacklisted_part in window_title
                        for blacklisted_part in self.BLACKLISTED_PAGES_PARTS])

    def notify_about_violation(self):
        os.system('notify-send "Your fate is in danger!" "You are wasting time that is given to you!"')


multi_logger = MultiLogger(no_webcam=no_webcam)
multi_blocker = MultiBlocker()
browser_violation_count = 0
print('starting watch cycle')
while True:
    try:
        window_title = get_active_window()
    except Exception as e:
        print(e)

    if multi_logger.window_changed(window_title):
        multi_logger.log_all(window_title)
    if multi_blocker.is_bad_browser_window(window_title):
        browser_violation_count += 1
    else:
        browser_violation_count = 0

    if browser_violation_count == 1:
        multi_blocker.notify_about_violation()
    elif browser_violation_count >= 3:
        multi_blocker.close_tab()

    multi_logger.log_idle()

    sleep(1)