# handlers/user.py
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from config import (
    ADMIN_USERNAME,
    MIN_WITHDRAW_AMOUNT,
    REFERRAL_PERCENTAGE,
    LOTTERY_TICKET_PRICE,
    MAX_CLICKS_PER_DAY,
    CLICK_COOLDOWN,
)
from database import Database
from keyboards.inline import (
    main_menu,
    profile_menu,
    check_subscription_menu,
    back_button,
    lottery_menu,
)
from utils.check_subscription import check_subscriptions
from utils.higher_lower import (
    start_higher_lower_game,
    process_bet,
    process_choice,
    process_user_dice,
    GameStates,
)
from utils.lottery import buy_lottery_ticket
import random
import time
from datetime import date

db = Database()


async def start_cmd(message: types.Message):
    referrer_id = None
    args = message.get_args()
    if args.isdigit():
        referrer_id = int(args)
        if referrer_id == message.from_user.id:
            referrer_id = None
    db.add_user(message.from_user.id, message.from_user.username, referrer_id)
    if referrer_id:
        db.increment_invited(referrer_id)
        db.update_balance(referrer_id, 0.7)  # Начисляем 100 рублей рефереру

        # Отправляем уведомление рефереру
        notification_text = f"""
<b>👥 Новый реферал!</b>

Пользователь @{message.from_user.username} присоединился по вашей ссылке.

<b>💰 Вы получили бонус: 0.7 🌟.</b>
"""
        try:
            await message.bot.send_message(referrer_id, notification_text, parse_mode='HTML')
        except Exception as e:
            print(f"Ошибка при отправке уведомления рефереру: {e}")

    # Проверка подписки
    is_subscribed = await check_subscriptions(message.from_user.id)
    if not is_subscribed:
        subscription_text = """
❗️ Для использования бота необходимо подписаться на наши каналы.
Пожалуйста, подпишитесь и нажмите кнопку "🔄 Проверить подписку".
"""
        await message.answer(subscription_text, reply_markup=check_subscription_menu())
        return

    welcome_text = f"""
👋 Привет, {message.from_user.full_name}!

Добро пожаловать в нашего бота. Используйте меню ниже для навигации.
"""
    await message.answer(welcome_text, reply_markup=main_menu(), parse_mode='HTML')


async def profile_callback(call: types.CallbackQuery):
    is_subscribed = await check_subscriptions(call.from_user.id)
    if not is_subscribed:
        subscription_text = """
❗️ Для использования бота необходимо подписаться на наши каналы.
Пожалуйста, подпишитесь и нажмите кнопку "🔄 Проверить подписку".
"""
        await call.message.answer(subscription_text, reply_markup=check_subscription_menu())
        return

    user = db.get_user(call.from_user.id)
    profile_text = f"""
🧾 <b>Ваш профиль</b>

💰 <b>Баланс</b>: {user[3]} 🌟
👥 <b>Приглашено</b>: {user[4]} человек
"""
    photos = await call.bot.get_user_profile_photos(call.from_user.id)
    if photos.total_count > 0:
        await call.message.answer_photo(
            photos.photos[0][0].file_id,
            caption=profile_text,
            reply_markup=profile_menu(),
            parse_mode='HTML',
        )
    else:
        await call.message.answer(profile_text, reply_markup=profile_menu(), parse_mode='HTML')


# Мини-игра (кликалка) с ограничениями
async def play_game_callback(call: types.CallbackQuery):
    is_subscribed = await check_subscriptions(call.from_user.id)
    if not is_subscribed:
        subscription_text = """
❗️ Для использования бота необходимо подписаться на наши каналы.
Пожалуйста, подпишитесь и нажмите кнопку "🔄 Проверить подписку".
"""
        await call.message.answer(subscription_text, reply_markup=check_subscription_menu())
        return

    user = db.get_user(call.from_user.id)
    current_time = int(time.time())
    last_click_time = user[6]  # Индекс 6 соответствует полю last_click_time
    daily_clicks = user[5]  # Индекс 5 соответствует полю daily_clicks

    # Проверяем кулдаун
    if current_time - last_click_time < CLICK_COOLDOWN:
        remaining_time = CLICK_COOLDOWN - (current_time - last_click_time)
        await call.answer(f"Подождите {remaining_time} секунд перед следующим кликом.", show_alert=True)
        return

    # Проверяем максимальное количество кликов в день
    if daily_clicks >= MAX_CLICKS_PER_DAY:
        await call.answer("Вы достигли максимального количества кликов на сегодня. Приходите завтра!", show_alert=True)
        return

    win_amount = random.randint(1, 50)
    db.update_balance(call.from_user.id, win_amount)
    db.increment_daily_clicks(call.from_user.id)
    db.update_last_click_time(call.from_user.id, current_time)

    # Начисление рефереру
    if user[2]:
        referrer_id = user[2]
        bonus = int(win_amount * REFERRAL_PERCENTAGE / 100)
        db.update_balance(referrer_id, bonus)
        # Уведомление рефереру о выигрыше реферала
        notification_text = f"""
<b>💰 Ваш реферал выиграл {win_amount} рублей!</b>

Вы получаете бонус <b>{bonus} рублей</b> ({REFERRAL_PERCENTAGE}% от выигрыша).
"""
        try:
            await call.bot.send_message(referrer_id, notification_text, parse_mode='HTML')
        except Exception as e:
            print(f"Ошибка при отправке уведомления рефереру: {e}")

    user = db.get_user(call.from_user.id)
    remaining_clicks = MAX_CLICKS_PER_DAY - user[5]  # daily_clicks

    message_text = f"""
🎉 <b>Поздравляем!</b>

Вы выиграли <b>{win_amount} рублей</b> в мини-игре!

Ваш текущий баланс: <b>{user[3]} рублей</b>
Осталось кликов на сегодня: <b>{remaining_clicks}</b>
"""
    await call.message.answer(message_text, parse_mode='HTML')


