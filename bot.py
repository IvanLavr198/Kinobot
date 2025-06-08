import os
import logging
import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)

# --- Настройки ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Получить у @BotFather
TMDB_API_KEY = os.getenv("TMDB_API_KEY")      # Ключ с https://www.themoviedb.org/
PORT = int(os.getenv("PORT", "8080"))         # Для Render
WEBHOOK_URL = os.getenv("WEBHOOK_URL")        # Например: https://your-bot-name.onrender.com
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")  # production или development

# --- Логирование ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Проверка обязательных переменных ---
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не установлен! Получите у @BotFather")
if not TMDB_API_KEY:
    raise ValueError("TMDB_API_KEY не установлен! Получите на https://www.themoviedb.org/")

logger.info(f"Бот запущен в режиме: {ENVIRONMENT}")

# --- Поиск фильма в TMDb ---
def search_movie(title: str):
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "ru-RU",
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Проверка на ошибки HTTP
        
        data = response.json()
        if not data.get("results"):
            logger.info(f"Фильм не найден: {title}")
            return None
            
        return data["results"][0]  # Первый результат
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к TMDb: {e}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
    return None

# --- Команды бота ---
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "🎬 Привет! Я бот для поиска фильмов.\n"
        "Просто напиши название фильма, и я найду его!"
    )

async def handle_message(update: Update, context: CallbackContext):
    movie_title = update.message.text
    logger.info(f"Поиск фильма: {movie_title}")
    
    movie = search_movie(movie_title)
    
    if not movie:
        await update.message.reply_text("Фильм не найден 😢 Попробуй другое название.")
        return
    
    # Формируем ответ
    title = movie.get("title", "Без названия")
    year = movie.get("release_date", "?")[:4] if movie.get("release_date") else "?"
    rating = movie.get("vote_average", "?")
    overview = movie.get("overview", "Нет описания.") or "Нет описания."
    poster_path = movie.get("poster_path")
    
    text = f"🎥 <b>{title}</b> ({year})\n⭐ Рейтинг: <b>{rating}/10</b>\n\n{overview}"
    
    try:
        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            await update.message.reply_photo(
                photo=poster_url,
                caption=text,
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        await update.message.reply_text("Произошла ошибка 😢 Попробуй позже.")

# --- Запуск бота ---
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Режим работы
    if ENVIRONMENT == "production" and WEBHOOK_URL:
        logger.info("Запуск в режиме PRODUCTION с вебхуком")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}",
            secret_token=None,
        )
    else:
        logger.info("Запуск в режиме DEVELOPMENT (polling)")
        app.run_polling()

if __name__ == "__main__":
    main()
