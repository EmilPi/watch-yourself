from vars import BROWSERS_BINARIES_NAMES_LIST, BROWSERS_WINDOWS_TITLES_STRINGS, BLACKLISTED_WINDOWS_TITLES_PARTS


def is_browser_window_title(title, binary_name=None):
    if binary_name and binary_name.lower() in [_.lower() for _ in BROWSERS_BINARIES_NAMES_LIST]:
        return True
    for browser_window_title_string in BROWSERS_WINDOWS_TITLES_STRINGS:
        if browser_window_title_string.lower() in title.lower():
            return True
    return False


def is_browser_window_title_bad(title, binary_name=None):
    return is_browser_window_title(title, binary_name) and any([
        blacklisted_part.lower() in title.lower()
        for blacklisted_part in BLACKLISTED_WINDOWS_TITLES_PARTS
    ])
