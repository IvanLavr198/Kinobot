import os
import logging
import requests
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)
import asyncio

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Установи это в Render (например: https://kinobot-fgym.onrender.com)

logging.basicConfig(level=logging.INFO)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Кинобот.\n"
        "Напиши /film Название фильма\n"
        "Или /tv Название сериала"
    )

# Поиск через TMDB
def tmdb_search(query, media_type='movie'):
    url = f'https://api.themoviedb.org/3/search/{media_type}'
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'ru-RU',
        'query': query,
        'include_adult': False
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None
    data = response.json()
    return data['results'][0] if data.get('results') else None

# /film
async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи название фильма после команды /film")
        return
    film = tmdb_search(' '.join(context.args), 'movie')
    if not film:
        await update.message.reply_text("Фильм не найден")
        return
    text = f"🎬 <b>{film.get('title')}</b>\n⭐ Рейтинг: {film.get('vote_average')}\n\n{film.get('overview')}"
    poster = film.get('poster_path')
    if poster:
        await update.message.reply_photo(
            photo=f"https://image.tmdb.org/t/p/w500{poster}",
            caption=text,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(text, parse_mode='HTML')

# /tv
async def search_tv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи название сериала после команды /tv")
        return
    tv = tmdb_search(' '.join(context.args), 'tv')
    if not tv:
        await update.message.reply_text("Сериал не найден")
        return
    text = f"📺 <b>{tv.get('name')}</b>\n⭐ Рейтинг: {tv.get('vote_average')}\n\n{tv.get('overview')}"
    poster = tv.get('poster_path')
    if poster:
        await update.message.reply_photo(
            photo=f"https://image.tmdb.org/t/p/w500{poster}",
            caption=text,
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(text, parse_mode='HTML')

# Основной запуск
async def main():
    if not TELEGRAM_TOKEN or not TMDB_API_KEY or not WEBHOOK_URL:
        print("Ошибка: переменные TELEGRAM_TOKEN, TMDB_API_KEY, WEBHOOK_URL обязательны.")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("film", search_movie))
    app.add_handler(CommandHandler("tv", search_tv))

    # Webhook start
    await app.initialize()
    await app.bot.set_webhook(WEBHOOK_URL + f"/{TELEGRAM_TOKEN}")
    await app.start()
    await app.updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        url_path=TELEGRAM_TOKEN,
        webhook_url=WEBHOOK_URL + f"/{TELEGRAM_TOKEN}",
    )
    print("Кинобот запущен через webhook.")
    await app.updater.idle()

if __name__ == '__main__':
    asyncio.run(main())
