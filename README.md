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

## CURRENT ISSUES
1. **No Linux support yet!**

## TBD
1. Make reports of your daily PC usage
2. Make: Makes pruductivity predictions (concentration, sleepiness, bad habits etc.) and recommendations using machine learning on
    1. the sequence of your windows and
    2. the webcam photos.

## INSTALLATION:

1. Copy files to a whatever folder (path) you want.
2. Setup startup of the script:
    ### On Windows 10:
    1. Open another Windows Explorer Windows
    2. Using Windows Explorer, go to C:\\Users\\**YOUR_USER_NAME**\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup
    3. Right-click empty space in the folder
    4. Click New -> Shortcut
    5. Get the **PATH_WERE_YOU_COPIED_THE_FILES**: click to the right of the folders hierarchy in the folder location line at the top of the Windows Explorer window, where you copied your files
    6. In the text field, type `powershell.exe **PATH_WERE_YOU_COPIED_THE_FILES**\\startup.ps1`
3. You're done!

### Antivirus configuration
* Kaspersky Internet Security (KIS)
    * on the first run of the script, KIS should prompt you to allow webcamera and other accesses. Unless you think differently, you should mark the flag to remember the decision for this application and click "Allow".
    <details><summary>Small details</summary>
    If you change the code of the script of code manually, KIS will re-ask you about script permissions.
    </details>

## USAGE
First, you can test if the script works. Double click the shortcut you created in the startup folder.
3. Double-click the created shortcut


## CHANGELOG

### Version 0.1:
### Version 0.2:
Added blocker script - only for Linux.

