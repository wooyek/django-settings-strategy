# coding=utf-8
# Created 2014 by Janusz Skonieczny

"""
Keys and secrets should be loaded of the environment.
Put here only things that are shared between all production deployments.
"""

import logging
import environ
from website import __version__ as release_version
from pathlib import Path

logging.debug("Settings loading: %s" % __file__)

# This will read only MISSING environment variables from a file
# We want to do this before loading any base settings as they may depend on environment
environ.Env.read_env(str(Path(__file__).parent / "production.env"), DEBUG='False', ASSETS_DEBUG='False')

# noinspection PyUnresolvedReferences
from .base import *

LOGGING['handlers']['console']['formatter'] = 'verbose'
LOGGING['handlers']['file'] = {
    'class': 'logging.handlers.RotatingFileHandler',
    'formatter': 'verbose',
    'backupCount': 3,
    'maxBytes': 4194304,  # 4MB
    'level': 'DEBUG',
    'filename': (os.path.join(ROOT_DIR, 'logs', 'website.log')),
}
LOGGING['root']['handlers'].append('file')

log_file = Path(LOGGING['handlers']['file']['filename'])
if not log_file.parent.exists():  # pragma: no cover
    logging.info("Creating log directory: {}".format(log_file.parent))
    Path(log_file).parent.mkdir(parents=True)

EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")

RAVEN_CONFIG = {
    'dsn': env("RAVEN_CONFIG_DSN"),
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    'release': release_version
}


