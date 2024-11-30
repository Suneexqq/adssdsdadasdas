# bot.py
import asyncio
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config import BOT_TOKEN
from handlers import register_user_handlers, register_admin_handlers
from database import Database
from utils.lottery import perform_lottery_draw, reset_daily_clicks_job

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = Database()

# Регистрация обработчиков
register_user_handlers(dp)
register_admin_handlers(dp)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    scheduler = AsyncIOScheduler(event_loop=loop, timezone=pytz.timezone('Europe/Moscow'))
    # Запускаем розыгрыш лотереи каждый день в 00:00 по московскому времени
    scheduler.add_job(perform_lottery_draw, CronTrigger(hour=0, minute=0), args=(bot, db))
    # Сброс ежедневных кликов в мини-игре
    scheduler.add_job(reset_daily_clicks_job, CronTrigger(hour=0, minute=0), args=(db,))
    scheduler.start()
    executor.start_polling(dp, skip_updates=True)
