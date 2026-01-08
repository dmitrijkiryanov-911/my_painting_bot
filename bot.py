import asyncio
from datetime import datetime
from io import BytesIO

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    FSInputFile,
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram.client.default import DefaultBotProperties

from config import TOKEN, EXCEL_FILENAME
from storage import add_order, get_orders_for_chat, parse_date_str, format_date

from openpyxl import Workbook

from storage import init_db
init_db()


# -----------------------------
# Инициализация бота
# -----------------------------

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher(storage=MemoryStorage())


# -----------------------------
# FSM состояния
# -----------------------------

class NewOrderStates(StatesGroup):
    waiting_title = State()
    waiting_date = State()
    waiting_months = State()
    waiting_confirm = State()


# -----------------------------
# Клавиатура
# -----------------------------

def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Внести картину")],
            [KeyboardButton(text="Мои заказы")],
        ],
        resize_keyboard=True
    )


# -----------------------------
# Команды
# -----------------------------

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот учёта картин.\n\nВыберите действие:",
        reply_markup=main_keyboard()
    )


# -----------------------------
# Внесение картины
# -----------------------------

@dp.message(F.text == "Внести картину")
async def start_new_order(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(NewOrderStates.waiting_title)
    await message.answer("Название?", reply_markup=ReplyKeyboardRemove())


@dp.message(NewOrderStates.waiting_title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(NewOrderStates.waiting_date)
    await message.answer("Дата передачи в студию? (например 08.01.2026)")


@dp.message(NewOrderStates.waiting_date)
async def process_date(message: Message, state: FSMContext):
    text = message.text.strip()
    try:
        _ = parse_date_str(text)
    except Exception:
        await message.answer("Не понял дату. Введите в формате ДД.ММ.ГГГГ, например 08.01.2026")
        return

    await state.update_data(date_transfer=text)
    await state.set_state(NewOrderStates.waiting_months)
    await message.answer("Срок хранения? (например 3 мес — только целые месяцы)")


@dp.message(NewOrderStates.waiting_months)
async def process_months(message: Message, state: FSMContext):
    text = message.text.strip().lower()

    parts = text.split()
    try:
        months = int(parts[0])
    except Exception:
        await message.answer("Введите целое число месяцев, например: 3 или 3 мес")
        return

    data = await state.get_data()
    title = data["title"]
    date_transfer_str = data["date_transfer"]
    dt = parse_date_str(date_transfer_str)

    from storage import add_months
    pickup_date = add_months(dt, months)

    await state.update_data(months=months, pickup_date=pickup_date)

    confirm_text = (
        "Давайте проверим данные.\n"
        f'Картина: "{title}"\n'
        f"Дата передачи в студию: {date_transfer_str}\n"
        f"Срок хранения: {months} мес\n"
        f"Дата, когда нужно забрать: {format_date(pickup_date)}\n\n"
        'Отправьте: "Все верно" — если информация верна.\n'
        'Отправьте: "/new" — если нужно изменить данные и внести новые.'
    )

    await state.set_state(NewOrderStates.waiting_confirm)
    await message.answer(confirm_text)


@dp.message(NewOrderStates.waiting_confirm)
async def process_confirm(message: Message, state: FSMContext):
    text = message.text.strip().lower()

    if text == "/new":
        await state.clear()
        await message.answer("Начнём заново.\n\nНазвание?", reply_markup=ReplyKeyboardRemove())
        await state.set_state(NewOrderStates.waiting_title)
        return

    # Нормализуем текст
    clean = text.replace('"', '').replace("«", "").replace("»", "").strip()

    if clean not in ["все верно", "всё верно"]:
        await message.answer('Пожалуйста, отправьте "Все верно" или "/new".')
        return

    data = await state.get_data()

    order = add_order(
        chat_id=message.chat.id,
        title=data["title"],
        date_transfer_str=data["date_transfer"],
        months=data["months"],
    )

    await state.clear()
    await message.answer(
        "Заказ сохранён ✅\n\n"
        f'Картина: "{order["title"]}"\n'
        f'Забрать до: {order["date_pickup"]}',
        reply_markup=main_keyboard()
    )



# -----------------------------
# Мои заказы
# -----------------------------

@dp.message(F.text == "Мои заказы")
async def my_orders(message: Message):
    orders = get_orders_for_chat(message.chat.id)

    if not orders:
        await message.answer("У вас пока нет заказов.", reply_markup=main_keyboard())
        return

    orders_sorted = sorted(
        orders,
        key=lambda o: parse_date_str(o["date_transfer"])
    )

    lines = ["Вот ваши заказы:\n"]
    for idx, o in enumerate(orders_sorted, start=1):
        lines.append(f'{idx}. Картина "{o["title"]}". Забрать: {o["date_pickup"]}')

    text = "\n".join(lines)

    # Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Заказы"

    ws.append(["Название", "Дата передачи", "Срок хранения (мес)", "Дата забора"])

    for o in orders_sorted:
        ws.append([
            o["title"],
            o["date_transfer"],
            o["months"],
            o["date_pickup"],
        ])

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)

    await message.answer(text)
    await message.answer_document(
        document=FSInputFile(bio, filename=EXCEL_FILENAME),
        caption="Снизу файл Excel, в котором можете увидеть все свои заказы.",
        reply_markup=main_keyboard()
    )


# -----------------------------
# Help
# -----------------------------

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Команды:\n"
        "/start — главное меню\n"
        "Кнопки:\n"
        "• Внести картину\n"
        "• Мои заказы"
    )


# -----------------------------
# Запуск
# -----------------------------

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())

