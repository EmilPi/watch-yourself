#!/usr/bin/env python3
from time import sleep, strftime
import json

import requests

from utils import close_tab, close_window
from utils_text import is_browser_window_title_bad
from cross_platform import notify

from get_active_window_title import get_active_window
from get_idle_time import get_idle_time
from cross_platform import IS_LINUX
from PIL import ImageGrab

import os

from vars import ENTRY_DATETIME_FORMAT

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--use-webcam', action='store_true',
                    help="If you want to make webcam photos of yourself while doing actions")
parser.add_argument('--no-webcam', action='store_true',
                    help="If you don\'t want to make webcam photos of yourself while doing actions")
parser.add_argument('--use-dslrcam', action='store_true',
                    help="If you want to make DSLR camera photos of yourself while doing actions")
parser.add_argument('--no-dslrcam', action='store_true',
                    help="If you don\'t want to make DSLR camera photos of yourself while doing actions")
parser.add_argument('--cap-fps', type=int, default=0,
                    help="Maximum fps of webcam. Default 0 (determined by camera and openCV).")
parser.add_argument('--use-droidcam', action='store_true',
                    help="If using DroidCam app on Android phone. Webcam URL should be opened in browser too in order for capture functionality to work! Will require --webcam-url anyway.")
parser.add_argument('--no-droidcam', action='store_true',
                    help="If not using DroidCam app on Android phone. Webcam URL should be opened in browser too in order for capture functionality to work! Will require --webcam-url anyway.")
parser.add_argument('--use-v4l2-backend', action='store_true',
                    help="If using webcam/cam requiring to use V4L2 backend.")
parser.add_argument('--no-v4l2-backend', action='store_true',
                    help="If not using webcam/cam requiring to use V4L2 backend.")
parser.add_argument('--use-screenshot', action='store_true',
                    help="Make screenshots while doing actions")
parser.add_argument('--no-screenshot', action='store_true',
                    help="Don\'t make screenshots while doing actions")

parser.add_argument('--webcam-url', required=False,
                    help="If using phone or other remote webcam, provide its video stream URL")
parser.add_argument('--log-titles-only', action='store_true',
                    help="Do not make screenshots or use cameras while doing actions")
parser.add_argument('--dry-run', action='store_true',
                    help="Log but don't interact with user.")

profile_options = json.load(open('profile_default.json'))
try:
    profile_options.update( json.load(open('profile.json')) )
except FileNotFoundError as e:
    print('Using default profile values before parsing command line args; create \'profile.json\' file to override.')
use_webcam = profile_options.get('use_webcam', False)
use_dslrcam = profile_options.get('use_dslrcam', False)
CAP_FPS = profile_options.get('cap_fps', 0)
use_v4l2_backend = profile_options.get('use_v4l2_backend', False)
no_screenshot = profile_options.get('no_screenshot', False)
use_droidcam = profile_options.get('use_droidcam', False)
webcam_url = profile_options.get('webcam_url', '')

args = parser.parse_args()
if args.use_webcam: use_webcam = True
if args.no_webcam: use_webcam = False
if args.use_dslrcam: use_dslrcam = True
if args.cap_fps: CAP_FPS = args.cap_fps
if args.no_dslrcam: use_dslrcam = False
if args.use_droidcam: use_droidcam = True
if args.no_droidcam: use_droidcam = False
# Attention - this is reverse variable
if args.no_screenshot: no_screenshot = True
if args.use_screenshot: no_screenshot = False
if args.use_v4l2_backend: use_v4l2_backend = True
if args.no_v4l2_backend: use_v4l2_backend = False
webcam_url = args.webcam_url or webcam_url
log_titles_only = args.log_titles_only or False
dry_run = args.dry_run or False

if log_titles_only:
    no_screenshot = True
    use_webcam = False
    use_dslrcam = False
    use_droidcam = False
    webcam_url = ''
if use_dslrcam and not IS_LINUX:
    print('Not tested on other OS but linux - use at your own risk!')

if use_droidcam:
    print(f"make sure to open {webcam_url} in browser - otherwise DroidCam won't let you to capture images!")
if use_v4l2_backend and use_webcam:
    print('Using V4L2 camera backend.')
if dry_run:
    print('Dry run: no actions will be performed.')

