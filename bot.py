import os
import logging
from aiohttp import web
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

if not TELEGRAM_TOKEN or not TMDB_API_KEY or not WEBHOOK_URL:
    raise RuntimeError("Ошибка: TELEGRAM_TOKEN, TMDB_API_KEY и WEBHOOK_URL должны быть заданы в переменных окружения")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Кинобот.\n"
        "Чтобы найти фильм — напиши /film название фильма\n"
        "Чтобы найти сериал — напиши /tv название сериала"
    )

def tmdb_search(query: str, media_type='movie'):
    import requests
    url = f'https://api.themoviedb.org/3/search/{media_type}'
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'ru-RU',
        'query': query,
        'include_adult': False
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        return None
    data = resp.json()
    results = data.get('results')
    if results:
        return results[0]
    return None

async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажи название фильма после команды /film")
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

    text = f"🎬 <b>{title}</b>\n\n⭐ Рейтинг: {rating}\n\n{overview}"

    if poster_url:
        await update.message.reply_photo(photo=poster_url, caption=text, parse_mode='HTML')
    else:
        await update.message.reply_text(text, parse_mode='HTML')

async def search_tv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажи название сериала после команды /tv")
        return
    query = ' '.join(context.args)
    tv_show = tmdb_search(query, 'tv')
    if not tv_show:
        await update.message.reply_text("Сериал не найден")
        return

    title = tv_show.get('name', 'Без названия')
    overview = tv_show.get('overview', 'Описание недоступно.')
    rating = tv_show.get('vote_average', '—')
    poster_path = tv_show.get('poster_path')
    poster_url = f'https://image.tmdb.org/t/p/w500{poster_path}' if poster_path else None

    text = f"📺 <b>{title}</b>\n\n⭐ Рейтинг: {rating}\n\n{overview}"

    if poster_url:
        await update.message.reply_photo(photo=poster_url, caption=text, parse_mode='HTML')
    else:
        await update.message.reply_text(text, parse_mode='HTML')

async def handle_update(request):
    """Обработка обновления от Telegram (webhook)."""
    bot: Bot = request.app['bot']
    application: Application = request.app['application']
    data = await request.json()
    update = Update.de_json(data, bot)
    await application.process_update(update)
    return web.Response(text='ok')

async def on_startup(app):
    bot = Bot(token=TELEGRAM_TOKEN)
    app['bot'] = bot

    application = Application.builder().bot(bot).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("film", search_movie))
    application.add_handler(CommandHandler("tv", search_tv))

    app['application'] = application

    # Установка webhook на Telegram
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook установлен: {WEBHOOK_URL}")

async def on_cleanup(app):
    bot = app['bot']
    await bot.delete_webhook()
    logging.info("Webhook удалён")

def main():
    port = int(os.environ.get('PORT', '8080'))
    app = web.Application()

    app.router.add_post(f'/{TELEGRAM_TOKEN}', handle_update)

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    logging.info(f"Запуск веб-сервера на порту {port}")
    web.run_app(app, port=port)

if __name__ == "__main__":
    main()
