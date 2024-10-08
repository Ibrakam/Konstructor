import asyncio

# Create your views here.
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.dispatch import receiver
from django.core.signals import request_started
from asgiref.sync import async_to_sync
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update

from modul.bot.main_bot.main import init_bot_handlers
from modul.clientbot.handlers.annon_bot.handlers.admin import admin_panel
from modul.clientbot.handlers.annon_bot.handlers.bot import anon_bot_handlers
from modul.clientbot.handlers.main import start_bot_client
# from modul.clientbot.handlers.main import start_client_bot

from modul.clientbot.shortcuts import get_bot_by_token
from modul.config import scheduler, settings_conf
from modul.helpers.filters import setup_main_bot_filter
from modul.loader import dp, main_bot_router, client_bot_router, bot_session, main_bot
import tracemalloc

tracemalloc.start()

print(scheduler.print_jobs())
default = DefaultBotProperties(parse_mode="HTML")

import logging
import time

# Настройка логгера
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_routers():
    logger.info("Setting up routers")
    if not hasattr(dp, 'routers_setup'):
        start_bot_client()
        admin_panel()
        init_bot_handlers()
        anon_bot_handlers()
        setup_main_bot_filter(main_bot_router, client_bot_router)
        dp.include_router(main_bot_router)
        dp.include_router(client_bot_router)
        dp.routers_setup = True
    logger.info("Routers setup completed")


@csrf_exempt
def telegram_webhook(request, token):
    start_time = time.time()
    logger.info(f"Received webhook for token: {token}")
    if request.method == 'POST':
        bot = async_to_sync(get_bot_by_token)(token)
        if token == settings_conf.BOT_TOKEN or bot:
            update = Update.parse_raw(request.body.decode())
            async_to_sync(feed_update)(token, update.dict())
            end_time = time.time()
            logger.info(f"Webhook processed in {end_time - start_time:.4f} seconds")
            return HttpResponse(status=202)
        logger.warning(f"Unauthorized webhook attempt for token: {token}")
        return HttpResponse(status=401)
    logger.warning(f"Invalid method for webhook: {request.method}")
    return HttpResponse(status=405)


async def feed_update(token, update):
    start_time = time.time()
    logger.info(f"Processing update for token: {token}")
    try:
        async with Bot(token, bot_session, default=default).context(auto_close=False) as bot_:
            await dp.feed_raw_update(bot_, update)
        end_time = time.time()
        logger.info(f"Update processed in {end_time - start_time:.4f} seconds")
    except Exception as e:
        logger.error(f"Error processing update: {e}", exc_info=True)


@receiver(request_started)
def startup_signal(sender, **kwargs):
    logger.info("Application startup signal received")
    async_to_sync(startup)()


async def startup():
    logger.info("Application startup initiated")
    setup_routers()
    await set_webhook()
    if not scheduler.running:
        scheduler.start()
    scheduler.print_jobs()
    logger.info("Application startup completed")


def shutdown():
    logger.info("Application shutdown initiated")
    if hasattr(bot_session, 'close'):
        async_to_sync(bot_session.close)()
    scheduler.remove_all_jobs()
    scheduler.shutdown()
    logger.info("Application shutdown completed")


async def set_webhook():
    logger.info("Setting webhook")
    try:
        webhook_url = settings_conf.WEBHOOK_URL.format(token=main_bot.token)
        webhook_info = await main_bot.get_webhook_info()
        if webhook_info.url != webhook_url:
            await main_bot.set_webhook(webhook_url, allowed_updates=settings_conf.USED_UPDATE_TYPES)
            logger.info(f"Webhook set to {webhook_url}")
        else:
            logger.info("Webhook already set correctly")
    except RuntimeError as e:
        if str(e) == "Event loop is closed":
            logger.warning("Event loop was closed, creating a new one")
            asyncio.set_event_loop(asyncio.new_event_loop())
        else:
            logger.error(f"Error setting webhook: {e}", exc_info=True)
