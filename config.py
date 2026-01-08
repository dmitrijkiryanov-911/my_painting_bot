import os

# Токен бота берём из переменных окружения Render
TOKEN = os.getenv("TOKEN")

# ID администратора (если нужно ограничить админ-функции)
ADMIN_ID = 809068111  # можешь поставить свой Telegram ID

# Имя файла с данными
DATA_FILE = "data.json"

# Имя Excel-файла
EXCEL_FILENAME = "my_painting.xlsx"