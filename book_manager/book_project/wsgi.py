import os
import sys

# Путь к твоему проекту
path = '/home/wvvish/book_manager'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'book_project.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()