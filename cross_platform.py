import sys
import subprocess

IS_LINUX = IS_WINDOWS = IS_MAC = False
PLATFORM = None

if sys.platform in ['linux', 'linux2']:
    PLATFORM = "linux"
    IS_LINUX = True
elif sys.platform in ['Windows', 'win32', 'cygwin']:
    PLATFORM = "windows"
    IS_WINDOWS = True
elif sys.platform in ['Mac', 'darwin', 'os2', 'os2emx']:
    PLATFORM = "mac"
    IS_MAC = True
else:
    print("sys.platform=%s is unknown. Please report." % sys.platform)

import os
def get_cmd_output(cmd, temp_file=None, **kwargs):
    """
    :param cmd:
    :return:
    """
    if temp_file:
        os.system('%s > %s' % (cmd, temp_file))
        with open(temp_file) as f:
            return f.read()
    if isinstance(cmd, str):
        cmd = cmd.split(' ')
    return subprocess.check_output(cmd, **kwargs).decode('utf-8')[:-1]
