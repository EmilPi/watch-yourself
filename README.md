# watch-yourself
A tool to watch and analyse your PC activity.

New contributors are most welcome! Anyone intersted in the topics below, please PM.
This is solely open-source project. The purpose is to make people better reflect on how they spend time of their lives and raise self-awareness.

Want to see your daily computer usage reports? This tool is intended right for this!
This tool currently
* Regularly makes photos with your webcam
* Regularly stores your currently opened window in the text file

## DEPENDENCIES AND REQUIREMENTS:
Python 3 should be installed on system and python.exe should be added to your PATH.

COMMON:
* opencv-python

WINDOWS 10:
* pywin


## TBD
1. Make reports of your daily PC usage
2. Make pruductivity predictions (concentration, sleepiness, bad habits etc.) and recommendations using machine learning on
    1. the sequence of your windows and
    2. the webcam photos.
3. Make windowed/tray icon app with user-friendly interface

## INSTALLATION:

1. cd into this directory
2. run
    1. `pip install -r requirements_linux.txt` for Linux
    2. `pip install -r requirements_windows.txt` for Windows
    3. `pip install -r requirements_mac.txt` for Mac
3. Done

## USAGE
### Windows:
1. Right-click on `blocker.py` file
2. choose 'Open with...'
3. Select Python (find it in the programs list or locate python.exe binary)
4. Choose 'Always use this program to open .py files
5. Press `Win + R` keyboard shortcut
6. Type `shell:startup` in the appearing dialog and press `ENTER`
7. Drag `blocker.py` file onto this folder with right mouse/touchpad button, select `Create shortcut` from appearing menu

Now blocker.py will autostart each time you log in!

#### Antivirus configuration
* Kaspersky Internet Security (KIS)
    * on the first run of the script, KIS should prompt you to allow webcamera and other accesses. Unless you think differently, you should mark the flag to remember the decision for this application and click "Allow".
    <details><summary>Small details</summary>
    If you change the code of the script of code manually, KIS will re-ask you about script permissions.
    </details>


### Linux
Make this script autostart.
### On Ubuntu 20.04 LTS, Gnome:
1. Press `Super` key
2. Start typing 'Startup Applications'
3. Press `Add`
4. Put some command name, and type `python <FULL_PATH_TO_REPO_FOLDER>/blocker.py`
5. Press `Add`
6. Press `Close`

Now blocker.py will autostart each time you log in!

## CHANGELOG

### Version 0.1:
### Version 0.2:
Added blocker script - only for Linux.
### Version 0.2.1:
Added blocker script for MacOS too.

### 2021-07-08:
Multiple Windows implementation fixes, updated README.
