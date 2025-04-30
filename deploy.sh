#!/bin/bash

# =============================================================================
# Скрипт автоматизированного деплоя ChronographBot на Ubuntu 24.04
# =============================================================================

# Убедимся, что скрипт запущен от имени root
if [[ $EUID -ne 0 ]]; then
   echo "Этот скрипт должен быть запущен от имени root" 
   exit 1
fi

# Цвета для форматирования вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# =============================================================================
# Конфигурационные параметры
# =============================================================================

# Получаем имя текущего пользователя, если скрипт запущен через sudo
if [ -n "$SUDO_USER" ]; then
    DEPLOY_USER=$SUDO_USER
else
    DEPLOY_USER="root"
fi

# Определяем базовые пути и параметры
BASE_DIR="/opt/chronograph_bot"
VENV_DIR="$BASE_DIR/venv"
LOGS_DIR="$BASE_DIR/logs"
SERVICE_NAME="chronograph-bot"
GIT_REPO="https://github.com/user/ChronographBot.git" # Замените на ваш репозиторий

# Спрашиваем, откуда брать исходный код
echo -e "${YELLOW}Выберите источник исходного кода:${NC}"
echo "1) Клонировать из GitHub репозитория"
echo "2) Использовать локальные файлы в текущей директории"
read -p "Ваш выбор (1/2): " source_choice

if [ "$source_choice" = "1" ]; then
    echo -e "${YELLOW}Введите URL GitHub репозитория:${NC}"
    read -p "URL: " GIT_REPO
    USE_GIT=true
else
    USE_GIT=false
    echo -e "${YELLOW}Будут использованы локальные файлы из текущей директории.${NC}"
fi

# =============================================================================
# Функции для установки и настройки
# =============================================================================

function print_status() {
    echo -e "${BLUE}>> $1${NC}"
}

function print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

function print_error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

function setup_system_packages() {
    print_status "Обновление списка пакетов..."
    apt-get update || print_error "Не удалось обновить список пакетов"
    
    print_status "Установка необходимых системных пакетов..."
    apt-get install -y python3.12 python3.12-venv python3.12-dev python3-pip git || print_error "Не удалось установить системные пакеты"
    
    print_success "Системные пакеты успешно установлены"
}

function setup_project_directory() {
    print_status "Создание рабочей директории проекта..."
    mkdir -p $BASE_DIR
    mkdir -p $LOGS_DIR
    
    # Установка прав на директории
    chown -R $DEPLOY_USER:$DEPLOY_USER $BASE_DIR
    
    print_success "Рабочая директория создана: $BASE_DIR"
}

