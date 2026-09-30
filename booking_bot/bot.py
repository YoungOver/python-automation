"""Telegram-бот записи клиентов (салон, клиника, мастер).

Клиент выбирает услугу, день и свободное время, оставляет телефон.
Админ получает заявку в личку и может подтвердить или отклонить её кнопкой.
Записи хранятся в SQLite, занятые слоты не показываются повторно.

Запуск:
    pip install aiogram==3.*
    set BOT_TOKEN=...  &  set ADMIN_ID=...
    python bot.py
"""
import asyncio
import os
import sqlite3
from datetime import date, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (CallbackQuery, KeyboardButton, Message,
                           ReplyKeyboardMarkup, ReplyKeyboardRemove)
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

SERVICES = {
    "cut": ("Стрижка", 1500),
    "color": ("Окрашивание", 4500),
    "nails": ("Маникюр", 1800),
}
WORK_HOURS = ["10:00", "11:30", "13:00", "14:30", "16:00", "17:30", "19:00"]
DAYS_AHEAD = 7

db = sqlite3.connect("bookings.db")
db.execute("""CREATE TABLE IF NOT EXISTS bookings(
    id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, phone TEXT,
    service TEXT, day TEXT, time TEXT, status TEXT DEFAULT 'new')""")
db.commit()


class Booking(StatesGroup):
    service = State()
    day = State()
    time = State()
    phone = State()


def busy_slots(day: str) -> set[str]:
    rows = db.execute(
        "SELECT time FROM bookings WHERE day=? AND status!='declined'", (day,))
    return {r[0] for r in rows}


dp = Dispatcher()


@dp.message(CommandStart())
async def start(msg: Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardBuilder()
    for key, (title, price) in SERVICES.items():
        kb.button(text=f"{title} · от {price} ₽", callback_data=f"svc:{key}")
    kb.adjust(1)
    await msg.answer("Здравствуйте! На какую услугу записать?", reply_markup=kb.as_markup())
    await state.set_state(Booking.service)


@dp.callback_query(Booking.service, F.data.startswith("svc:"))
async def pick_service(cb: CallbackQuery, state: FSMContext):
    await state.update_data(service=cb.data.split(":")[1])
    kb = InlineKeyboardBuilder()
    for i in range(DAYS_AHEAD):
        d = date.today() + timedelta(days=i)
        kb.button(text=d.strftime("%d.%m"), callback_data=f"day:{d.isoformat()}")
    kb.adjust(4)
    await cb.message.edit_text("Выберите день:", reply_markup=kb.as_markup())
    await state.set_state(Booking.day)


@dp.callback_query(Booking.day, F.data.startswith("day:"))
async def pick_day(cb: CallbackQuery, state: FSMContext):
    day = cb.data.split(":", 1)[1]
    free = [t for t in WORK_HOURS if t not in busy_slots(day)]
    if not free:
        await cb.answer("На этот день всё занято, выберите другой", show_alert=True)
        return
    await state.update_data(day=day)
    kb = InlineKeyboardBuilder()
    for t in free:
        kb.button(text=t, callback_data=f"time:{t}")
    kb.adjust(4)
    await cb.message.edit_text("Свободное время:", reply_markup=kb.as_markup())
    await state.set_state(Booking.time)


@dp.callback_query(Booking.time, F.data.startswith("time:"))
async def pick_time(cb: CallbackQuery, state: FSMContext):
    await state.update_data(time=cb.data.split(":", 1)[1])
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить номер", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True)
    await cb.message.answer("Оставьте номер, чтобы мы могли подтвердить запись:", reply_markup=kb)
    await state.set_state(Booking.phone)


@dp.message(Booking.phone, F.contact)
async def got_phone(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    title, _ = SERVICES[data["service"]]
    cur = db.execute(
        "INSERT INTO bookings(user_id,name,phone,service,day,time) VALUES(?,?,?,?,?,?)",
        (msg.from_user.id, msg.from_user.full_name, msg.contact.phone_number,
         title, data["day"], data["time"]))
    db.commit()
    await state.clear()
    await msg.answer(
        f"Готово! {title}, {data['day']} в {data['time']}.\nАдминистратор подтвердит запись в ближайшее время.",
        reply_markup=ReplyKeyboardRemove())

    kb = InlineKeyboardBuilder()
    kb.button(text="Подтвердить", callback_data=f"ok:{cur.lastrowid}")
    kb.button(text="Отклонить", callback_data=f"no:{cur.lastrowid}")
    await bot.send_message(
        ADMIN_ID,
        f"Новая запись\n{title}\n{data['day']} {data['time']}\n"
        f"{msg.from_user.full_name}, {msg.contact.phone_number}",
        reply_markup=kb.as_markup())


@dp.callback_query(F.data.regexp(r"^(ok|no):\d+$"))
async def admin_decision(cb: CallbackQuery, bot: Bot):
    if cb.from_user.id != ADMIN_ID:
        return
    action, booking_id = cb.data.split(":")
    status = "confirmed" if action == "ok" else "declined"
    db.execute("UPDATE bookings SET status=? WHERE id=?", (status, booking_id))
    db.commit()
    user_id, service, day, time = db.execute(
        "SELECT user_id, service, day, time FROM bookings WHERE id=?", (booking_id,)).fetchone()
    text = (f"Запись подтверждена: {service}, {day} в {time}. Ждём вас!" if status == "confirmed"
            else "К сожалению, это время занято. Нажмите /start, чтобы выбрать другое.")
    await bot.send_message(user_id, text)
    await cb.message.edit_text(cb.message.text + ("\n✅ Подтверждено" if status == "confirmed" else "\n❌ Отклонено"))


async def main():
    await dp.start_polling(Bot(BOT_TOKEN))


if __name__ == "__main__":
    asyncio.run(main())
