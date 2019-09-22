#!/usr/bin/env python
"""
Create desktop shortcuts for Windows
"""
from __future__ import print_function
import os
import sys

from .shortcut import shortcut
from . import UserFolders

import win32com.client
#from win32com.shell import shellcon

# Windows Special Folders
# ID numbers from https://gist.github.com/maphew/47e67b6a99e240f01aced8b6b5678eeb
# https://docs.microsoft.com/en-gb/windows/win32/api/shldisp/ne-shldisp-shellspecialfolderconstants#constants
#
# Start menu: user = 11, all users = 22
# Desktop   : user =  0, all users = 25

scut_ext = 'lnk'
ico_ext = 'ico'

_SHELLAPP = win32com.client.Dispatch("Shell.Application")
_WSHELL = win32com.client.Dispatch("Wscript.Shell")

def _getwinfolder(idnum):
    return _SHELLAPP.namespace(idnum).self.path

def get_homedir():
    '''Return home directory'''
    return _getwinfolder(40)

def get_desktop():
    '''Return user Desktop folder'''
    # shellcon.CSIDL_DESKTOP ?
    return _getwinfolder(0)

def get_startmenu():
    '''Return user Start Menu folder'''
    # shellcon.CSIDL_STARTMENU ?
    return _getwinfolder(11)

def get_folders():
    """get user-specific folders

    Returns:
    -------
    Named tuple with fields 'home', 'desktop', 'startmenu'

    Example:
    -------
    >>> from pyshortcuts import get_folders
    >>> folders = get_folders()
    >>> print("Home, Desktop, StartMenu ",
    ...       folders.home, folders.desktop, folders.startmenu)
    """
    return UserFolders(get_homedir(), get_desktop(), get_startmenu())


def make_shortcut(script, name=None, description=None, icon=None,
                  folder=None, terminal=True, desktop=True,
                  startmenu=True, executable=None):
    """create shortcut

    Arguments:
    ---------
    script      (str) path to script, may include command-line arguments
    name        (str, None) name to display for shortcut [name of script]
    description (str, None) longer description of script [`name`]
    icon        (str, None) path to icon file [python icon]
    folder      (str, None) subfolder of Desktop for shortcut [None] (See Note 1)
    terminal    (bool) whether to run in a Terminal [True]
    desktop     (bool) whether to add shortcut to Desktop [True]
    startmenu   (bool) whether to add shortcut to Start Menu [True] (See Note 2)
    executable  (str, None) name of executable to use [this Python] (see Note 3)

    Notes:
    ------
    1. `folder` will place shortcut in a subfolder of Desktop and/or Start Menu
    2. Start Menu does not exist for Darwin / MacOSX
    3. executable defaults to the Python executable used to make shortcut.
    """
    userfolders = get_folders()
    scut = shortcut(script, userfolders, name=name, description=description,
                    folder=folder, icon=icon)

    if executable is None:
        executable = os.path.join(sys.prefix, 'pythonw.exe')
        if terminal:
            executable = os.path.join(sys.prefix, 'python.exe')

    # Check for other valid ways to run the script
    # try appending .exe if script itself not found
    if not os.path.exists(scut.full_script):
        tname = scut.full_script + '.exe'
        if os.path.exists(tname):
            executable = tname
            scut.full_script = ''

    # If script is already executable use it directly instead of via pyexe
    ext = os.path.splitext(scut.full_script)[1].lower()
    known_exes = [ext.lower() for ext in os.environ['PATHEXT'].split(os.pathsep)]
    if ext in known_exes:
        executable = scut.full_script
        scut.full_script = ''

    for (create, folder) in ((desktop, scut.desktop_dir),
                             (startmenu, scut.startmenu_dir)):
        if create:
            if not os.path.exists(folder):
                os.makedirs(folder)
            dest = os.path.join(folder, scut.target)

            wscript = _WSHELL.CreateShortCut(dest)
            wscript.Targetpath = '"%s"' % executable
            wscript.Arguments = ' '.join((scut.full_script, scut.arguments))
            wscript.WorkingDirectory = folders.home
            wscript.WindowStyle = 0
            wscript.Description = scut.description
            wscript.IconLocation = scut.icon
            wscript.save()

    return scut