if use_webcam:
    import cv2
if use_dslrcam:
    # need to install libgphoto separately - not tested on Windows
    import gphoto2 as gp

SCRIPT_PATH = '.'
IMG_PATH = '%s%simgs' % (SCRIPT_PATH, os.sep)
LOG_PATH = '%s%slog_all.txt' % (SCRIPT_PATH, os.sep)

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

    def __init__(self, use_webcam=False, use_dslrcam=False, use_droidcam=False,
                 webcam_url='',
                 use_v4l2_backend=False,
                 no_screenshot=False,
                 ):
        self.use_webcam = use_webcam
        self.use_dslrcam = use_dslrcam
        self.no_screenshot = no_screenshot
        self.webcam_url = webcam_url
        self.use_droidcam = use_droidcam
        if not self.use_webcam:
            self.cap = None
        else:
            if use_v4l2_backend:
                self.cap = cv2.VideoCapture(cv2.CAP_V4L2)
            elif webcam_url and not use_droidcam:
                self.cap = cv2.VideoCapture(webcam_url)
            else:
                self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # TODO test again with 0 on notebook webcam, ext. webcam
            if CAP_FPS:
                self.cap.set(cv2.CAP_PROP_FPS, CAP_FPS)
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
        return strftime(ENTRY_DATETIME_FORMAT)

    def log_entry(self, entry_text):
        self.logfile.write('\n%s : %s' % (
            self._datetime_str(),
            entry_text
        ))
        self.logfile.flush()

    @staticmethod
    def get_img_save_fpath(
            prefix='screenshot',
            EXT='png'
    ):
        return '%s%s%s__%s.%s' % (
            IMG_PATH,
            os.sep,
            prefix,
            MultiLogger._datetime_str(),
            EXT
        )

    def make_screenshot(self):
        if self.no_screenshot:
            return
        # NotImplementedError: "scrot" must be installed to use screenshot functions in Linux. Run: sudo apt-get install scrot
        img_path = MultiLogger.get_img_save_fpath(prefix='screen', EXT='png')
        try:
            screenshot = ImageGrab.grab(all_screens=True)
        except Exception as e:
            print('failed to make screenshot with error', e)
            return
        screenshot.save(img_path)

    def make_webcam_photo(self):
        EXT = 'png'
        if self.use_droidcam:
            EXT = 'jpg'
        if self.cap is None and not self.use_droidcam:
            return

        save_fname = MultiLogger.get_img_save_fpath(prefix='webcam', EXT=EXT)
        if self.use_droidcam:
            r = requests.get(f'{self.webcam_url}/cam/1/frame.jpg')
            open(save_fname, 'wb').write(r.content)
            return

        ret, frame = self.cap.read()
        self.cap.grab()  # free any buffer frame, so next time we get the latest frame

        if not ret:
            print("WARNING: webcam didn't return good photo")
            return
        cv2.imwrite(save_fname, frame)

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
        camera_file.save(MultiLogger.get_img_save_fpath(prefix='dslrcam', EXT=CAMERA_EXT))
        dslr.exit()

    def log_idle(self):
        try:
            idle_time = get_idle_time()
            if idle_time > 2 * self.last_idle_time \
                    or idle_time < self.last_idle_time:
                self.logfile.write('\t%.3f' % idle_time)
                if idle_time > self.MIN_IDLE_LOGGING_INTERVAL:
                    self.log_pictures()
                self.last_idle_time = idle_time
        except Exception as e:
            print(e)
            print('WARNING: could not get idle time.')

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
        binary_name = window_title.split(' __ ', 1)[0]  # will only be meaningful for Linux
        window_title = window_title.split(' __ ', 1)[-1]
        return is_browser_window_title_bad(window_title, binary_name)

    def notify_about_violation(self):
        notify("You are wasting time that is given to you!", "Your very fate is in danger!")


multi_logger = MultiLogger(use_webcam=use_webcam,
                           use_dslrcam=use_dslrcam,
                           use_droidcam=use_droidcam,
                           no_screenshot=no_screenshot,
                           use_v4l2_backend=use_v4l2_backend,
                           webcam_url=webcam_url
                           )
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
    # (1. / CAP_FPS)
    sleep(sleep_time)
