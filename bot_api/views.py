import asyncio

from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from django.dispatch import receiver
from django.core.signals import request_started
from asgiref.sync import async_to_sync
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update
import json
#from modul.clientbot.handlers.leomatch.handlers.registration import leomatch_start_handler
from modul.bot.main_bot.main import init_bot_handlers
from modul.clientbot.handlers.main import start_bot_client
from modul.clientbot.shortcuts import get_bot_by_token
from modul.config import scheduler, settings_conf
from modul.helpers.filters import setup_main_bot_filter
from modul.loader import dp, main_bot_router, client_bot_router, bot_session, main_bot
import tracemalloc

tracemalloc.start()

default = DefaultBotProperties(parse_mode="HTML")
def setup_routers():
    if not hasattr(dp, 'routers_setup'):
#        leomatch_start_handler()
        start_bot_client()
        init_bot_handlers()
        setup_main_bot_filter(main_bot_router, client_bot_router)
        dp.include_router(main_bot_router)
        dp.include_router(client_bot_router)
        dp.routers_setup = True


@csrf_exempt
def telegram_webhook(request, token):
    print(f"Received webhook for token: {token}")
    if request.method == 'POST':
        bot = async_to_sync(get_bot_by_token)(token)
        if token == settings_conf.BOT_TOKEN or bot:
            update = Update.parse_raw(request.body.decode())
            async_to_sync(feed_update)(token, update.dict())
            return HttpResponse(status=202)
        return HttpResponse(status=401)
    return HttpResponse(status=405)


async def feed_update(token, update):
    async with Bot(token, bot_session, default=default).context(auto_close=False) as bot_:
        await dp.feed_raw_update(bot_, update)


@receiver(request_started)
def startup_signal(sender, **kwargs):
    async_to_sync(startup)()


async def startup():
    setup_routers()
    await set_webhook()
    if not scheduler.running:
        scheduler.start()
    scheduler.print_jobs()
    # Запустите scheduler здесь, если он нужен


def shutdown():
    if hasattr(bot_session, 'close'):
        async_to_sync(bot_session.close)()
    scheduler.remove_all_jobs()
    scheduler.shutdown()
    # Остановите scheduler здесь, если он используется


# async def set_webhook():
#     webhook_url = settings_conf.WEBHOOK_URL.format(token=main_bot.token)
#     webhook_info = await main_bot.get_webhook_info()
#     if webhook_info.url != webhook_url:
#         await main_bot.set_webhook(webhook_url, allowed_updates=settings_conf.USED_UPDATE_TYPES)


async def set_webhook():
    try:
        webhook_url = settings_conf.WEBHOOK_URL.format(token=main_bot.token)
        webhook_info = await main_bot.get_webhook_info()
        if webhook_info.url != webhook_url:
            await main_bot.set_webhook(webhook_url, allowed_updates=settings_conf.USED_UPDATE_TYPES)
    except RuntimeError as e:
        if str(e) == "Event loop is closed":
            asyncio.set_event_loop(asyncio.new_event_loop())
