# -*- coding: utf-8 -*-

"""\
Utilities
---------

Miscellaneous utilities that do not fit anywhere else in the library.

Currently available utilities

.. autosummary::
   :nosignatures:

   timestamp
   abspath
   ensure_dir
   exec_dir
   find
   grep
   echo
"""

from __future__ import print_function
import sys
import os
import re
from datetime import datetime
from contextlib import contextmanager
import logging
import fnmatch
import itertools
import functools
import pytz

_lgr = logging.getLogger(__name__)

# Adapted from matplotlib code
def user_home_dir():
    """Absolute path to user's home directory"""
    try:
        path = os.path.expanduser("~")
    except ImportError:
        pass
    else:
        if os.path.isdir(path):
            return path

    for ev in ["HOME", "USERPROFILE"]:
        path = os.environ.get(ev)
        if path is not None and os.path.isdir(path):
            return path
    return None

def username():
    """User's login name on the system"""
    import getpass
    return getpass.getuser()

def timestamp(local=False):
    """Timestamp in ISO format

    If ``local`` is set to True, timestamp is returned in local timezone. By
    default, it returns the timestamp in UTC timezone.

    Returns:
        str: Timestamp string in ISO format
    """
    return (datetime.now().isoformat()
            if local else
            datetime.now(pytz.utc).isoformat())

def abspath(fpath):
    """Get the absolute path

    Differs from :func:`os.path.abspath` in that this function will expand
    tilde and shell variables, i.e., combines ``expanduser``, ``expandvars``,
    and ``abspath`` in one call.

    Returns:
        path: Absolute path to the file/directory.

    """
    ptmp1 = os.path.expanduser(fpath)
    ptmp2 = os.path.expandvars(ptmp1)
    return os.path.abspath(ptmp2)

def ensure_dir(dpath):
    """Ensure that the directory exists.

    Checks if the path provided exists on the system. If not, creates it. Also
    creates intermediate directories if they don't exist.

    Returns:
        path: Absolute path to the directory
    """
    absdir = abspath(dpath)
    if not os.path.exists(absdir):
        os.makedirs(absdir)
    return absdir

@contextmanager
def exec_dir(dpath, create=False):
    """A context manager to execute code in a given directory.

    When used within a with-block, the subsequent code is executed within the
    directory ``dpath``. The original working directory (as given by
    :func:`os.getcwd`) is restored at the end of the with-block.
    """
    adir = abspath(dpath)
    if create:
        adir = ensure_directory(adir)
    pwd = os.getcwd()
    try:
        os.chdir(adir)
        yield adir
    finally:
        os.chdir(pwd)

def find(pat, root=None):
    """Unix find command like utility.

    Args:
        pat (str): A pattern with Unix shell-style wildcards.
        root (path): Base directory for starting search (must exist)

    Returns:
        An iterator that yields all files matching the pattern
    """
    basedir = os.getcwd() if root is None else root
    for croot, dirs, files in os.walk(basedir):
        for f in itertools.chain(dirs, files):
            if fnmatch.fnmatch(f, pat):
                yield os.path.relpath(
                    os.path.join(croot, f), basedir)

def coroutine(func):
    """Prime a coroutine for send commands.

    Args:
        func (coroutine): A function that takes values via yield
    """
    @functools.wraps(func)
    def _func(*args, **kwargs):
        fn = func(*args, **kwargs)
        fn.next()
        return fn
    return _func

@coroutine
def echo(fh=sys.stdout):
    """A simple output sink.

    Args:
        fh (file): A valid file handle to print to
    """
    while True:
        output = (yield)
        print(output, file=fh)

@coroutine
def grep(pattern, targets,
         send_close=True,
         matcher="search",
         flags=0):
    """Unix grep-like utility.

    Args:
        pattern (str): A regular expression
        targets (list): A list of consumers that act on matching lines
        send_close (bool): Send close signal to targets when grep exits
        matcher: ``search``, ``match``, ``findall`` methods
        flags: Regexp flags used when compiling pattern
    """
    pat = re.compile(pattern, flags=flags)
    sfunc = getattr(pat, matcher)
    try:
        while True:
            line = (yield)
            m = sfunc(line)
            if m:
                for t in targets:
                    t.send(m)
    except GeneratorExit:
        if send_close:
            for t in targets:
                t.close()
