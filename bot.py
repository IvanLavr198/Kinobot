import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Кинобот 🎬\n\n"
        "🔍 Чтобы найти фильм: /film Название\n"
        "📺 Чтобы найти сериал: /serial Название"
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
        logging.error(f"TMDB error: {response.status_code}")
        return None
    data = response.json()
    return data['results'][0] if data.get('results') else None

async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи название фильма: /film Название")
        return
    query = ' '.join(context.args)
    film = tmdb_search(query, 'movie')
    if not film:
        await update.message.reply_text("Фильм не найден 😢")
        return

    title = film.get('title', 'Без названия')
    overview = film.get('overview', 'Описание недоступно.')
    rating = film.get('vote_average', '—')
    poster_path = film.get('poster_path')
    poster_url = f'https://image.tmdb.org/t/p/w500{poster_path}' if poster_path else None

    text = f"🎬 <b>{title}</b>\n⭐ Рейтинг: {rating}\n\n{overview}"
    if poster_url:
        await update.message.reply_photo(photo=poster_url, caption=text, parse_mode='HTML')
    else:
        await update.message.reply_text(text, parse_mode='HTML')

async def search_tv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Укажи название сериала: /serial Название")
        return
    query = ' '.join(context.args)
    tv_show = tmdb_search(query, 'tv')
    if not tv_show:
        await update.message.reply_text("Сериал не найден 😢")
        return

    title = tv_show.get('name', 'Без названия')
    overview = tv_show.get('overview', 'Описание недоступно.')
    rating = tv_show.get('vote_average', '—')
    poster_path = tv_show.get('poster_path')
    poster_url = f'https://image.tmdb.org/t/p/w500{poster_path}' if poster_path else None

    text = f"📺 <b>{title}</b>\n⭐ Рейтинг: {rating}\n\n{overview}"
    if poster_url:
        await update.message.reply_photo(photo=poster_url, caption=text, parse_mode='HTML')
    else:
        await update.message.reply_text(text, parse_mode='HTML')

def main():
    if not TELEGRAM_TOKEN or not TMDB_API_KEY:
        print("❌ Ошибка: переменные окружения TELEGRAM_TOKEN и TMDB_API_KEY должны быть заданы!")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('film', search_movie))
    app.add_handler(CommandHandler('serial', search_tv))

    logging.info("🤖 Бот запущен")
    app.run_polling()

if __name__ == '__main__':
    main()
