"""
ASGI config for m project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'm.settings')

application = get_asgi_application()

try:
    from politiaware_backend.observability import wrap_asgi_application
    application = wrap_asgi_application(application)
except Exception:
    pass

