from .base import *  # noqa: F403,F401


DEBUG = False
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
STORAGES["staticfiles"] = {
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
}
LOGGING["loggers"]["django.request"]["level"] = "ERROR"
