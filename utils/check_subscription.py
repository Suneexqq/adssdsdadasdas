# utils/check_subscription.py
from aiogram import Bot
from config import BOT_TOKEN, REQUIRED_CHANNELS

bot = Bot(token=BOT_TOKEN)

async def check_subscriptions(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ['member', 'creator', 'administrator']:
                return False
        except Exception:
            # Если бот не является администратором в канале или возникла ошибка
            return False
    return True
