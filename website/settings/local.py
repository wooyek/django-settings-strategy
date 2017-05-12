# coding=utf-8
# Created 2014 by Janusz Skonieczny

import logging
import environ

logging.debug("Settings loading: %s" % __file__)

# This will read missing environment variables from a file
# We wan to do this before loading a base settings as they may depend on environment
environ.Env.read_env(DEBUG='True')

from .base import *

ALLOWED_HOSTS += [
    '127.0.0.1',
    'localhost',
    '.example.com',
    'vagrant',
    ]

# https://docs.djangoproject.com/en/1.6/topics/email/#console-backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

LOGGING['handlers']['mail_admins']['email_backend'] = 'django.core.mail.backends.dummy.EmailBackend'

# Sync task testing
# http://docs.celeryproject.org/en/2.5/configuration.html?highlight=celery_always_eager#celery-always-eager

CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True


