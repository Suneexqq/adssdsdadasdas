# handlers/admin.py
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import ADMIN_USERNAME
from database import Database
from keyboards.inline import admin_menu

db = Database()


class BroadcastState(StatesGroup):
    waiting_for_message = State()


def register_admin_handlers(dp: Dispatcher):
    @dp.message_handler(commands=['admin'])
    async def admin_cmd(message: types.Message):
        if message.from_user.username != ADMIN_USERNAME:
            await message.answer("У вас нет доступа к этой команде.")
            return
        await message.answer("Админ-панель:", reply_markup=admin_menu())

    @dp.callback_query_handler(text='stats')
    async def stats_callback(call: types.CallbackQuery):
        if call.from_user.username != ADMIN_USERNAME:
            await call.answer("У вас нет доступа к этой команде.")
            return
        total_users = db.get_total_users()
        await call.message.answer(f"Общее количество пользователей: {total_users}")

    @dp.callback_query_handler(text='broadcast')
    async def broadcast_callback(call: types.CallbackQuery):
        if call.from_user.username != ADMIN_USERNAME:
            await call.answer("У вас нет доступа к этой команде.")
            return
        await call.message.answer("Пожалуйста, отправьте сообщение для рассылки.")
        await BroadcastState.waiting_for_message.set()

    @dp.message_handler(state=BroadcastState.waiting_for_message, content_types=types.ContentTypes.ANY)
    async def start_broadcast(message: types.Message, state: FSMContext):
        users = db.get_all_users()
        success_count = 0
        for user in users:
            try:
                await message.copy_to(user[0])
                success_count += 1
            except Exception:
                continue
        await message.answer(f"Рассылка завершена. Сообщение отправлено {success_count} пользователям.")
        await state.finish()
