#!/bin/python3
from time import sleep, strftime
import json

from utils import close_tab, close_window
from cross_platform import notify

from get_active_window_title import get_active_window
from get_idle_time import get_idle_time
import pyautogui as pygui

import os

import sys

no_webcam = no_screenshot = '--log-titles-only' in sys.argv
no_webcam += '--no-webcam' in sys.argv

if not no_webcam:
    import cv2

SCRIPT_PATH = '.'
IMG_PATH = '%s%simgs' % (SCRIPT_PATH, os.sep)
LOG_PATH = '%s%slog_all.txt' % (SCRIPT_PATH, os.sep)
SETTINGS_PATH = '%s%ssettings.json' % (SCRIPT_PATH, os.sep)




class MultiLogger(object):
    MIN_IDLE_LOGGING_INTERVAL = 10

    def __init__(self, no_webcam=False, no_screenshot=False):
        self.no_webcam = no_webcam
        self.no_screenshot = no_screenshot
        if self.no_webcam:
            self.cap = None
        else:
            self.cap = cv2.VideoCapture(0)
            # camera warmup, preventing blank images
            for i in range(30):
                self.cap.read()
        self.logfile = open(LOG_PATH, 'a', encoding='utf-8')
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
        return strftime('%y_%m_%d__%H_%M_%S')

    def log_entry(self, entry_text):
        self.logfile.write('\n%s : %s' % (
            self._datetime_str(),
            entry_text
        ))
        self.logfile.flush()

    def make_screenshot(self):
        if self.no_screenshot:
            return
        # NotImplementedError: "scrot" must be installed to use screenshot functions in Linux. Run: sudo apt-get install scrot
        img_path = '%s%sscreen__%s.png' % (
            IMG_PATH,
            os.sep,
            self._datetime_str())
        screenshot = pygui.screenshot(img_path)
        screenshot.save(img_path)

    def make_webcam_photo(self):
        if self.cap is None:
            return
        ret, frame = self.cap.read()
        if not ret:
            print("WARNING: webcam didn't return good photo")
            return
        cv2.imwrite('%s%swebcam__%s.png' % (
            IMG_PATH,
            os.sep,
            self._datetime_str()), frame)

    def log_idle(self):
        idle_time = get_idle_time()
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
        close_tab()

    def close_window(self):
        close_window()

    def is_bad_browser_window(self, window_title):
        is_browser = any([window_title.lower().startswith(
            browser_binary_name.lower())
            for browser_binary_name in self.BROWSERS_LIST])
        return is_browser \
            and any([
                blacklisted_part in window_title
                for blacklisted_part in self.BLACKLISTED_PAGES_PARTS
        ])

    def notify_about_violation(self):
        notify("You are wasting time that is given to you!", "Your very fate is in danger!")


multi_logger = MultiLogger(no_webcam=no_webcam, no_screenshot=no_screenshot)
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
