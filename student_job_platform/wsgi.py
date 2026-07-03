"""
WSGI config cho Student Job Platform project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student_job_platform.settings')
application = get_wsgi_application()
