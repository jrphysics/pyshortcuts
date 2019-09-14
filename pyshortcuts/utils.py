#!/usr/bin/env python
"""
utilities for pyshortcuts
  get_homedir()         get home directory (all platforms)
  get_win_folders()     get Home, Desktop and Startmenu paths
  fix_paths()           get absolute paths for script, target folder, icon
"""
import os
import sys


platform = sys.platform
if os.name == "nt":
    platform = "win"
if platform == "linux2":
    platform = "linux"


def unixpath(d):
    "unix path"
    return d.replace("\\", "/")


def winpath(d):
    "ensure path uses windows delimiters"
    if d.startswith("//"):
        d = d[1:]
    d = d.replace("/", "\\")
    return d


nativepath = unixpath
if platform == "win":
    nativepath = winpath

HAS_PWD = True
try:
    import pwd
except ImportError:
    HAS_PWD = False

## mhw: WIP: getting a handle on named tuples
def get_win_folders():
    """Return named tuple of Home, Desktop and Startmenu paths.

        folders = get_win_folders()
        print("Home, Desktop, StartMenu ",
            folders.home, folders.desktop, folders.startmenu)
    """
    import win32com.client

    shellapp = win32com.client.Dispatch("Shell.Application")
    from collections import namedtuple

    nt = namedtuple("folders", "home desktop startmenu")
    folders = nt(
        os.environ["USERPROFILE"],
        shellapp.namespace(11).self.path,
        shellapp.namespace(0).self.path,
    )
    return folders
    # Windows Special Folders
    # ID numbers from https://gist.github.com/maphew/47e67b6a99e240f01aced8b6b5678eeb
    # https://docs.microsoft.com/en-gb/windows/win32/api/shldisp/ne-shldisp-shellspecialfolderconstants#constants
    #
    # Start menu: user = 11, all users = 22
    # Desktop   : user =  0, all users = 25


##


def get_homedir():
    "determine home directory of current user"
    home = None

    def get_home_from_env():
        # try '~' which works on most Unixes, then common environmental variables
        for var in ("~", "$HOME", "$HOMEPATH", "$USERPROFILE", "$ALLUSERSPROFILE"):
            p = os.path.expandvars(var)
            if os.path.exists(p):
                return p

    # for Unixes, allow for sudo case
    susername = os.environ.get("SUDO_USER", None)
    if HAS_PWD and susername is not None and home is None:
        home = pwd.getpwnam(susername).pw_dir

    elif home is None:
        home = get_home_from_env()

    # finally, use current folder
    else:
        home = os.path.abspath(".")

    return nativepath(home)


def fix_paths(script, folder=None, icon_path=None, icon=None):
    """get absolute paths to

    1.  script
    2.  desktop folder or subfolder (creating if needed)
    3.  icon

    """
    scriptname = os.path.abspath(script)

    dest = os.path.join(get_homedir(), "Desktop")
    if folder is not None:
        dest = os.path.join(dest, folder)
        if not os.path.exists(dest):
            os.mkdir(dest)

    if icon_path is None:
        _path, _fname = os.path.split(__file__)
        icon_path = os.path.join(_path, "icons")
    if icon is None:
        icon = "py"
    ext = ".ico"
    if platform.startswith("darwin"):
        ext = ".icns"
    iconfile = os.path.abspath(os.path.join(icon_path, icon + ext))

    return scriptname, dest, iconfile
