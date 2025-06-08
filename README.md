# 1. Клонируем репозиторий и переходим в папку проекта
git clone https://github.com/твой-пользователь/кинобот.git
cd кинобот

# 2. Создаем виртуальное окружение и активируем его
python -m venv venv
source venv/bin/activate  # Для Linux/macOS
# или
venv\Scripts\activate     # Для Windows

# 3. Устанавливаем зависимости из requirements.txt
pip install -r requirements.txt

# 4. Создаем файл .env и добавляем переменные окружения (открой .env в любом редакторе и вставь это)
echo "TELEGRAM_TOKEN=твой_токен_бота" >> .env
echo "TMDB_API_KEY=твой_ключ_tmdb" >> .env
echo "WEBHOOK_URL=https://твое-доменное-имя/твой_токен_бота" >> .env
echo "PORT=8080" >> .env
