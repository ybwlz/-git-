"""
WSGI config for mymanage project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mymanage.settings')

application = get_wsgi_application()
