import os
import logging
import requests
from aiohttp import web
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем переменные окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.getenv('PORT', '8080'))

if not TELEGRAM_TOKEN or not TMDB_API_KEY or not WEBHOOK_URL:
    logger.error("TELEGRAM_TOKEN, TMDB_API_KEY и WEBHOOK_URL должны быть заданы!")
    exit(1)

# Функция поиска в TMDB
def tmdb_search(query: str, media_type='movie'):
    url = f'https://api.themoviedb.org/3/search/{media_type}'
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'ru-RU',
        'query': query,
        'include_adult': False
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        logger.warning(f"TMDB API error: {resp.status_code}")
        return None
    data = resp.json()
    results = data.get('results')
    if results:
        return results[0]
    return None

# Команды бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Кинобот.\n"
        "Используй команды:\n"
        "/film название_фильма — поиск фильма\n"
        "/tv название_сериала — поиск сериала"
    )

async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи название фильма после команды /film")
        return
    query = ' '.join(context.args)
    movie = tmdb_search(query, 'movie')
    if not movie:
        await update.message.reply_text("Фильм не найден")
        return

    title = movie.get('title', 'Без названия')
    overview = movie.get('overview', 'Описание недоступно.')
    rating = movie.get('vote_average', '—')
    poster_path = movie.get('poster_path')
    poster_url = f'https://image.tmdb.org/t/p/w500{poster_path}' if poster_path else None

    text = f"🎬 <b>{title}</b>\n⭐ Рейтинг: {rating}\n\n{overview}"
    if poster_url:
        await update.message.reply_photo(photo=poster_url, caption=text, parse_mode='HTML')
    else:
        await update.message.reply_text(text, parse_mode='HTML')

async def search_tv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи название сериала после команды /tv")
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

    text = f"📺 <b>{title}</b>\n⭐ Рейтинг: {rating}\n\n{overview}"
    if poster_url:
        await update.message.reply_photo(photo=poster_url, caption=text, parse_mode='HTML')
    else:
        await update.message.reply_text(text, parse_mode='HTML')

# Обработчик webhook запросов от Telegram
async def handle_update(request: web.Request):
    bot: Bot = request.app['bot']
    data = await request.json()
    update = Update.de_json(data, bot)
    application: Application = request.app['application']
    await application.update_queue.put(update)
    return web.Response(text='OK')

# Запуск и настройка aiohttp + telegram bot
async def on_startup(app: web.Application):
    logger.info("Запускаем бота и настраиваем webhook...")
    bot = Bot(token=TELEGRAM_TOKEN)
    app['bot'] = bot

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    app['application'] = application

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('film', search_movie))
    application.add_handler(CommandHandler('tv', search_tv))

    await application.initialize()
    await application.start()
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook установлен на {WEBHOOK_URL}")

async def on_cleanup(app: web.Application):
    logger.info("Чистим за ботом...")
    bot: Bot = app['bot']
    application: Application = app['application']
    await bot.delete_webhook()
    await application.stop()
    await application.shutdown()
    logger.info("Бот остановлен.")

def main():
    app = web.Application()
    app.router.add_post(f'/{TELEGRAM_TOKEN}', handle_update)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    logger.info(f"Запуск сервера на порту {PORT}")
    web.run_app(app, port=PORT)

if __name__ == '__main__':
    main()
