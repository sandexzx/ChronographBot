import logging
import os
from datetime import datetime

# Создаем директорию для логов, если её нет
if not os.path.exists('logs'):
    os.makedirs('logs')

# Настраиваем формат логов
log_format = '%(asctime)s - %(levelname)s - %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

# Создаем логгер
logger = logging.getLogger('chronograph_bot')
logger.setLevel(logging.INFO)

# Создаем обработчик для записи в файл
log_filename = f'logs/chronograph_{datetime.now().strftime("%Y%m%d")}.log'
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Создаем обработчик для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Создаем форматтер
formatter = logging.Formatter(log_format, date_format)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Добавляем обработчики к логгеру
logger.addHandler(file_handler)
logger.addHandler(console_handler) 