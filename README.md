# django-settings-strategy
How to handle django settings in a maintainable way

If you like it give me na upvote on SO: 
http://stackoverflow.com/a/43938067/260480

---

So there are some pretty complicated patterns for settings customization that will give them the flexibility in usage of: 

- evnironment, 
- in place settings, 
- sharing common settings blocks and
- branching based on purpose like local/testing/production.

Just thinking about all these intertwining files gives me a headache. 
Combining, importing (sometimes conditionally), overriding, patching of what was already set in case `DEBUG` setting changed later on. 
What a nightmare!

Through the years I went through all different solutions. They all _somewhat_ work, but are so painful to manage. 
WTF! Do we really need all that hassle? We started with just one `settings.py` file. 
Now we need a documentation just to correctly combine all these together in a correct order!

This repo is me trying to hit the sweet spot.

# Let's recap the goals (some common, some mine)

 1. Keep secrets a secret — don't store them in a repo.

 2. Set/read keys and secrets through environment settings, [12 factor style](https://12factor.net/).

 3. Have sensible fallback defaults. Ideally for local development you don't need anything more beside defaults.

 2. …but try to keep defaults production safe. It's better to miss a setting override locally, 
 than having to remember to adjust default settings making it safe for production.

 4. Have the ability to switch `DEBUG` on/off in a way that can have an effect on other settings (eg. using javascript compressed or not).

 5. Switching between purpose settings, like local/testing/staging/production, should be based only on `DJANGO_SETTINGS_MODULE`, nothing more.

 6. …but allow further parametrization through environment settings like `DATABASE_URL`.

 6. …also allow them to use different purpose settings and run them locally side by side, eg. production setup on local developer machine, to access production database or smoke test compressed style sheets.

 7. Fail if an environment variable is not explicitly set (requiring an empty value at minimum), especially in production, eg. `EMAIL_HOST_PASSWORD`.

 8. Respond to default `DJANGO_SETTINGS_MODULE` set in manage.py during [django-admin startproject](https://docs.djangoproject.com/en/dev/ref/django-admin/#startproject)

 9. Keep conditionals to a minimum, if the condition is _the_ purposed environment type (eg. for production set log file and it's rotation), override settings in associated purposed settings file.   

# Do not's

 1. Do not let django read DJANGO_SETTINGS_MODULE setting form a file.  
    Ugh! Think of how meta this is. If you need to have a file (like docker
    env) read that into the environment before staring up a django process.
 
 2. Do not override DJANGO_SETTINGS_MODULE in your project/app code, eg. based on hostname or process name.  
    If you are lazy to set environment variable (like for `setup.py test`) do it in tooling just before you run your project code.
 
 4. Avoid magic and patching of how django reads it's settings, preprocess the settings but do not interfere afterwards.
  
 5. No complicated logic based nonsense. Configuration should be fixed and materialized not computed on the fly. 
    Providing a fallback defaults is just enough logic here.  
    Do you really want to debug, why locally you have correct set of settings but in production on a remote server, 
    on one of hundred machines something computed differently? Oh! Unit tests? For settings? Seriously?      

# Solution

My strategy consists of excellent [django-environ](https://github.com/joke2k/django-environ) used with `ini` style files, 
providing `os.environment` defaults for local development, some minimal and short `settings/<purpose>.py` files that have an 
`import settings/base.py` *AFTER* the `os.environment` updated missing settings from an `INI` file. 
This effectively give us a kind of settings injection.

The trick here is to modify `os.environment` before you import `settings/base.py`.

    .
    │   manage.py
    ├───data
    └───website
    ├───settings
    │   │   __init__.py   <-- imports local for compatybility
    │   │   base.py       <-- almost all the settings, reads from proces environment 
    │   │   local.py      <-- a few modifications for local development
    │   │   production.py <-- ideally is empy and everything is in base 
    │   │   testing.py    <-- mimics production with a reasonable exeptions
    │   │   .env          <-- for local use, not kept in repo
    │   __init__.py
    │   urls.py
    │   wsgi.py


## settings/.env

A defaults for local development. A secret file, to mostly set required environment variables. 
Set them to empty values if they are not required in local development. 
We provide defaults here and not in `settings/base.py` to fail on any other machine if the're missing from the environment.

## settings/local.py

What happens in here, is loading environment from `settings/.env`, then importing common settings 
from `settings/base.py`. After that we can override a few to ease local development.

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

## settings/production.py

For production we should not expect an environment file, but it's easier to have one if we're testing something. 
But anyway, lest's provide few defaults inline, so `settings/base.py` can respond accordingly. 

    environ.Env.read_env(Path(__file__) / "production.env", DEBUG='False', ASSETS_DEBUG='False')
    from .base import *

The main point of interest here are `DEBUG` and `ASSETS_DEBUG` overrides, 
they will be applied to the python `os.environ` ONLY if they are MISSING from the environment and the file. 

These will be our production defaults, no need to put them in the environment or file, but they can be overridden if needed. Neat!

## settings/base.py

These are your mostly vanilla django settings, with a few conditionals and lot's of reading them from the environment. 
Almost everything is in here, keeping all the purposed environments consistent and as similar as possible.

The main differences are below (I hope these are self explanatory):

    import environ
    
    # https://github.com/joke2k/django-environ
    env = environ.Env()
    
    # Build paths inside the project like this: os.path.join(BASE_DIR, ...)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Where BASE_DIR is a django source root, ROOT_DIR is a whole project root
    # It may differ BASE_DIR for eg. when your django project code is in `src` folder
    # This may help to separate python modules and *django apps* from other stuff
    # like documentation, fixtures, docker settings
    ROOT_DIR = BASE_DIR
    
    # Quick-start development settings - unsuitable for production
    # See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/
    
    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = env('SECRET_KEY')
    
    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = env('DEBUG', default=False)
    
    INTERNAL_IPS = [
        '127.0.0.1',
    ]
    
    ALLOWED_HOSTS = []
    
    if 'ALLOWED_HOSTS' in os.environ:
        hosts = os.environ['ALLOWED_HOSTS'].split(" ")
        BASE_URL = "https://" + hosts[0]
        for host in hosts:
            host = host.strip()
            if host:
                ALLOWED_HOSTS.append(host)
    
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)

----

    # Database
    # https://docs.djangoproject.com/en/1.11/ref/settings/#databases
    
    if "DATABASE_URL" in os.environ:  # pragma: no cover
        # Enable database config through environment
        DATABASES = {
            # Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
            'default': env.db(),
        }
    
        # Make sure we use have all settings we need
        # DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'
        DATABASES['default']['TEST'] = {'NAME': os.environ.get("DATABASE_TEST_NAME", None)}
        DATABASES['default']['OPTIONS'] = {
            'options': '-c search_path=gis,public,pg_catalog',
            'sslmode': 'require',
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                # 'ENGINE': 'django.contrib.gis.db.backends.spatialite',
                'NAME': os.path.join(ROOT_DIR, 'data', 'db.dev.sqlite3'),
                'TEST': {
                    'NAME': os.path.join(ROOT_DIR, 'data', 'db.test.sqlite3'),
                }
            }
        }

----

    STATIC_ROOT = os.path.join(ROOT_DIR, 'static')
    
    # django-assets
    # http://django-assets.readthedocs.org/en/latest/settings.html
    
    ASSETS_LOAD_PATH = STATIC_ROOT
    ASSETS_ROOT = os.path.join(ROOT_DIR, 'assets', "compressed")
    ASSETS_DEBUG = env('ASSETS_DEBUG', default=DEBUG)  # Disable when testing compressed file in DEBUG mode
    if ASSETS_DEBUG:
        ASSETS_URL = STATIC_URL
        ASSETS_MANIFEST = "json:{}".format(os.path.join(ASSETS_ROOT, "manifest.json"))
    else:
        ASSETS_URL = STATIC_URL + "assets/compressed/"
        ASSETS_MANIFEST = "json:{}".format(os.path.join(STATIC_ROOT, 'assets', "compressed", "manifest.json"))
    ASSETS_AUTO_BUILD = ASSETS_DEBUG
    ASSETS_MODULES = ('website.assets',)

The last bit shows the power here. `ASSETS_DEBUG` has a sensible default, 
which can be overridden in `settings/production.py` and even that that can be overridden by an environment setting! Yay! 

In effect we have a mixed hierarchy of importance:

1. settings/<purpose>.py - sets defaults based on purpose, does not store secrets
2. settings/base.py - is mostly controlled by environment 
3. process environment settings - 12 factor baby!
4. settings/.env - local defaults for easy startup
 
