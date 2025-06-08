import os
import logging
from aiohttp import web
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Dispatcher

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Кинобот.\n"
        "Чтобы найти фильм — напиши /film название фильма\n"
        "Чтобы найти сериал — напиши /tv название сериала"
    )

def tmdb_search(query, media_type='movie'):
    import requests
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
    if data.get('results'):
        return data['results'][0]
    return None

async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажи название фильма после команды /film")
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
    """Обработка входящих обновлений от Telegram (webhook)"""
    bot = request.app['bot']
    data = await request.json()
    update = Update.de_json(data, bot)
    dispatcher = request.app['dispatcher']
    await dispatcher.process_update(update)
    return web.Response()

async def on_startup(app):
    bot = Bot(token=TELEGRAM_TOKEN)
    app['bot'] = bot
    dispatcher = Dispatcher(bot, None, workers=0)
    app['dispatcher'] = dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('film', search_movie))
    dispatcher.add_handler(CommandHandler('tv', search_tv))

    # Устанавливаем webhook (URL укажем позже)
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')
    if not WEBHOOK_URL:
        raise ValueError("WEBHOOK_URL не задана в переменных окружения")
    await bot.set_webhook(WEBHOOK_URL)

async def on_cleanup(app):
    bot = app['bot']
    await bot.delete_webhook()

def main():
    if not TELEGRAM_TOKEN or not TMDB_API_KEY:
        print("Ошибка: TELEGRAM_TOKEN и TMDB_API_KEY должны быть заданы!")
        return

    app = web.Application()
    app.router.add_post(f'/{TELEGRAM_TOKEN}', handle_update)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    port = int(os.environ.get('PORT', 8080))
    web.run_app(app, port=port)

if __name__ == '__main__':
    main()
