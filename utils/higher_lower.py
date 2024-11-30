# utils/higher_lower.py
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import MIN_BET, REFERRAL_PERCENTAGE
from keyboards.inline import game_choice_menu, game_bet_menu, game_result_menu
from database import Database

db = Database()

class GameStates(StatesGroup):
    waiting_for_bet = State()
    waiting_for_choice = State()
    waiting_for_user_dice = State()

async def start_higher_lower_game(call: types.CallbackQuery, state: FSMContext, db: Database):
    await call.message.answer(f"🎲 <b>Игра: Больше/Меньше</b>\n\n💰 Введите ставку (минимум {MIN_BET} рублей):", parse_mode='HTML')
    await GameStates.waiting_for_bet.set()

async def process_bet(message: types.Message, state: FSMContext):
    try:
        bet_amount = float(message.text)
        if bet_amount < MIN_BET:
            await message.answer(f"Минимальная ставка: {MIN_BET} рублей. Пожалуйста, введите сумму заново.")
            return
        user = db.get_user(message.from_user.id)
        if user[3] < bet_amount:
            await message.answer("Недостаточно средств на балансе. Пополните баланс и попробуйте снова.")
            await state.finish()
            return
        await state.update_data(bet_amount=bet_amount)
        await message.answer(f"🎲 Ваша ставка: {bet_amount} рублей.\nВыберите исход:", reply_markup=game_choice_menu(), parse_mode='HTML')
        await GameStates.waiting_for_choice.set()
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму.")

async def process_choice(call: types.CallbackQuery, state: FSMContext):
    user_choice = call.data  # 'more' или 'less'
    await state.update_data(user_choice=user_choice)

    # Ход бота
    bot_dice_message = await call.bot.send_dice(call.from_user.id)
    bot_dice_value = bot_dice_message.dice.value
    await state.update_data(bot_dice_value=bot_dice_value)

    await call.message.answer(f"🎲 Бот кинул кубик, и выпало: {bot_dice_value}.\nТеперь ваша очередь!\nКидайте кубик:", reply_markup=game_bet_menu(), parse_mode='HTML')
    await GameStates.waiting_for_user_dice.set()

async def process_user_dice(call: types.CallbackQuery, state: FSMContext):
    user_dice_message = await call.bot.send_dice(call.from_user.id)
    user_dice_value = user_dice_message.dice.value

    data = await state.get_data()
    bet_amount = data['bet_amount']
    user_choice = data['user_choice']
    bot_dice_value = data['bot_dice_value']

    result = None
    win_amount = 0

    if user_choice == 'more':
        if user_dice_value > bot_dice_value:
            result = 'win'
            win_amount = bet_amount * 1.5
        else:
            result = 'lose'
    elif user_choice == 'less':
        if user_dice_value < bot_dice_value:
            result = 'win'
            win_amount = bet_amount * 1.5
        else:
            result = 'lose'

    # Обновляем баланс пользователя
    if result == 'win':
        db.update_balance(call.from_user.id, win_amount)
        message_text = f"🎉 Вы выиграли {win_amount} рублей! Поздравляем!\n🏆 Баланс: {db.get_user(call.from_user.id)[3]} рублей"
    else:
        db.update_balance(call.from_user.id, -bet_amount)
        message_text = f"😞 Увы, вы проиграли. Ваша ставка {bet_amount} рублей списана.\n🏆 Баланс: {db.get_user(call.from_user.id)[3]} рублей"

    # Добавляем лог игры
    db.add_game_log(call.from_user.id, bet_amount, user_dice_value, bot_dice_value, result)

    # Начисляем реферальный бонус
    user = db.get_user(call.from_user.id)
    if user[2]:
        referrer_id = user[2]
        referral_bonus = bet_amount * REFERRAL_PERCENTAGE / 100
        db.update_balance(referrer_id, referral_bonus)
        db.update_referral_income(referrer_id, referral_bonus)
        # Уведомление рефереру
        notification_text = f"""
<b>💰 Ваш реферал сделал ставку {bet_amount} рублей в игре "Больше/Меньше".</b>

Вы получили {referral_bonus} рублей ({REFERRAL_PERCENTAGE}% от ставки).
"""
        try:
            await call.bot.send_message(referrer_id, notification_text, parse_mode='HTML')
        except Exception as e:
            print(f"Ошибка при отправке уведомления рефереру: {e}")

    await call.message.answer(message_text, reply_markup=game_result_menu(), parse_mode='HTML')
    await state.finish()
