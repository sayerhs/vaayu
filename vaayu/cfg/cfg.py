# -*- coding: utf-8 -*-

"""
Configuration
"""

import os
import os.path as pth
import platform
import logging
from logging.config import dictConfig

from ..prelude.attrdict import AttrDict
from ..prelude import utils

_lgr = logging.getLogger(__name__)

#: Default filename for the config file
_rcfile_default = "vaayurc.yml"

#: Environment variable containing the path to the system config file
_rcsys_var = "VAAYURC_SYSTEM"

#: Environment variable for the user specific config file
_rcfile_var = "VAAYURC"

class VaayuCfg(AttrDict): #pylint: disable=too-many-ancestors
    """Vaayu Configuration Dictionary"""

def _get_appdata_dir():
    """Return the path to the Windows AppData directory"""
    if "%AppData%" in os.environ:
        return pth.join(os.environ["%AppData%"], "vaayu")
    return None

def search_cfg_files():
    """Search locations and return all possible configuration files.

    The following locations are searched and returned in the order mentioned
    below:

       - The file indicated by the contents of :envvar:`VAAYURC_SYSTEM` if it
         exists.

       - On Windows systems, the :file:`%AppData%/vaayu/vaayurc.yml` if it
         exists.

       - The file in home directory, if it exists. Linux:
         :file:`~/.vaayurc.yml`; windows: :file:`%USERPROFILE%/vaayurc.yml`

       - The file indicated by the contents of :envvar:`VAAYURC`, if it exists.

       - :file:`vaayurc.yml` if it exists in the current working directory.

    Returns:
        List of configuration files available

    """
    rcfiles = []

    sys_rc = os.environ.get(_rcsys_var, None)
    if sys_rc and pth.exists(sys_rc):
        rcfiles.append(sys_rc)

    sysname = platform.system().lower()
    if "windows" in sysname:
        appdir = _get_appdata_dir()
        if appdir:
            rcfile = pth.join(appdir, _rcfile_default)
            if pth.exists(rcfile):
                rcfiles.append(rcfile)

    home = utils.user_home_dir()
    if home:
        rcfile = (pth.join(home, "."+_rcfile_default)
                  if not "windows" in sysname else
                  pth.join(home, _rcfile_default))
        if pth.exists(rcfile):
            rcfiles.append(rcfile)

    env_rc = os.environ.get(_rcfile_var, None)
    if env_rc and pth.exists(env_rc):
        rcfiles.append(env_rc)

    cwd_rc = pth.join(os.getcwd(), _rcfile_default)
    if pth.exists(cwd_rc):
        rcfiles.append(cwd_rc)

    return rcfiles

def configure_logging(log_cfg=None):
    """Configure Python logging.

    If ``log_cfg`` is None, then the basic configuration of python logging
    module is used.

    See `Python Logging Documentation <https://docs.python.org/3.6/library/logging.config.html#logging-config-dictschema>`_ for more information.
    """
    def get_default_log_file():
        """Set up default logging file if none provided"""
        sysname = platform.system().lower()
        if "windows" in sysname:
            appdir = _get_appdata_dir()
            if appdir is not None:
                appdir = utils.ensure_dir(appdir)
                return pth.join(appdir, "vaayu.log")
        else:
            vdir = utils.ensure_dir(os.path.join(
                utils.user_home_dir(), ".vaayu"))
            return pth.join(vdir, "vaayu.log")

    if log_cfg is None:
        logging.basicConfig()
    else:
        log_to_file = log_cfg.log_to_file
        log_filename = log_cfg.log_file or get_default_log_file()
        lggr_cfg = log_cfg.pylogger_options

        lggr_cfg.handlers.log_file.filename = log_filename
        if log_to_file:
            lggr_cfg.loggers.vaayu.handlers.append("log_file")
        dictConfig(lggr_cfg)
        if log_to_file:
            _lgr.info("Logging enabled to file: %s"%log_filename) # pylint: disable=logging-not-lazy
        else:
            _lgr.warning("Logging to file disabled.")

def _cfg_manager():
    """Configuration manager"""
    cfg = [None]

    def _init_config(load_files=True):
        """Initialize configuration

        Args:
            load_files (bool): Flag indicating whether YAML files are read
        """
        cdir = pth.dirname(__file__)
        default_yaml = pth.join(cdir, "default_cfg.yml")
        cfg = VaayuCfg.load_yaml(default_yaml)

        if load_files:
            rcfiles = search_cfg_files()
            for rcname in rcfiles:
                ctmp = VaayuCfg.load_yaml(rcname)
                cfg.merge(ctmp)

        log_cfg = cfg.vaayu.get("logging")
        configure_logging(log_cfg)
        # Pop off logger dictionary options
        _ = cfg.vaayu.logging.pop("pylogger_options")
        msg = ("Loaded configuration from files = %s"%rcfiles
               if rcfiles else
               "No configuration found; using defaults.")
        _lgr.debug(msg)
        if not log_cfg.log_to_file:
            _lgr.info(msg)
        return cfg

    def _get_config():
        """Get the configuration object

        On the first call, initializes the configuration object by parsing all
        available configuration files. Successive invocations return the same
        object that can be mutated by the user. The config dictionary can be
        reset by invoking :func:`~vaayu.cfg.cfg.reload_config`.

        Returns:
            VaayuCfg: The configuration dictionary
        """
        if cfg[0] is None:
            cfg[0] = _init_config()
        return cfg[0]

    def _reset_default_config():
        """Reset to default configuration

        Resets to library default configuration. Unlike
        :func:`~vaayu.cfg.cfg.reload_config`, this function does not
        load the configuration files.

        Returns:
            VaayuCfg: The configuration dictionary
        """
        cfg[0] = _init_config(False)
        return cfg[0]

    def _reload_config():
        """Reset the configuration object

        Forces reloading of all the available configuration files and resets
        the modifications made by user scripts.

        See also: :func:`~vaayu.cfg.cfg.reset_default_config`

        Returns:
            VaayuCfg: The configuration dictionary
        """
        cfg[0] = _init_config()
        return cfg[0]

    return _get_config, _reload_config, _reset_default_config

get_config, reload_config, reset_default_config = _cfg_manager()
