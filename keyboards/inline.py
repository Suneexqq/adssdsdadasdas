# keyboards/inline.py
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import REQUIRED_CHANNELS, LOTTERY_TICKET_PRICE

# Главное меню
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton('🧾 Профиль', callback_data='profile')
    )
    keyboard.add(
        InlineKeyboardButton('💳 Запросить вывод', callback_data='withdraw')
    )
    keyboard.add(
        InlineKeyboardButton('📈 Реферальная ссылка', callback_data='referral_link')
    )
    return keyboard

# Меню профиля
def profile_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton('🔄 Проверить подписки', callback_data='check_subscriptions'),
        InlineKeyboardButton('⬅️ Назад', callback_data='back_to_menu')
    )
    return keyboard

# Меню выбора направления
def game_choice_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton('🔼 Больше', callback_data='more'),
        InlineKeyboardButton('🔽 Меньше', callback_data='less')
    )
    return keyboard

# Кнопка для броска кубика
def game_bet_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton('🎲 Кинуть кубик', callback_data='roll_dice')
    )
    return keyboard

# Меню после игры
def game_result_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton('🔄 Играть снова', callback_data='play_game'),
        InlineKeyboardButton('🏠 В главное меню', callback_data='back_to_menu')
    )
    return keyboard

# Меню лотереи
def lottery_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(f'🎟 Купить билет ({LOTTERY_TICKET_PRICE} рублей)', callback_data='buy_ticket'),
        InlineKeyboardButton('⬅️ Назад', callback_data='back_to_menu')
    )
    return keyboard

# Админ-панель
def admin_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton('📊 Посмотреть статистику', callback_data='stats'),
        InlineKeyboardButton('✉️ Сделать рассылку', callback_data='broadcast')
    )
    return keyboard

# Меню проверки подписки
def check_subscription_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    # Добавляем кнопки с ссылками на каналы
    for channel in REQUIRED_CHANNELS:
        keyboard.add(
            InlineKeyboardButton('📢 Подписаться', url=f'https://t.me/{channel.replace("@", "")}')
        )
    keyboard.add(
        InlineKeyboardButton('🔄 Проверить подписку', callback_data='check_subscriptions')
    )
    return keyboard

# Кнопка "Назад"
def back_button():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('⬅️ Назад', callback_data='back_to_menu'))
    return keyboard
