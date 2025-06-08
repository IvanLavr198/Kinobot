import os
import logging
import requests
from aiohttp import web
from telegram import Update, Bot
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# Переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Логирование
logging.basicConfig(level=logging.INFO)

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Кинобот.\n"
        "Напиши /film название фильма\n"
        "или /tv название сериала."
    )

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
    return data.get('results', [None])[0]

async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Напиши название фильма после /film")
        return
    query = ' '.join(context.args)
    film = tmdb_search(query, 'movie')
    if not film:
        await update.message.reply_text("Фильм не найден")
        return
    title = film.get('title', 'Без названия')
    overview = film.get('overview', 'Описание недоступно.')
    rating = film.get('vote_average', '—')
    poster_path = film.get('poster_path')
    poster_url = f'https://image.tmdb.org/t/p/w500{poster_path}' if poster_path else None
    text = f"🎬 <b>{title}</b>\n\n⭐ Рейтинг: {rating}\n\n{overview}"
    if poster_url:
        await update.message.reply_photo(photo=poster_url, caption=text, parse_mode='HTML')
    else:
        await update.message.reply_text(text, parse_mode='HTML')

async def search_tv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Напиши название сериала после /tv")
        return
    query = ' '.join(context.args)
    tv = tmdb_search(query, 'tv')
    if not tv:
        await update.message.reply_text("Сериал не найден")
        return
    title = tv.get('name', 'Без названия')
    overview = tv.get('overview', 'Описание недоступно.')
    rating = tv.get('vote_average', '—')
    poster_path = tv.get('poster_path')
    poster_url = f'https://image.tmdb.org/t/p/w500{poster_path}' if poster_path else None
    text = f"📺 <b>{title}</b>\n\n⭐ Рейтинг: {rating}\n\n{overview}"
    if poster_url:
        await update.message.reply_photo(photo=poster_url, caption=text, parse_mode='HTML')
    else:
        await update.message.reply_text(text, parse_mode='HTML')

# Основной запуск
async def main():
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("film", search_movie))
    app.add_handler(CommandHandler("tv", search_tv))

    # Установка вебхука
    await app.bot.set_webhook(WEBHOOK_URL)
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
