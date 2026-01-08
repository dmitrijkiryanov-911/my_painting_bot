import asyncio
from datetime import date

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from config import TOKEN
from storage import get_all_orders, parse_date_str


async def send_reminders():
    """Отправляет напоминания пользователям."""
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )

    today = date.today()
    orders = get_all_orders()

    for o in orders:
        if o.get("status") != "active":
            continue

        pickup_date = parse_date_str(o["date_pickup"])
        delta_days = (pickup_date - today).days

        # Только 7, 2 и 0 дней
        if delta_days not in (7, 2, 0):
            continue

        chat_id = o["chat_id"]
        title = o["title"]
        pickup_str = o["date_pickup"]

        if delta_days == 7:
            text = (
                f'Напоминание: через 7 дней нужно забрать картину "{title}".\n'
                f"Дата забора: {pickup_str}"
            )
        elif delta_days == 2:
            text = (
                f'Напоминание: через 2 дня нужно забрать картину "{title}".\n'
                f"Дата забора: {pickup_str}"
            )
        else:  # delta_days == 0
            text = (
                f'Сегодня крайний день забрать картину "{title}".\n'
                f"Дата забора: {pickup_str}"
            )

        try:
            await bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"Ошибка отправки напоминания для chat_id={chat_id}: {e}")

    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(send_reminders())
