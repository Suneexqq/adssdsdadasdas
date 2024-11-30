# utils/lottery.py
import random
from datetime import date
from config import REFERRAL_PERCENTAGE, LOTTERY_TICKET_PRICE

async def perform_lottery_draw(bot, db):
    today_date = date.today().isoformat()
    tickets = db.get_lottery_tickets(today_date)
    if not tickets:
        # Нет участников
        return

    # Список user_id участников (может содержать повторения)
    participants = [ticket[0] for ticket in tickets]

    # Выбираем случайного победителя
    winner_id = random.choice(participants)
    jackpot = len(participants) * LOTTERY_TICKET_PRICE  # Общий призовой фонд

    # Начисляем выигрыш
    db.update_balance(winner_id, jackpot)

    # Уведомляем победителя
    winner_message = f"""
🎉 <b>Поздравляем!</b>

Вы выиграли джекпот лотереи в размере <b>{jackpot} рублей</b>!
"""
    try:
        await bot.send_message(winner_id, winner_message, parse_mode='HTML')
    except Exception as e:
        print(f"Ошибка при отправке сообщения победителю: {e}")

    # Оповещаем всех участников
    for user_id in set(participants):
        if user_id != winner_id:
            loser_message = f"""
🎟 <b>Результаты лотереи</b>

К сожалению, вы не выиграли в сегодняшней лотерее. Не унывайте и попробуйте снова завтра!
"""
            try:
                await bot.send_message(user_id, loser_message, parse_mode='HTML')
            except Exception as e:
                print(f"Ошибка при отправке сообщения участнику: {e}")

    # Очищаем билеты за сегодняшний день
    db.clear_lottery_tickets(today_date)

async def buy_lottery_ticket(call, db):
    user = db.get_user(call.from_user.id)
    if user[3] < LOTTERY_TICKET_PRICE:
        await call.answer("У вас недостаточно средств для покупки билета.", show_alert=True)
        return

    # Списываем средства
    db.update_balance(call.from_user.id, -LOTTERY_TICKET_PRICE)
    # Добавляем билет
    today_date = date.today().isoformat()
    db.add_lottery_ticket(call.from_user.id, today_date)

    # Начисление рефереру
    if user[2]:
        referrer_id = user[2]
        bonus = LOTTERY_TICKET_PRICE * REFERRAL_PERCENTAGE / 100
        db.update_balance(referrer_id, bonus)
        # Уведомление рефереру о покупке билета рефералом
        notification_text = f"""
<b>🎟 Ваш реферал купил билет лотереи за {LOTTERY_TICKET_PRICE} рублей!</b>

Вы получаете бонус <b>{bonus} рублей</b> ({REFERRAL_PERCENTAGE}% от покупки).
"""
        try:
            await call.bot.send_message(referrer_id, notification_text, parse_mode='HTML')
        except Exception as e:
            print(f"Ошибка при отправке уведомления рефереру: {e}")

    await call.answer("Вы успешно приобрели билет для сегодняшней лотереи!", show_alert=True)

async def reset_daily_clicks_job(db):
    db.reset_daily_clicks()
    print("Ежедневные клики пользователей сброшены")
