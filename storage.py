import json
import os
from datetime import datetime, date
from typing import List, Dict, Any

from config import DATA_FILE


# -----------------------------
# Загрузка и сохранение JSON
# -----------------------------

def load_data() -> Dict[str, Any]:
    """Загружает базу данных из JSON или создаёт новую."""
    if not os.path.exists(DATA_FILE):
        return {"next_id": 1, "orders": []}

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: Dict[str, Any]) -> None:
    """Сохраняет данные в JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# -----------------------------
# Работа с датами
# -----------------------------

def parse_date_str(s: str) -> date:
    """Преобразует строку 'ДД.ММ.ГГГГ' в объект date."""
    return datetime.strptime(s, "%d.%m.%Y").date()


def format_date(d: date) -> str:
    """Преобразует date обратно в строку 'ДД.ММ.ГГГГ'."""
    return d.strftime("%d.%m.%Y")


def add_months(base_date: date, months: int) -> date:
    """Добавляет к дате целое количество месяцев."""
    month = base_date.month - 1 + months
    year = base_date.year + month // 12
    month = month % 12 + 1

    # Корректируем день (например, 31 февраля → 28 февраля)
    day = min(
        base_date.day,
        [
            31,
            29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
            31, 30, 31, 30, 31, 31, 30, 31, 30, 31
        ][month - 1]
    )

    return date(year, month, day)


# -----------------------------
# Работа с заказами
# -----------------------------

def add_order(chat_id: int, title: str, date_transfer_str: str, months: int) -> Dict[str, Any]:
    """Добавляет новый заказ в базу."""
    data = load_data()

    dt = parse_date_str(date_transfer_str)
    pickup_date = add_months(dt, months)

    order_id = data["next_id"]
    data["next_id"] += 1

    order = {
        "id": order_id,
        "chat_id": chat_id,
        "title": title,
        "date_transfer": date_transfer_str,
        "months": months,
        "date_pickup": format_date(pickup_date),
        "status": "active"
    }

    data["orders"].append(order)
    save_data(data)

    return order


def get_orders_for_chat(chat_id: int) -> List[Dict[str, Any]]:
    """Возвращает список активных заказов пользователя."""
    data = load_data()
    return [
        o for o in data["orders"]
        if o["chat_id"] == chat_id and o["status"] == "active"
    ]


def get_all_orders() -> List[Dict[str, Any]]:
    """Возвращает все заказы (для напоминаний)."""
    data = load_data()
    return data["orders"]


def update_order(order_id: int, **fields) -> bool:
    """Обновляет заказ по ID."""
    data = load_data()
    updated = False

    for o in data["orders"]:
        if o["id"] == order_id:
            o.update(fields)
            updated = True
            break

    if updated:
        save_data(data)

    return updated


def delete_order(order_id: int) -> bool:
    """Удаляет заказ по ID."""
    data = load_data()
    before = len(data["orders"])

    data["orders"] = [o for o in data["orders"] if o["id"] != order_id]
    after = len(data["orders"])

    if after != before:
        save_data(data)
        return True

    return False