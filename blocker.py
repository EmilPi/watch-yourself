#!/usr/bin/env python3
from time import sleep, strftime
import json

from utils import close_tab, close_window
from cross_platform import notify

from get_active_window_title import get_active_window
from get_idle_time import get_idle_time
from cross_platform import IS_LINUX
if IS_LINUX:
    import pyautogui as pygui
else:
    from PIL import ImageGrab

import os

import sys

# defaults
no_screenshot = False
use_webcam = False
use_dslrcam = False
if ('--log-titles-only' in sys.argv) \
  or ('--no-screenshot' in sys.argv):
    no_screenshot = True
else:
    if '--use-webcam' in sys.argv:
        use_webcam = True
    elif '--use-dslr-cam' in sys.argv:
        use_dslrcam = True
        if not IS_LINUX:
            print('Not tested on other OS but linux - use at your own risk!')

dry_run = '--dry-run' in sys.argv

if use_webcam:
    import cv2
if use_dslrcam:
    # need to install libgphoto separately - not tested on Windows
    import gphoto2 as gp

SCRIPT_PATH = '.'
IMG_PATH = '%s%simgs' % (SCRIPT_PATH, os.sep)
LOG_PATH = '%s%slog_all.txt' % (SCRIPT_PATH, os.sep)
SETTINGS_PATH = '%s%ssettings.json' % (SCRIPT_PATH, os.sep)

CAP_FPS_MAX = 2

# Command '['xdotool', 'getwindowpid', '6291465']' returned non-zero exit status 1.
# Traceback (most recent call last):
#   File "blocker.py", line 152, in <module>
#     if multi_logger.window_changed(window_title):
# NameError: name 'window_title' is not defined

# TODO - measure time spent in apps/sites for today
# TODO - add time limits on apps/sites instead of blacklisting and instant closing
# TODO - close apps/sites only after time spent in them exceeds limits


class MultiLogger(object):
    MIN_IDLE_LOGGING_INTERVAL = 10

    def __init__(self,
                 use_webcam=False,
                 use_dslrcam=False,
                 no_screenshot=False,
                 ):
        self.use_webcam = use_webcam
        self.use_dslrcam = use_dslrcam
        self.no_screenshot = no_screenshot
        if not self.use_webcam:
            self.cap = None
        else:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_FPS, CAP_FPS_MAX)
        if not self.use_dslrcam:
            self.dslr = None
        else:
            self.dslr = True
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
        try:
            if IS_LINUX:
                screenshot = pygui.screenshot(img_path)
            else:
                screenshot = ImageGrab.grab(all_screens=True)
        except Exception as e:
            print('failed to make screenshot with error', e)
            return
        screenshot.save(img_path)

    def make_webcam_photo(self):
        if self.cap is None:
            return
        ret, frame = self.cap.read()
        self.cap.grab()  # free any buffer frame, so next time we get the latest frame

        if not ret:
            print("WARNING: webcam didn't return good photo")
            return
        cv2.imwrite('%s%swebcam__%s.png' % (
            IMG_PATH,
            os.sep,
            self._datetime_str()), frame)

    # based on https://github.com/jim-easterbrook/python-gphoto2/blob/master/examples/capture-image.py
    def make_dslrcam_photo(self):
        # keeping the reference to camera in self.dslr leads to strange I/O errors:
        # better to reclaim it each time
        if not self.dslr:
            return
        err, dslr = gp.gp_camera_new()
        gp.gp_camera_init(dslr)
        file_path = dslr.capture(gp.GP_CAPTURE_IMAGE)
        camera_file = dslr.file_get(
            file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
        CAMERA_EXT = 'jpg'  # TODO fix hardcoded ext for my dslr camera
        camera_file.save('%s%sdslrcam__%s.%s' % (
            IMG_PATH,
            os.sep,
            self._datetime_str(),
            CAMERA_EXT
        ))
        dslr.exit()

    def log_idle(self):
        idle_time = get_idle_time()
        if idle_time > 2 * self.last_idle_time \
                or idle_time < self.last_idle_time:
            self.logfile.write('\t%.3f' % idle_time)
            if idle_time > self.MIN_IDLE_LOGGING_INTERVAL:
                self.log_pictures()
            self.last_idle_time = idle_time

    def log_pictures(self):
        # TODO - make this non-blocking maybe?
        self.make_screenshot()
        self.make_webcam_photo()
        self.make_dslrcam_photo()

    def log_all(self, entry_text):
        self.log_entry(entry_text)
        self.log_pictures()

    def window_changed(self, window_title):
        if window_title != self.last_window_title:
            self.last_window_title = window_title
            return True
        return False


class MultiBlocker(object):
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        settings = json.load(open(SETTINGS_PATH, encoding='utf-8'))
        self.BROWSERS_LIST = settings['BROWSERS_LIST']
        self.BLACKLISTED_PAGES_PARTS = settings['BLACKLISTED_PAGES_PARTS']

    def close_tab(self):
        if self.dry_run:
            notify('You should close this tab now!', "Your very fate is in danger!")
        else:
            close_tab()

    def close_window(self):
        if self.dry_run:
            notify('You should close this window now!', "Your very fate is in danger!")
        else:
            close_window()

    def is_bad_browser_window(self, window_title):
        is_browser = any([
            (
                window_title.lower().startswith(browser_binary_name.lower()) or
                window_title.lower().endswith(browser_binary_name.lower())
            )
            for browser_binary_name in self.BROWSERS_LIST])
        return is_browser \
            and any([
                blacklisted_part in window_title
                for blacklisted_part in self.BLACKLISTED_PAGES_PARTS
        ])

    def notify_about_violation(self):
        notify("You are wasting time that is given to you!", "Your very fate is in danger!")


multi_logger = MultiLogger(use_webcam=use_webcam,
                           use_dslrcam=use_dslrcam,
                           no_screenshot=no_screenshot)
multi_blocker = MultiBlocker(dry_run=dry_run)
browser_violation_count = 0
print('starting watch cycle')
while True:
    # TODO - wrap into try/catch, log errors to separate log file
    try:
        window_title = get_active_window()
    except Exception as e:
        print(e)

    if multi_logger.window_changed(window_title):
        multi_logger.log_all(window_title)
        print(window_title)
    if multi_blocker.is_bad_browser_window(window_title):
        browser_violation_count += 1
    else:
        browser_violation_count = 0

    if browser_violation_count == 1:
        multi_blocker.notify_about_violation()
    elif browser_violation_count >= 3:
        multi_blocker.close_tab()

    multi_logger.log_idle()

    sleep_time = 1
    # !! this sleep time must not be shorter than
    # (1. / CAP_FPS_MAX)
    sleep(sleep_time)