# Игра "Больше/Меньше"
async def higher_lower_game_callback(call: types.CallbackQuery, state: FSMContext):
    await start_higher_lower_game(call, state, db)


async def lottery_callback(call: types.CallbackQuery):
    await call.message.answer(
        "🎟 <b>Лотерея</b>\n\nВы можете купить билеты для участия в сегодняшнем розыгрыше. Каждый билет стоит 10 рублей и увеличивает ваш шанс на победу.",
        reply_markup=lottery_menu(),
        parse_mode='HTML',
    )


async def buy_ticket_callback(call: types.CallbackQuery):
    await buy_lottery_ticket(call, db)


async def referral_link_callback(call: types.CallbackQuery):
    is_subscribed = await check_subscriptions(call.from_user.id)
    if not is_subscribed:
        subscription_text = """
❗️ Для использования бота необходимо подписаться на наши каналы.
Пожалуйста, подпишитесь и нажмите кнопку "🔄 Проверить подписку".
"""
        await call.message.answer(subscription_text, reply_markup=check_subscription_menu())
        return

    bot_username = (await call.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={call.from_user.id}"
    message_text = f"""
🔗 <b>Ваша реферальная ссылка</b>

Приглашайте друзей и получайте бонусы! Отправьте им эту ссылку:

👉 {link}

💰 За каждого приглашённого вы получите <b>0.7 🌟</b>, а также <b>{REFERRAL_PERCENTAGE}%</b> от их дохода!
"""
    await call.message.edit_text(message_text, reply_markup=back_button(), parse_mode='HTML')


async def withdraw_callback(call: types.CallbackQuery):
    is_subscribed = await check_subscriptions(call.from_user.id)
    if not is_subscribed:
        subscription_text = """
❗️ Для использования бота необходимо подписаться на наши каналы.
Пожалуйста, подпишитесь и нажмите кнопку "🔄 Проверить подписку".
"""
        await call.message.answer(subscription_text, reply_markup=check_subscription_menu())
        return

    user = db.get_user(call.from_user.id)
    if user[3] < MIN_WITHDRAW_AMOUNT:
        await call.answer(f"Минимальная сумма для вывода: {MIN_WITHDRAW_AMOUNT} ⭐.", show_alert=True)
        return

    db.add_withdraw_request(call.from_user.id, user[3])
    db.update_balance(call.from_user.id, -user[3])

    message_text = f"""
💳 <b>Запрос на вывод средств</b>

Ваш запрос на вывод <b>{user[3]} ⭐</b> отправлен администратору. Ожидайте подтверждения.

Спасибо за использование нашего бота!
"""
    await call.message.answer(message_text, parse_mode='HTML')
    admin_message = f"""
📬 <b>Новый запрос на вывод средств</b>

Пользователь: @{call.from_user.username}
ID: {call.from_user.id}
Сумма: {user[3]} рублей

Для обработки запроса используйте команду: /process_withdraw {call.from_user.id}
"""
    await call.bot.send_message(f'@{ADMIN_USERNAME}', admin_message, parse_mode='HTML')


async def check_subscriptions_callback(call: types.CallbackQuery):
    is_subscribed = await check_subscriptions(call.from_user.id)
    if is_subscribed:
        await call.answer("Вы успешно подписались на все каналы!", show_alert=True)
        # Возвращаем пользователя в главное меню
        await call.message.answer("Теперь вы можете пользоваться ботом:", reply_markup=main_menu())
    else:
        await call.answer("Вы не подписаны на все обязательные каналы.", show_alert=True)


async def back_to_menu_callback(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.edit_text("Вы вернулись в главное меню:", reply_markup=main_menu())


def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(start_cmd, commands=['start'])
    dp.register_callback_query_handler(profile_callback, text='profile')
    dp.register_callback_query_handler(play_game_callback, text='mini_game')
    dp.register_callback_query_handler(higher_lower_game_callback, text='play_game', state='*')
    dp.register_message_handler(process_bet, state=GameStates.waiting_for_bet)
    dp.register_callback_query_handler(process_choice, state=GameStates.waiting_for_choice)
    dp.register_callback_query_handler(process_user_dice, text='roll_dice', state=GameStates.waiting_for_user_dice)
    dp.register_callback_query_handler(lottery_callback, text='lottery')
    dp.register_callback_query_handler(buy_ticket_callback, text='buy_ticket')
    dp.register_callback_query_handler(referral_link_callback, text='referral_link')
    dp.register_callback_query_handler(withdraw_callback, text='withdraw')
    dp.register_callback_query_handler(check_subscriptions_callback, text='check_subscriptions')
    dp.register_callback_query_handler(back_to_menu_callback, text='back_to_menu', state='*')
