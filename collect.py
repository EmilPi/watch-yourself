import cv2
import time
from win32gui import GetWindowText, GetForegroundWindow
from os.path import exists

def run_collection():
    camera = cv2.VideoCapture(0)
    min_period, max_period = 1,15
    last_window_title = ''
    next_screenshot_time = 0
    while True:
        current_window_title = GetWindowText( GetForegroundWindow() )

        if current_window_title != last_window_title or time.time()>next_screenshot_time:
            print('cap!', end='.. ')

            last_window_title = current_window_title
            next_screenshot_time = time.time() + max_period

            timestamp_string = time.strftime('imgs/%Y-%m-%d_%H-%M-%S')

            try:
                ret_val, img = camera.read()
                if ret_val != True:
                    print('Webcamera photo capture failed: trying to acces camera again...')
                    camera = cv2.VideoCapture(0)
                    ret_val, img = camera.read()

            except Exception as e:
                print('On camera read got error:', e)
                camera = cv2.VideoCapture(0)
                ret_val, img = camera.read()

            cv2.imwrite(timestamp_string+'.jpg', img)
            fh=open('windows.txt','a', encoding='utf-8')
            fh.write('%s: %s\n' % (timestamp_string, current_window_title))
            fh.close()

            print('cap in %d s!' % (next_screenshot_time - time.time()), end='.. ', flush=True)

        time.sleep(min_period)

def main():
    run_collection()

if __name__ == '__main__':
    main()
    