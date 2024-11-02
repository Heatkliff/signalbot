import sys
import os
from django.core.wsgi import get_wsgi_application

# Путь к директории с проектом
project_path = "/home/cryptosig/cryptosignalbot/AlienSignalsBot"

# Добавляем директорию проекта в sys.path, если её там ещё нет
if project_path not in sys.path:
    sys.path.append(project_path)

# Устанавливаем переменную среды для файла настроек Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AlienSignalsBot.settings")

# Создаём WSGI-приложение для Passenger
application = get_wsgi_application()