function setup_source_code() {
    if [ "$USE_GIT" = true ]; then
        print_status "Клонирование репозитория из GitHub..."
        git clone $GIT_REPO $BASE_DIR/src || print_error "Не удалось клонировать репозиторий"
    else
        print_status "Копирование локальных файлов в рабочую директорию..."
        mkdir -p $BASE_DIR/src
        cp -r ./* $BASE_DIR/src/ || print_error "Не удалось скопировать файлы"
    fi
    
    # Проверка наличия основных файлов
    if [ ! -f "$BASE_DIR/src/bot.py" ]; then
        print_error "Не найден основной файл bot.py в исходном коде"
    fi
    
    if [ ! -f "$BASE_DIR/src/requirements.txt" ]; then
        print_error "Не найден файл requirements.txt в исходном коде"
    fi
    
    print_success "Исходный код установлен в $BASE_DIR/src"
}

function setup_python_environment() {
    print_status "Создание виртуального окружения Python 3.12..."
    python3.12 -m venv $VENV_DIR || print_error "Не удалось создать виртуальное окружение"
    
    print_status "Активация виртуального окружения и установка зависимостей..."
    source $VENV_DIR/bin/activate
    
    # Обновление pip
    pip install --upgrade pip || print_error "Не удалось обновить pip"
    
    # Установка зависимостей
    pip install -r $BASE_DIR/src/requirements.txt || print_error "Не удалось установить зависимости"
    
    print_success "Виртуальное окружение настроено и зависимости установлены"
}

function setup_env_file() {
    print_status "Настройка файла окружения .env..."
    
    # Проверка наличия .env файла
    if [ -f "$BASE_DIR/src/.env" ]; then
        print_status "Файл .env уже существует. Пропускаем создание."
        return
    fi
    
    # Запрашиваем необходимые переменные окружения
    echo -e "${YELLOW}Введите токен бота (BOT_TOKEN):${NC}"
    read -p "BOT_TOKEN: " bot_token
    
    echo -e "${YELLOW}Введите API ключ OpenAI (OPENAI_API_KEY):${NC}"
    read -p "OPENAI_API_KEY: " openai_key
    
    echo -e "${YELLOW}Введите ID администратора в Telegram (ADMIN_ID):${NC}"
    read -p "ADMIN_ID: " admin_id
    
    # Создаем файл .env
    cat > $BASE_DIR/src/.env << EOF
BOT_TOKEN=$bot_token
OPENAI_API_KEY=$openai_key
ADMIN_ID=$admin_id
EOF
    
    # Устанавливаем правильные права доступа для .env файла
    chmod 600 $BASE_DIR/src/.env
    chown $DEPLOY_USER:$DEPLOY_USER $BASE_DIR/src/.env
    
    print_success "Файл .env создан и настроен"
}

function create_systemd_service() {
    print_status "Создание systemd сервиса для автоматического запуска бота..."
    
    # Определяем имя сервиса на основе имени проекта
    local service_file="/etc/systemd/system/${SERVICE_NAME}.service"
    
    # Определяем основной файл для запуска
    local main_file="bot.py"
    
    # Создаем файл сервиса
    cat > $service_file << EOF
[Unit]
Description=ChronographBot Telegram Bot Service
After=network.target

[Service]
Type=simple
User=$DEPLOY_USER
WorkingDirectory=$BASE_DIR/src
ExecStart=$VENV_DIR/bin/python $main_file
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
    
    # Перезагружаем systemd
    systemctl daemon-reload
    
    # Включаем сервис для автозапуска
    systemctl enable $SERVICE_NAME
    
    print_success "Systemd сервис создан и настроен для автоматического запуска"
}

function start_service() {
    print_status "Запуск сервиса $SERVICE_NAME..."
    systemctl start $SERVICE_NAME
    
    # Проверяем статус
    if systemctl is-active --quiet $SERVICE_NAME; then
        print_success "Сервис успешно запущен"
    else
        print_error "Сервис не запустился. Проверьте журнал: journalctl -u $SERVICE_NAME"
    fi
}

function print_help() {
    echo -e "${GREEN}=========================================================${NC}"
    echo -e "${GREEN}        ChronographBot успешно установлен!                ${NC}"
    echo -e "${GREEN}=========================================================${NC}"
    echo ""
    echo -e "${YELLOW}Полезные команды для управления ботом:${NC}"
    echo ""
    echo -e "${BLUE}➤ Просмотр логов:${NC}"
    echo "  journalctl -u $SERVICE_NAME -f"
    echo ""
    echo -e "${BLUE}➤ Управление сервисом:${NC}"
    echo "  Перезапуск:  sudo systemctl restart $SERVICE_NAME"
    echo "  Остановка:   sudo systemctl stop $SERVICE_NAME"
    echo "  Запуск:      sudo systemctl start $SERVICE_NAME"
    echo "  Статус:      sudo systemctl status $SERVICE_NAME"
    echo ""
    echo -e "${BLUE}➤ Файлы проекта:${NC}"
    echo "  Рабочая директория: $BASE_DIR/src"
    echo "  Логи: $LOGS_DIR"
    echo "  Файл конфигурации: $BASE_DIR/src/.env"
    echo ""
    echo -e "${YELLOW}Для любых вопросов обращайтесь к документации проекта.${NC}"
    echo -e "${GREEN}=========================================================${NC}"
}

# =============================================================================
# Основная часть скрипта
# =============================================================================

print_status "Начинаем установку ChronographBot..."

# Последовательно выполняем все этапы установки
setup_system_packages
setup_project_directory
setup_source_code
setup_python_environment
setup_env_file
create_systemd_service
start_service
print_help

exit 0