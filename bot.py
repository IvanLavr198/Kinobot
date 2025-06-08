import os
import logging
from typing import Optional, Dict, Any
import requests
from telegram import Update, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)

# ==================== КОНФИГУРАЦИЯ ====================
class Config:
    """Класс для хранения конфигурации бота"""
    def __init__(self):
        self.TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        self.TMDB_API_KEY = os.getenv("TMDB_API_KEY")
        self.PORT = int(os.getenv("PORT", "8080"))
        self.WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").rstrip("/")
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
        
        self.validate()
    
    def validate(self):
        """Проверка обязательных параметров"""
        if not self.TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN не установлен!")
        if not self.TMDB_API_KEY:
            raise ValueError("TMDB_API_KEY не установлен!")
        if self.ENVIRONMENT == "production" and not self.WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL обязателен для production!")

# ==================== TMDB API ====================
class TMDBClient:
    """Клиент для работы с TMDB API"""
    BASE_URL = "https://api.themoviedb.org/3"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def search_movie(self, query: str) -> Optional[Dict[str, Any]]:
        """Поиск фильма с обработкой ошибок"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/search/movie",
                params={
                    "api_key": self.api_key,
                    "query": query,
                    "language": "ru-RU",
                    "region": "RU"
                },
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])[0] if data.get("results") else None
        except (requests.RequestException, IndexError, KeyError) as e:
            logging.error(f"TMDB API error: {str(e)}")
            return None

# ==================== TELEGRAM BOT ====================
class MovieBot:
    """Основной класс бота"""
    def __init__(self, config: Config):
        self.config = config
        self.tmdb = TMDBClient(config.TMDB_API_KEY)
        self.app = Application.builder().token(config.TELEGRAM_TOKEN).build()
        
        # Регистрация обработчиков
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start(self, update: Update, context: CallbackContext):
        """Обработка команды /start"""
        await update.message.reply_text(
            "🎬 Кино-бот\n"
            "Отправь мне название фильма и я найду информацию о нем!\n\n"
            "Пример: 'Крестный отец' или 'Interstellar'"
        )
    
    async def handle_message(self, update: Update, context: CallbackContext):
        """Обработка текстовых сообщений"""
        query = update.message.text.strip()
        if not query:
            await update.message.reply_text("Пожалуйста, введите название фильма")
            return
        
        if movie := self.tmdb.search_movie(query):
            await self.send_movie_info(update, movie)
        else:
            await update.message.reply_text("Фильм не найден. Попробуйте изменить запрос.")
    
    async def send_movie_info(self, update: Update, movie: Dict[str, Any]):
        """Отправка информации о фильме"""
        title = movie.get("title", "Без названия")
        year = movie.get("release_date", "")[:4]
        rating = movie.get("vote_average", 0)
        overview = movie.get("overview", "Описание отсутствует")
        poster_path = movie.get("poster_path")
        
        message_text = (
            f"🎥 <b>{title}</b> ({year if year else 'год неизвестен'})\n"
            f"⭐ <b>{rating:.1f}</b>/10\n\n"
            f"{overview}"
        )
        
        if poster_path:
            photo_url = f"https://image.tmdb.org/t/p/w780{poster_path}"
            try:
                await update.message.reply_photo(
                    photo=photo_url,
                    caption=message_text,
                    parse_mode="HTML"
                )
                return
            except Exception as e:
                logging.error(f"Error sending photo: {e}")
        
        await update.message.reply_text(message_text, parse_mode="HTML")
    
    def run(self):
        """Запуск бота в соответствующем режиме"""
        if self.config.ENVIRONMENT == "production":
            logging.info(f"Starting webhook on {self.config.WEBHOOK_URL}")
            self.app.run_webhook(
                listen="0.0.0.0",
                port=self.config.PORT,
                webhook_url=self.config.WEBHOOK_URL,
                secret_token=None,
            )
        else:
            logging.info("Starting polling...")
            self.app.run_polling()

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    
    try:
        config = Config()
        bot = MovieBot(config)
        bot.run()
    except Exception as e:
        logging.critical(f"Failed to start bot: {str(e)}")
        raise
