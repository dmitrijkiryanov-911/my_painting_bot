import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

DB_PATH = "database.db"


# ------------------------------
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДАТ
# ------------------------------

def parse_date_str(s: str) -> date:
    return datetime.strptime(s, "%d.%m.%Y").date()

def format_date(d: date) -> str:
    return d.strftime("%d.%m.%Y")

def add_months(d: date, months: int) -> date:
    year = d.year + (d.month + months - 1) // 12
    month = (d.month + months - 1) % 12 + 1
    day = min(d.day, [31,
                      29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                      31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return date(year, month, day)


# ------------------------------
# ИНИЦИАЛИЗАЦИЯ БАЗЫ
# ------------------------------

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            date_transfer TEXT NOT NULL,
            months INTEGER NOT NULL,
            date_pickup TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ------------------------------
# ДОБАВЛЕНИЕ ЗАКАЗА
# ------------------------------

def add_order(chat_id: int, title: str, date_transfer_str: str, months: int) -> Dict[str, Any]:
    dt = parse_date_str(date_transfer_str)
    pickup_date = add_months(dt, months)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO orders (chat_id, title, date_transfer, months, date_pickup, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (chat_id, title, date_transfer_str, months, format_date(pickup_date), "active"))

    conn.commit()

    order_id = cur.lastrowid
    conn.close()

    return {
        "id": order_id,
        "chat_id": chat_id,
        "title": title,
        "date_transfer": date_transfer_str,
        "months": months,
        "date_pickup": format_date(pickup_date),
        "status": "active"
    }


# ------------------------------
# ПОЛУЧЕНИЕ ЗАКАЗОВ
# ------------------------------

def get_orders_for_chat(chat_id: int) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, chat_id, title, date_transfer, months, date_pickup, status
        FROM orders
        WHERE chat_id = ? AND status = 'active'
    """, (chat_id,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "chat_id": r[1],
            "title": r[2],
            "date_transfer": r[3],
            "months": r[4],
            "date_pickup": r[5],
            "status": r[6]
        }
        for r in rows
    ]


def get_all_orders() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, chat_id, title, date_transfer, months, date_pickup, status
        FROM orders
        WHERE status = 'active'
    """)

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "chat_id": r[1],
            "title": r[2],
            "date_transfer": r[3],
            "months": r[4],
            "date_pickup": r[5],
            "status": r[6]
        }
        for r in rows
    ]


# ------------------------------
# ОБНОВЛЕНИЕ И УДАЛЕНИЕ
# ------------------------------

def update_order(order_id: int, **fields) -> bool:
    if not fields:
        return False

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    sets = ", ".join([f"{k} = ?" for k in fields])
    values = list(fields.values())
    values.append(order_id)

    cur.execute(f"UPDATE orders SET {sets} WHERE id = ?", values)

    conn.commit()
    updated = cur.rowcount > 0
    conn.close()

    return updated


def delete_order(order_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()

    deleted = cur.rowcount > 0
    conn.close()

    return deleted
