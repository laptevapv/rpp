import asyncio
import psycopg2
import requests
import os
from dotenv import load_dotenv
from decimal import Decimal
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, BotCommand
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from xml.etree import ElementTree as ET

# Загрузка переменных окружения
load_dotenv()
bot_token = os.getenv("BOT_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=bot_token)
dp = Dispatcher(storage=MemoryStorage())

# Конфигурация подключения к БД
DB_CONFIG = {
    "dbname": "rgz_rpp",
    "user": "postgres",
    "password": "",
    "host": "localhost"
}

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/reg", description="Регистрация пользователя"),
        BotCommand(command="/add_operation", description="Добавить операцию"),
        BotCommand(command="/operations", description="Просмотр операций"),
        BotCommand(command="/menu", description="Показать меню"),
    ]
    await bot.set_my_commands(commands)

# Состояния FSM
class RegState(StatesGroup):
    waiting_for_name = State()

class OperationState(StatesGroup):
    waiting_for_type = State()
    waiting_for_sum = State()
    waiting_for_date = State()
    waiting_for_payment = State()

class ViewOperationsState(StatesGroup):
    waiting_for_currency = State()

# Обработчики команд
@dp.message(Command("start"))
async def start_command(message: Message, state: FSMContext):  
    await message.reply("Привет! Я бот для учёта финансов. Используй /menu чтобы увидеть список команд.")

@dp.message(Command("menu"))
async def show_menu(message: Message):
    text = (
        "Меню команд:\n\n"
        "/reg - Регистрация пользователя\n"
        "/add_operation - Добавить операцию (доход или расход)\n"
        "/operations - Просмотр всех операций\n"
        "/menu - Показать это меню"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("reg"))
async def handle_reg_command(message: Message, state: FSMContext):
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE id = %s", (message.chat.id,))
            if cur.fetchone():
                await message.answer("Вы уже зарегистрированы.")
                return
    await message.answer("Введите логин:")
    await state.set_state(RegState.waiting_for_name)

@dp.message(RegState.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (id, name) VALUES (%s, %s)", (message.chat.id, message.text.strip()))
            conn.commit()
    await message.answer("Вы успешно зарегистрированы!", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@dp.message(Command("add_operation"))
async def handle_add_operation(message: Message, state: FSMContext):
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE id = %s", (message.chat.id,))
            if not cur.fetchone():
                await message.answer("Сначала зарегистрируйтесь через /reg.")
                return
    buttons = [[KeyboardButton(text="РАСХОД"), KeyboardButton(text="ДОХОД")]]
    await message.answer("Выберите тип операции:", reply_markup=ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True))
    await state.set_state(OperationState.waiting_for_type)

@dp.message(OperationState.waiting_for_type)
async def process_op_type(message: Message, state: FSMContext):
    if message.text not in ["РАСХОД", "ДОХОД"]:
        await message.answer("Пожалуйста, выберите РАСХОД или ДОХОД.")
        return
    await state.update_data(type_operation=message.text)
    await message.answer("Введите сумму операции в рублях:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(OperationState.waiting_for_sum)

@dp.message(OperationState.waiting_for_sum)
async def process_op_sum(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную сумму.")
        return
    await state.update_data(amount=amount)
    await message.answer("Введите дату операции (ГГГГ-ММ-ДД):")
    await state.set_state(OperationState.waiting_for_date)

@dp.message(OperationState.waiting_for_date)
async def process_op_date(message: Message, state: FSMContext):
    try:
        date = datetime.strptime(message.text.strip(), "%Y-%m-%d").date()
    except ValueError:
        await message.answer("Неверный формат даты. Используйте ГГГГ-ММ-ДД.")
        return
    await state.update_data(date=str(date))
    data = await state.get_data()

    if data["type_operation"] == "ДОХОД":
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO operations (date, sum, chat_id, type_operation)
                    VALUES (%s, %s, %s, %s)
                """, (data["date"], data["amount"], message.chat.id, data["type_operation"]))
                conn.commit()
        await message.answer("Доход добавлен!", reply_markup=ReplyKeyboardRemove())
        await state.clear()
    else:
        buttons = [[KeyboardButton(text="НАЛИЧНЫЕ"), KeyboardButton(text="КАРТА")]]
        await message.answer("Выберите способ оплаты:", reply_markup=ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True))
        await state.set_state(OperationState.waiting_for_payment)

@dp.message(OperationState.waiting_for_payment)
async def process_payment_method(message: Message, state: FSMContext):
    if message.text not in ["НАЛИЧНЫЕ", "КАРТА"]:
        await message.answer("Выберите: НАЛИЧНЫЕ или КАРТА.")
        return
    await state.update_data(payment_method=message.text)
    data = await state.get_data()
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO operations (date, sum, chat_id, type_operation, payment_method)
                VALUES (%s, %s, %s, %s, %s)
            """, (data["date"], data["amount"], message.chat.id, data["type_operation"], data["payment_method"]))
            conn.commit()
    await message.answer("Расход добавлен!", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@dp.message(Command("operations"))
async def handle_view_operations(message: Message, state: FSMContext):
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE id = %s", (message.chat.id,))
            if not cur.fetchone():
                await message.answer("Сначала зарегистрируйтесь через /reg.")
                return
    buttons = [[KeyboardButton(text="RUB"), KeyboardButton(text="USD"), KeyboardButton(text="EUR")]]
    await message.answer("Выберите валюту:", reply_markup=ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True))
    await state.set_state(ViewOperationsState.waiting_for_currency)

@dp.message(ViewOperationsState.waiting_for_currency)
async def process_currency_choice(message: Message, state: FSMContext):
    currency = message.text.upper()
    if currency not in ["RUB", "USD", "EUR"]:
        await message.answer("Выберите валюту: RUB, USD или EUR.")
        return

    try:
        response = requests.get("https://www.cbr.ru/scripts/XML_daily.asp")
        response.encoding = 'windows-1251'
        root = ET.fromstring(response.text)
        rate = Decimal("1.0")
        if currency != "RUB":
            for valute in root.findall("Valute"):
                if valute.find("CharCode").text == currency:
                    rate = Decimal(valute.find("Value").text.replace(",", ".")) / Decimal(valute.find("Nominal").text)
                    break
    except Exception:
        rate = Decimal("1.0")

    symbol = {"RUB": "₽", "USD": "$", "EUR": "€"}[currency]
    lines = [f"Операции в {currency}:"]

    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT date, sum, type_operation, payment_method FROM operations
                WHERE chat_id = %s ORDER BY date DESC
            """, (message.chat.id,))
            rows = cur.fetchall()

    if not rows:
        await message.answer("Нет операций.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    for date, amount, op_type, pay_method in rows:
        converted = round(Decimal(amount) / rate, 2)
        line = f"{date} | {converted} {symbol} | {op_type}"
        if op_type == "РАСХОД" and pay_method:
            line += f" | {pay_method}"
        lines.append(line)

    await message.answer("\n".join(lines), reply_markup=ReplyKeyboardRemove())
    await state.clear()

# Запуск бота
async def main():
    print("Бот запущен.")
    await set_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
